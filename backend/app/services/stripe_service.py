"""
Stripe service for ArtLock marketplace.

Handles:
- Stripe Connect onboarding for artists (to receive payouts)
- Stripe Checkout for companies purchasing data licenses
- Webhook processing for payment confirmation
- Payout transfers to artists after purchase
"""

import stripe
import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal
from app.core.config import settings


# Initialize Stripe – key read from settings
def _get_stripe():
    stripe.api_key = settings.STRIPE_SECRET_KEY or "sk_test_placeholder"
    return stripe


PLATFORM_FEE_PERCENT = Decimal("0.10")   # 10% platform fee


# ─────────────────────────────────────────
# Artist Connect Accounts
# ─────────────────────────────────────────

def create_connect_account(user_email: str, user_id: int) -> dict:
    """
    Create a Stripe Connect Express account for an artist so they can
    receive payouts when their works are purchased.
    """
    s = _get_stripe()
    account = s.Account.create(
        type="express",
        email=user_email,
        capabilities={
            "transfers": {"requested": True},
        },
        metadata={"artlockr_user_id": str(user_id)},
    )
    return {"stripe_account_id": account.id}


def create_onboarding_link(stripe_account_id: str, return_url: str, refresh_url: str) -> str:
    """
    Generate a Stripe-hosted onboarding URL so the artist can enter their
    bank/payout details. Returns the URL to redirect the artist to.
    """
    s = _get_stripe()
    link = s.AccountLink.create(
        account=stripe_account_id,
        refresh_url=refresh_url,
        return_url=return_url,
        type="account_onboarding",
    )
    return link.url


def get_account_status(stripe_account_id: str) -> dict:
    """Check if the artist has completed Stripe onboarding."""
    s = _get_stripe()
    account = s.Account.retrieve(stripe_account_id)
    return {
        "onboarded": account.details_submitted,
        "charges_enabled": account.charges_enabled,
        "payouts_enabled": account.payouts_enabled,
        "requirements": account.get("requirements", {}),
    }


def create_dashboard_link(stripe_account_id: str) -> str:
    """Return a link to the artist's Stripe Express dashboard."""
    s = _get_stripe()
    link = s.Account.create_login_link(stripe_account_id)
    return link.url


# ─────────────────────────────────────────
# Checkout Sessions (Company Purchases)
# ─────────────────────────────────────────

def create_checkout_session(
    listing_id: int,
    listing_title: str,
    price_usd: Decimal,
    buyer_stripe_customer_id: Optional[str],
    artist_stripe_account_id: str,
    success_url: str,
    cancel_url: str,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Create a Stripe Checkout session for a company purchasing a data license.

    Uses Stripe Connect destination charges so the artist receives the payment
    minus the platform fee automatically.
    """
    s = _get_stripe()

    price_cents = int(price_usd * 100)
    platform_fee_cents = int(price_cents * float(PLATFORM_FEE_PERCENT))

    session_params = {
        "payment_method_types": ["card"],
        "line_items": [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": listing_title,
                        "description": "Creative data license – ArtLock Marketplace",
                    },
                    "unit_amount": price_cents,
                },
                "quantity": 1,
            }
        ],
        "mode": "payment",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "payment_intent_data": {
            "application_fee_amount": platform_fee_cents,
            "transfer_data": {
                "destination": artist_stripe_account_id,
            },
        },
        "metadata": {
            "listing_id": str(listing_id),
            **(metadata or {}),
        },
    }

    if buyer_stripe_customer_id:
        session_params["customer"] = buyer_stripe_customer_id

    session = s.checkout.Session.create(**session_params)

    return {
        "session_id": session.id,
        "checkout_url": session.url,
        "payment_intent_id": session.payment_intent,
    }


def create_stripe_customer(email: str, company_name: str, user_id: int) -> str:
    """Create a Stripe customer for a company buyer."""
    s = _get_stripe()
    customer = s.Customer.create(
        email=email,
        name=company_name,
        metadata={"artlockr_user_id": str(user_id)},
    )
    return customer.id


# ─────────────────────────────────────────
# Webhook Processing
# ─────────────────────────────────────────

def construct_webhook_event(payload: bytes, sig_header: str) -> dict:
    """Verify and parse an incoming Stripe webhook."""
    s = _get_stripe()
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    event = s.Webhook.construct_event(payload, sig_header, webhook_secret)
    return event


def handle_checkout_completed(session: dict) -> dict:
    """
    Extract data from a completed checkout.Session event to update
    the purchase record in the database.
    """
    return {
        "listing_id": int(session["metadata"].get("listing_id", 0)),
        "stripe_payment_intent_id": session.get("payment_intent"),
        "amount_total": Decimal(session["amount_total"]) / 100,
    }


def handle_payment_intent_succeeded(payment_intent: dict) -> dict:
    """Extract transfer details once a payment succeeds."""
    charges = payment_intent.get("charges", {}).get("data", [])
    transfer_id = None
    if charges:
        transfer_id = charges[0].get("transfer")
    return {
        "stripe_payment_intent_id": payment_intent["id"],
        "stripe_transfer_id": transfer_id,
        "stripe_charge_id": charges[0]["id"] if charges else None,
    }


# ─────────────────────────────────────────
# Refunds
# ─────────────────────────────────────────

def issue_refund(stripe_payment_intent_id: str, reason: str = "requested_by_customer") -> dict:
    """Issue a full refund for a purchase."""
    s = _get_stripe()
    refund = s.Refund.create(
        payment_intent=stripe_payment_intent_id,
        reason=reason,
    )
    return {"refund_id": refund.id, "status": refund.status}


# ─────────────────────────────────────────
# License Key Generation
# ─────────────────────────────────────────

def generate_license_key(purchase_id: int, buyer_id: int) -> str:
    """Generate a unique, verifiable license key for a completed purchase."""
    raw = f"artlockr-{purchase_id}-{buyer_id}-{uuid.uuid4()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32].upper()
