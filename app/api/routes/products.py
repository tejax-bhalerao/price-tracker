from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.routes.users import get_current_user
from app.database.session import get_db
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductDetailResponse,
    PriceHistoryResponse,
    ProductPriceCheckResult,
)
from app.services.price_service import price_service
from app.services.scraper import scraper

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new product to track",
)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Create a new product tracking record and perform an initial price scrape."""
    user_id = current_user.id if current_user else None

    # Initial scrape to get starting price
    scrape_res = scraper.scrape_url(str(product_in.url))
    initial_price = scrape_res.price if scrape_res.success else None
    currency = scrape_res.currency if (scrape_res.success and scrape_res.currency) else product_in.currency

    product = Product(
        user_id=user_id,
        name=product_in.name,
        url=str(product_in.url),
        target_price=product_in.target_price,
        current_price=initial_price,
        currency=currency,
        is_active=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # If price found, log first entry in history
    if initial_price is not None:
        history = PriceHistory(
            product_id=product.id,
            price=initial_price,
            currency=currency,
        )
        db.add(history)
        db.commit()
        db.refresh(product)

    response = ProductResponse.model_validate(product)
    response.message = (
        f"Product created successfully. Initial price: {currency} {initial_price:,.2f}"
        if initial_price is not None
        else "Product created successfully. Initial price could not be automatically detected."
    )
    return response


@router.get(
    "/",
    response_model=List[ProductResponse],
    summary="List all tracked products",
)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Retrieve list of tracked products with optional filtering."""
    query = db.query(Product)
    if current_user:
        query = query.filter(Product.user_id == current_user.id)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
    return products


@router.get(
    "/{product_id}",
    response_model=ProductDetailResponse,
    summary="Get product details with price history",
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Retrieve a single product along with its complete price history."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )
    return product


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product details or target price",
)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Update product name, URL, target price, or active tracking status."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    update_data = product_in.model_dump(exclude_unset=True)
    if "url" in update_data and update_data["url"] is not None:
        update_data["url"] = str(update_data["url"])

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a tracked product",
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Delete a tracked product and its price history."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    db.delete(product)
    db.commit()
    return {"message": f"Product {product_id} deleted successfully"}


@router.post(
    "/{product_id}/check-now",
    response_model=ProductPriceCheckResult,
    summary="Trigger immediate price scrape and alert check",
)
def check_product_price_now(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Force an immediate scrape for the product and send an alert if below target price."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    result = price_service.check_and_update_product_price(db, product)
    return result


@router.get(
    "/{product_id}/history",
    response_model=List[PriceHistoryResponse],
    summary="Get price history list for a product",
)
def get_product_history(
    product_id: int,
    limit: int = Query(30, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve historical price points for charting or analysis."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    history = (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return history