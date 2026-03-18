"""
Marketplace service – business logic for browsing, listing, and purchasing
creative works on the ArtLock data marketplace.
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import Optional
from decimal import Decimal
from datetime import datetime, timedelta
import secrets

from backend.app.models.database import (
    User, ArtistProfile, CompanyProfile,
    CreativeWork, Listing, Purchase,
    ListingStatus, PurchaseStatus,
)
from backend.app.services import stripe_service


# ─────────────────────────────────────────
# Listings
# ─────────────────────────────────────────

def create_listing(
    db: Session,
    artist_id: int,
    work_id: int,
    title: str,
    description: str,
    price: Decimal,
    license_type: str,
    license_details: Optional[str] = None,
    max_buyers: Optional[int] = None,
) -> Listing:
    listing = Listing(
        work_id=work_id,
        artist_id=artist_id,
        title=title,
        description=description,
        price=price,
        license_type=license_type,
        license_details=license_details,
        max_buyers=max_buyers,
        status=ListingStatus.active,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def browse_listings(
    db: Session,
    work_type: Optional[str] = None,
    license_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    page: int = 1,
    page_size: int = 24,
) -> dict:
    query = (
        db.query(Listing)
        .join(CreativeWork, Listing.work_id == CreativeWork.id)
        .filter(Listing.status == ListingStatus.active)
    )

    if work_type:
        query = query.filter(CreativeWork.work_type == work_type)

    if license_type:
        query = query.filter(Listing.license_type == license_type)

    if min_price is not None:
        query = query.filter(Listing.price >= min_price)

    if max_price is not None:
        query = query.filter(Listing.price <= max_price)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Listing.title.ilike(pattern),
                Listing.description.ilike(pattern),
                CreativeWork.tags.cast(str).ilike(pattern),
            )
        )

    total = query.count()

    if sort_by == "price_asc":
        query = query.order_by(Listing.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Listing.price.desc())
    elif sort_by == "featured":
        query = query.order_by(Listing.featured.desc(), Listing.created_at.desc())
    else:
        query = query.order_by(Listing.created_at.desc())

    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


def get_listing(db: Session, listing_id: int) -> Optional[Listing]:
    return db.query(Listing).filter(Listing.id == listing_id).first()


def get_artist_listings(db: Session, artist_id: int) -> list:
    return db.query(Listing).filter(Listing.artist_id == artist_id).all()


# ─────────────────────────────────────────
# Purchases
# ─────────────────────────────────────────

def initiate_purchase(
    db: Session,
    listing_id: int,
    buyer_id: int,
    frontend_base_url: str = "http://localhost:3000",
) -> dict:
    """
    Start a purchase: create a Stripe Checkout session and a pending Purchase row.
    Returns the Stripe checkout URL to redirect the buyer.
    """
    listing = db.query(Listing).filter(
        Listing.id == listing_id,
        Listing.status == ListingStatus.active,
    ).first()

    if not listing:
        raise ValueError("Listing not available")

    # Enforce exclusive license limit
    if listing.license_type == "exclusive":
        existing = db.query(Purchase).filter(
            Purchase.listing_id == listing_id,
            Purchase.status == PurchaseStatus.completed,
        ).count()
        if existing > 0:
            raise ValueError("Exclusive license already sold")

    if listing.max_buyers:
        sold = db.query(Purchase).filter(
            Purchase.listing_id == listing_id,
            Purchase.status == PurchaseStatus.completed,
        ).count()
        if sold >= listing.max_buyers:
            raise ValueError("No licenses remaining")

    buyer = db.query(User).filter(User.id == buyer_id).first()
    artist = db.query(User).filter(User.id == listing.artist_id).first()

    if not artist.stripe_account_id or not artist.stripe_onboarded:
        raise ValueError("Artist has not completed payment setup")

    platform_fee = listing.price * Decimal("0.10")
    seller_payout = listing.price - platform_fee

    checkout = stripe_service.create_checkout_session(
        listing_id=listing_id,
        listing_title=listing.title,
        price_usd=listing.price,
        buyer_stripe_customer_id=buyer.stripe_customer_id,
        artist_stripe_account_id=artist.stripe_account_id,
        success_url=f"{frontend_base_url}/purchase/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{frontend_base_url}/marketplace",
        metadata={"buyer_id": str(buyer_id)},
    )

    purchase = Purchase(
        listing_id=listing_id,
        buyer_id=buyer_id,
        amount=listing.price,
        platform_fee=platform_fee,
        seller_payout=seller_payout,
        stripe_payment_intent_id=checkout.get("payment_intent_id"),
        status=PurchaseStatus.pending,
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    return {
        "purchase_id": purchase.id,
        "checkout_url": checkout["checkout_url"],
        "session_id": checkout["session_id"],
    }


def complete_purchase(db: Session, stripe_session_data: dict) -> Optional[Purchase]:
    """
    Called from Stripe webhook when checkout.session.completed fires.
    Updates the Purchase record, generates a license key, and marks exclusive
    listings as sold.
    """
    data = stripe_service.handle_checkout_completed(stripe_session_data)
    listing_id = data["listing_id"]
    payment_intent_id = data["stripe_payment_intent_id"]

    purchase = db.query(Purchase).filter(
        Purchase.stripe_payment_intent_id == payment_intent_id,
    ).first()

    if not purchase:
        # Fallback: find by listing_id + pending
        purchase = db.query(Purchase).filter(
            Purchase.listing_id == listing_id,
            Purchase.status == PurchaseStatus.pending,
        ).order_by(Purchase.id.desc()).first()

    if not purchase:
        return None

    license_key = stripe_service.generate_license_key(purchase.id, purchase.buyer_id)

    purchase.status = PurchaseStatus.completed
    purchase.license_key = license_key
    purchase.completed_at = datetime.utcnow()
    purchase.download_expires_at = datetime.utcnow() + timedelta(days=30)

    # Mark exclusive listing as sold
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if listing and listing.license_type == "exclusive":
        listing.status = ListingStatus.sold_exclusive

    # Update artist earnings
    artist = db.query(User).filter(User.id == listing.artist_id).first()
    if artist and artist.artist_profile:
        artist.artist_profile.total_earnings += purchase.seller_payout
        artist.artist_profile.total_sales += 1

    # Update company spend
    buyer = db.query(User).filter(User.id == purchase.buyer_id).first()
    if buyer and buyer.company_profile:
        buyer.company_profile.total_spent += purchase.amount
        buyer.company_profile.total_purchases += 1

    db.commit()
    db.refresh(purchase)
    return purchase


def get_purchase_by_license(db: Session, license_key: str) -> Optional[Purchase]:
    return db.query(Purchase).filter(Purchase.license_key == license_key).first()


def get_buyer_purchases(db: Session, buyer_id: int) -> list:
    return (
        db.query(Purchase)
        .filter(
            Purchase.buyer_id == buyer_id,
            Purchase.status == PurchaseStatus.completed,
        )
        .order_by(Purchase.purchased_at.desc())
        .all()
    )


# ─────────────────────────────────────────
# Marketplace Stats
# ─────────────────────────────────────────

def marketplace_stats(db: Session) -> dict:
    total_listings = db.query(Listing).filter(Listing.status == ListingStatus.active).count()
    total_artists = db.query(User).filter(User.role == "artist").count()
    total_companies = db.query(User).filter(User.role == "company").count()
    total_sales = db.query(Purchase).filter(Purchase.status == PurchaseStatus.completed).count()
    total_volume = db.query(func.sum(Purchase.amount)).filter(
        Purchase.status == PurchaseStatus.completed
    ).scalar() or 0

    work_type_counts = (
        db.query(CreativeWork.work_type, func.count(CreativeWork.id))
        .group_by(CreativeWork.work_type)
        .all()
    )

    return {
        "total_listings": total_listings,
        "total_artists": total_artists,
        "total_companies": total_companies,
        "total_sales": total_sales,
        "total_volume_usd": float(total_volume),
        "works_by_type": {wt: cnt for wt, cnt in work_type_counts},
    }
