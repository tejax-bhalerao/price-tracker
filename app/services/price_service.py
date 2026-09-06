from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.price_history import PriceHistory
from app.models.user import User
from app.schemas.product import ProductPriceCheckResult
from app.services.scraper import scraper
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class PriceService:
    """Orchestrates product scraping, price history tracking, and price drop notifications."""

    @staticmethod
    def check_and_update_product_price(
        db: Session, product: Product
    ) -> ProductPriceCheckResult:
        """Check current price for a product, save history, and dispatch alerts if target is reached."""
        old_price = product.current_price
        target_price = product.target_price
        scrape_res = scraper.scrape_url(product.url)

        if not scrape_res.success or scrape_res.price is None:
            logger.warning(
                f"Failed to scrape price for product {product.id} ({product.name}): {scrape_res.error_message}"
            )
            return ProductPriceCheckResult(
                product_id=product.id,
                product_name=product.name,
                old_price=old_price,
                new_price=old_price,
                target_price=target_price,
                is_price_drop=False,
                alert_triggered=False,
                status="failed",
                message=scrape_res.error_message or "Scraping failed",
            )

        new_price = scrape_res.price
        now = datetime.now(timezone.utc)

        # Update product record
        product.current_price = new_price
        if scrape_res.currency:
            product.currency = scrape_res.currency
        product.last_checked_at = now
        product.updated_at = now

        # Add price history entry
        history_entry = PriceHistory(
            product_id=product.id,
            price=new_price,
            currency=product.currency,
            recorded_at=now,
        )
        db.add(history_entry)

        # Check for price drop below target
        is_price_drop = new_price <= target_price
        alert_triggered = False

        if is_price_drop:
            # Check alert deduplication (e.g. at most 1 alert every 12 hours)
            can_send_alert = True
            if product.last_alert_sent_at:
                # If alert sent less than 12h ago and price hasn't dropped further
                if now - product.last_alert_sent_at < timedelta(hours=12):
                    can_send_alert = False

            if can_send_alert:
                # Find owner email if attached
                recipient_email = "user@example.com"
                if product.user_id:
                    owner = db.query(User).filter(User.id == product.user_id).first()
                    if owner and owner.email:
                        recipient_email = owner.email

                email_sent = email_service.send_price_drop_alert(
                    to_email=recipient_email,
                    product_name=product.name,
                    url=str(product.url),
                    target_price=target_price,
                    current_price=new_price,
                    currency=product.currency,
                    old_price=old_price,
                )
                if email_sent:
                    product.last_alert_sent_at = now
                    alert_triggered = True

        db.commit()
        db.refresh(product)

        return ProductPriceCheckResult(
            product_id=product.id,
            product_name=product.name,
            old_price=old_price,
            new_price=new_price,
            target_price=target_price,
            is_price_drop=is_price_drop,
            alert_triggered=alert_triggered,
            status="success",
            message=f"Price updated to {product.currency} {new_price:,.2f}"
            + (" (Target reached! Alert triggered)" if alert_triggered else ""),
        )


price_service = PriceService()
