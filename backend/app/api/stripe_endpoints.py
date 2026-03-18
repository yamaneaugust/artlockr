"""
Stripe endpoints.

Handles:
- Artist Connect onboarding (create account, get onboarding link)
- Webhook events from Stripe (payment confirmation)
- Artist dashboard link
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from backend.app.models.database import User
from backend.app.services import stripe_service, marketplace_service
from backend.app.core.database import get_db

router = APIRouter(prefix="/stripe", tags=["Stripe"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# ─────────────────────────────────────────
# Artist Stripe Connect Onboarding
# ─────────────────────────────────────────

@router.post("/connect/onboard")
def start_artist_onboarding(
    user_id: int,                  # TODO: replace with JWT auth
    db: Session = Depends(get_db),
):
    """
    Create a Stripe Connect Express account for an artist (if they don't have
    one yet) and return the Stripe-hosted onboarding URL.
    """
    user = db.query(User).filter(User.id == user_id, User.role == "artist").first()
    if not user:
        raise HTTPException(status_code=404, detail="Artist not found")

    # Create account if needed
    if not user.stripe_account_id:
        try:
            result = stripe_service.create_connect_account(user.email, user.id)
            user.stripe_account_id = result["stripe_account_id"]
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Stripe error: {e}")

    # Get onboarding link
    try:
        url = stripe_service.create_onboarding_link(
            user.stripe_account_id,
            return_url=f"{FRONTEND_URL}/profile?stripe=success",
            refresh_url=f"{FRONTEND_URL}/profile?stripe=refresh",
        )
        return {"onboarding_url": url}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Stripe error: {e}")


@router.get("/connect/status")
def get_onboarding_status(
    user_id: int,                  # TODO: replace with JWT auth
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.stripe_account_id:
        return {"onboarded": False, "stripe_account_id": None}

    try:
        status = stripe_service.get_account_status(user.stripe_account_id)
        if status["onboarded"] and not user.stripe_onboarded:
            user.stripe_onboarded = True
            db.commit()
        return {"stripe_account_id": user.stripe_account_id, **status}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Stripe error: {e}")


@router.get("/connect/dashboard")
def get_stripe_dashboard(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.stripe_account_id:
        raise HTTPException(status_code=400, detail="No Stripe account linked")
    try:
        url = stripe_service.create_dashboard_link(user.stripe_account_id)
        return {"dashboard_url": url}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Stripe error: {e}")


# ─────────────────────────────────────────
# Company Customer Setup
# ─────────────────────────────────────────

@router.post("/customer/create")
def create_company_customer(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Create a Stripe Customer for a company so cards can be saved."""
    user = db.query(User).filter(User.id == user_id, User.role == "company").first()
    if not user:
        raise HTTPException(status_code=404, detail="Company not found")

    if user.stripe_customer_id:
        return {"stripe_customer_id": user.stripe_customer_id, "already_exists": True}

    company_name = user.company_profile.company_name if user.company_profile else user.username

    try:
        customer_id = stripe_service.create_stripe_customer(user.email, company_name, user.id)
        user.stripe_customer_id = customer_id
        db.commit()
        return {"stripe_customer_id": customer_id}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Stripe error: {e}")


# ─────────────────────────────────────────
# Webhook
# ─────────────────────────────────────────

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    """
    Receive Stripe webhook events.
    Configure your webhook URL in the Stripe dashboard to point here.
    Listens for:
      - checkout.session.completed  → mark purchase complete
      - payment_intent.succeeded    → update transfer ID
      - account.updated             → update onboarding status
    """
    payload = await request.body()

    try:
        event = stripe_service.construct_webhook_event(payload, stripe_signature or "")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        purchase = marketplace_service.complete_purchase(db, data)
        if purchase:
            return {"status": "purchase_completed", "purchase_id": purchase.id}

    elif event_type == "payment_intent.succeeded":
        details = stripe_service.handle_payment_intent_succeeded(data)
        from backend.app.models.database import Purchase
        purchase = db.query(Purchase).filter(
            Purchase.stripe_payment_intent_id == details["stripe_payment_intent_id"]
        ).first()
        if purchase:
            purchase.stripe_transfer_id = details["stripe_transfer_id"]
            purchase.stripe_charge_id = details["stripe_charge_id"]
            db.commit()

    elif event_type == "account.updated":
        account_id = data.get("id")
        user = db.query(User).filter(User.stripe_account_id == account_id).first()
        if user and data.get("details_submitted"):
            user.stripe_onboarded = True
            db.commit()

    return {"received": True}
