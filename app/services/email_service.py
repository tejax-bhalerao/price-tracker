import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for dispatching email notifications for price drops."""

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME
        self.enabled = settings.ENABLE_EMAIL_ALERTS

    def _render_price_drop_html(
        self,
        product_name: str,
        url: str,
        target_price: float,
        current_price: float,
        currency: str,
        old_price: Optional[float] = None,
    ) -> str:
        """Render a clean HTML price drop alert email template."""
        discount_text = ""
        if old_price and old_price > current_price:
            diff = old_price - current_price
            percent = (diff / old_price) * 100
            discount_text = f"<p style='color: #10b981; font-weight: bold;'>🎉 Price dropped by {currency} {diff:,.2f} ({percent:.1f}% off)!</p>"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Price Drop Alert!</title>
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f7; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h2 style="color: #4f46e5; margin-top: 0;">⚡ Price Drop Alert!</h2>
                <p>Great news! The product you are tracking has dropped to or below your target price.</p>
                
                <div style="background-color: #f8fafc; border-left: 4px solid #4f46e5; padding: 15px; margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #1e293b;">{product_name}</h3>
                    <p style="margin: 5px 0;"><strong>Current Price:</strong> <span style="color: #10b981; font-size: 1.2em; font-weight: bold;">{currency} {current_price:,.2f}</span></p>
                    <p style="margin: 5px 0;"><strong>Your Target Price:</strong> {currency} {target_price:,.2f}</p>
                    {discount_text}
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <a href="{url}" style="background-color: #4f46e5; color: #ffffff; text-decoration: none; padding: 12px 25px; border-radius: 6px; font-weight: bold; display: inline-block;">View Deal & Buy Now</a>
                </div>

                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0 20px 0;">
                <p style="font-size: 0.85em; color: #64748b; text-align: center;">You received this email because you subscribed to price tracking for this product on E-Commerce Price Tracker.</p>
            </div>
        </body>
        </html>
        """

    def send_price_drop_alert(
        self,
        to_email: str,
        product_name: str,
        url: str,
        target_price: float,
        current_price: float,
        currency: str = "USD",
        old_price: Optional[float] = None,
    ) -> bool:
        """Send an email alert for a price drop."""
        subject = f"Price Alert: {product_name} dropped to {currency} {current_price:,.2f}!"
        html_body = self._render_price_drop_html(
            product_name=product_name,
            url=url,
            target_price=target_price,
            current_price=current_price,
            currency=currency,
            old_price=old_price,
        )

        if not self.enabled or not self.host or not self.user:
            logger.info(
                f"[SIMULATION] Email alert triggered for {to_email}: {product_name} is now {currency} {current_price} (Target: {target_price})"
            )
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            part = MIMEText(html_body, "html")
            msg.attach(part)

            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(self.from_email, [to_email], msg.as_string())

            logger.info(f"Price alert email successfully sent to {to_email} for {product_name}")
            return True
        except Exception as exc:
            logger.error(f"Failed to send email alert to {to_email}: {exc}")
            return False


email_service = EmailService()
