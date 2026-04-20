"""
Profile endpoints for artists and companies.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.database import User, ArtistProfile, CompanyProfile, Listing, Purchase
from app.db.session import get_db

router = APIRouter(prefix="/profiles", tags=["Profiles"])


# ─────────────────────────────────────────
# Artist Profiles
# ─────────────────────────────────────────

@router.get("/artist/{user_id}")
async def get_artist_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id, User.role == "artist"))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Artist not found")

    profile = user.artist_profile
    active_listings = [l for l in user.listings if l.status == "active"]

    return {
        "id": user.id,
        "username": user.username,
        "display_name": profile.display_name if profile else user.username,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "website": user.website,
        "location": user.location,
        "specialties": profile.specialties if profile else [],
        "portfolio_url": profile.portfolio_url if profile else None,
        "social_links": profile.social_links if profile else {},
        "verified": profile.verified_artist if profile else False,
        "total_sales": profile.total_sales if profile else 0,
        "rating": profile.rating if profile else None,
        "stripe_onboarded": user.stripe_onboarded,
        "listing_count": len(active_listings),
        "listings": [
            {
                "id": l.id,
                "title": l.title,
                "price": float(l.price),
                "license_type": l.license_type,
                "work_type": l.work.work_type,
                "preview_url": l.work.preview_url,
                "created_at": l.created_at.isoformat(),
            }
            for l in active_listings[:12]
        ],
        "joined": user.created_at.isoformat(),
    }


@router.put("/artist/{user_id}")
async def update_artist_profile(
    user_id: int,
    display_name: Optional[str] = None,
    bio: Optional[str] = None,
    website: Optional[str] = None,
    location: Optional[str] = None,
    specialties: Optional[list] = None,
    portfolio_url: Optional[str] = None,
    social_links: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).filter(User.id == user_id, User.role == "artist"))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Artist not found")

    if bio is not None:
        user.bio = bio
    if website is not None:
        user.website = website
    if location is not None:
        user.location = location

    if not user.artist_profile:
        user.artist_profile = ArtistProfile(user_id=user_id)
        db.add(user.artist_profile)

    profile = user.artist_profile
    if display_name is not None:
        profile.display_name = display_name
    if specialties is not None:
        profile.specialties = specialties
    if portfolio_url is not None:
        profile.portfolio_url = portfolio_url
    if social_links is not None:
        profile.social_links = social_links

    await db.commit()
    return {"updated": True}


# ─────────────────────────────────────────
# Company Profiles
# ─────────────────────────────────────────

@router.get("/company/{user_id}")
async def get_company_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id, User.role == "company"))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Company not found")

    profile = user.company_profile
    purchases = [p for p in user.purchases if p.status == "completed"]

    return {
        "id": user.id,
        "username": user.username,
        "company_name": profile.company_name if profile else user.username,
        "industry": profile.industry if profile else None,
        "company_size": profile.company_size if profile else None,
        "use_case": profile.use_case if profile else None,
        "bio": user.bio,
        "website": user.website,
        "avatar_url": user.avatar_url,
        "verified": profile.verified_company if profile else False,
        "total_purchases": profile.total_purchases if profile else 0,
        "total_spent": float(profile.total_spent) if profile else 0,
        "stripe_customer_id": user.stripe_customer_id,
        "recent_purchases": [
            {
                "id": p.id,
                "listing_title": p.listing.title,
                "amount": float(p.amount),
                "license_type": p.listing.license_type,
                "purchased_at": p.purchased_at.isoformat(),
            }
            for p in purchases[-5:]
        ],
        "joined": user.created_at.isoformat(),
    }


@router.put("/company/{user_id}")
async def update_company_profile(
    user_id: int,
    company_name: Optional[str] = None,
    industry: Optional[str] = None,
    company_size: Optional[str] = None,
    use_case: Optional[str] = None,
    bio: Optional[str] = None,
    website: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).filter(User.id == user_id, User.role == "company"))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Company not found")

    if bio is not None:
        user.bio = bio
    if website is not None:
        user.website = website

    if not user.company_profile:
        user.company_profile = CompanyProfile(user_id=user_id, company_name=user.username)
        db.add(user.company_profile)

    profile = user.company_profile
    if company_name is not None:
        profile.company_name = company_name
    if industry is not None:
        profile.industry = industry
    if company_size is not None:
        profile.company_size = company_size
    if use_case is not None:
        profile.use_case = use_case

    await db.commit()
    return {"updated": True}


# ─────────────────────────────────────────
# User Registration
# ─────────────────────────────────────────

@router.post("/register")
async def register_user(
    email: str,
    username: str,
    password: str,
    role: str,                  # artist | company
    company_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    import hashlib
    from datetime import datetime

    # Check if email exists
    result = await db.execute(select(User).filter(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Check if username exists
    result = await db.execute(select(User).filter(User.username == username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username taken")

    if role not in ("artist", "company"):
        raise HTTPException(status_code=400, detail="Role must be artist or company")
    if role == "company" and not company_name:
        raise HTTPException(status_code=400, detail="company_name required for company accounts")

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()  # use bcrypt in production
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_pw,
        role=role,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    await db.flush()

    if role == "artist":
        db.add(ArtistProfile(user_id=user.id, display_name=username))
    else:
        db.add(CompanyProfile(user_id=user.id, company_name=company_name))

    await db.commit()
    await db.refresh(user)
    return {"user_id": user.id, "role": user.role, "username": user.username}


@router.post("/login")
async def login_user(email: str, password: str, db: AsyncSession = Depends(get_db)):
    import hashlib
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    result = await db.execute(
        select(User).filter(User.email == email, User.hashed_password == hashed_pw)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "email": user.email,
        "stripe_onboarded": user.stripe_onboarded,
    }
