from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class PriceHistoryResponse(BaseModel):
    id: int
    price: float
    currency: str
    recorded_at: datetime

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["iPhone 16 Pro"],
    )
    url: HttpUrl = Field(
        ...,
        examples=["https://example.com/product/iphone-16-pro"],
    )
    target_price: float = Field(
        ...,
        gt=0,
        examples=[70000.0],
    )
    currency: str = Field(
        default="USD",
        max_length=10,
        examples=["USD"],
    )


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[HttpUrl] = None
    target_price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    user_id: Optional[int] = None
    current_price: Optional[float] = None
    is_active: bool
    last_checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    message: Optional[str] = None

    model_config = {"from_attributes": True}


class ProductDetailResponse(ProductResponse):
    price_history: List[PriceHistoryResponse] = []


class ProductPriceCheckResult(BaseModel):
    product_id: int
    product_name: str
    old_price: Optional[float]
    new_price: Optional[float]
    target_price: float
    is_price_drop: bool
    alert_triggered: bool
    status: str
    message: str