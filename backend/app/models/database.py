from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text, Numeric, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    artist = "artist"
    company = "company"
    admin = "admin"


class WorkType(str, enum.Enum):
    image = "image"
    audio = "audio"
    video = "video"
    text = "text"
    dataset = "dataset"
    other = "other"


class LicenseType(str, enum.Enum):
    cc0 = "cc0"                        # Public domain
    cc_by = "cc_by"                    # Attribution
    non_exclusive = "non_exclusive"    # Multiple buyers allowed
    exclusive = "exclusive"            # Single buyer
    custom = "custom"                  # Custom terms


class ListingStatus(str, enum.Enum):
    active = "active"
    sold_exclusive = "sold_exclusive"
    paused = "paused"
    deleted = "deleted"


class PurchaseStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    refunded = "refunded"
    disputed = "disputed"


# ─────────────────────────────────────────
# Core User Model
# ─────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default=UserRole.artist)   # artist | company | admin
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_url = Column(String)
    bio = Column(Text)
    website = Column(String)
    location = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Stripe
    stripe_account_id = Column(String, unique=True)    # Stripe Connect (artists)
    stripe_customer_id = Column(String, unique=True)   # Stripe Customer (companies)
    stripe_onboarded = Column(Boolean, default=False)

    # Privacy
    consent_terms = Column(Boolean, default=False)
    consent_date = Column(DateTime)

    # Relationships
    artist_profile = relationship("ArtistProfile", back_populates="user", uselist=False)
    company_profile = relationship("CompanyProfile", back_populates="user", uselist=False)
    works = relationship("CreativeWork", back_populates="owner")
    listings = relationship("Listing", back_populates="artist")
    purchases = relationship("Purchase", back_populates="buyer")


# ─────────────────────────────────────────
# Artist Profile
# ─────────────────────────────────────────

class ArtistProfile(Base):
    __tablename__ = "artist_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    display_name = Column(String)
    specialties = Column(JSON)       # ["photography", "music", "illustration"]
    portfolio_url = Column(String)
    social_links = Column(JSON)      # {"twitter": "...", "instagram": "..."}
    total_earnings = Column(Numeric(12, 2), default=0)
    total_sales = Column(Integer, default=0)
    rating = Column(Float)           # Avg buyer rating
    verified_artist = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="artist_profile")


# ─────────────────────────────────────────
# Company Profile
# ─────────────────────────────────────────

class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    company_name = Column(String, nullable=False)
    industry = Column(String)         # "AI Research", "Gaming", etc.
    company_size = Column(String)     # startup / mid / enterprise
    use_case = Column(Text)           # What they use data for
    verified_company = Column(Boolean, default=False)
    total_spent = Column(Numeric(12, 2), default=0)
    total_purchases = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="company_profile")


# ─────────────────────────────────────────
# Creative Works (multi-type: image/audio/video/text)
# ─────────────────────────────────────────

class CreativeWork(Base):
    __tablename__ = "creative_works"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text)
    work_type = Column(String, nullable=False)   # image | audio | video | text | dataset
    file_format = Column(String)                 # jpg, png, mp3, wav, mp4, txt, zip
    file_size = Column(Integer)                  # bytes
    duration = Column(Float)                     # seconds (audio/video)
    file_hash = Column(String, unique=True, index=True)
    feature_path = Column(String)                # extracted ML features
    preview_url = Column(String)                 # low-res/watermarked preview

    # Metadata
    tags = Column(JSON)                          # ["landscape", "nature", "digital"]
    style = Column(String)                       # art style
    dimensions = Column(String)                  # "1920x1080" for images/video
    sample_rate = Column(Integer)                # Hz for audio

    # Origin
    source = Column(String, default="upload")    # upload | common_crawl | public_dataset
    source_url = Column(String)                  # original URL if from crawl
    source_dataset = Column(String)              # dataset name

    # Privacy
    image_deleted = Column(Boolean, default=False)
    upload_proof_hash = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="works")
    listing = relationship("Listing", back_populates="work", uselist=False)


# ─────────────────────────────────────────
# Marketplace Listings
# ─────────────────────────────────────────

class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(Integer, ForeignKey("creative_works.id"), nullable=False)
    artist_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)        # USD
    license_type = Column(String, nullable=False)         # cc0 | non_exclusive | exclusive | custom
    license_details = Column(Text)                        # Custom license text
    max_buyers = Column(Integer)                          # null = unlimited
    status = Column(String, default=ListingStatus.active) # active | sold_exclusive | paused | deleted
    featured = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    work = relationship("CreativeWork", back_populates="listing")
    artist = relationship("User", back_populates="listings")
    purchases = relationship("Purchase", back_populates="listing")


# ─────────────────────────────────────────
# Purchases
# ─────────────────────────────────────────

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)       # USD paid
    platform_fee = Column(Numeric(10, 2))                 # 10% fee
    seller_payout = Column(Numeric(10, 2))                # 90% to artist

    # Stripe
    stripe_payment_intent_id = Column(String, unique=True)
    stripe_transfer_id = Column(String)                   # Transfer to artist
    stripe_charge_id = Column(String)

    status = Column(String, default=PurchaseStatus.pending)
    license_key = Column(String, unique=True)             # Download/access key
    download_url = Column(String)                         # Time-limited URL
    download_expires_at = Column(DateTime)

    purchased_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    listing = relationship("Listing", back_populates="purchases")
    buyer = relationship("User", back_populates="purchases")


# ─────────────────────────────────────────
# Public Dataset Index (Common Crawl etc.)
# ─────────────────────────────────────────

class PublicDatasetEntry(Base):
    __tablename__ = "public_dataset_entries"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False, index=True)
    content_type = Column(String)          # image/jpeg, audio/mp3, etc.
    work_type = Column(String)             # image | audio | video | text
    file_format = Column(String)
    file_size = Column(Integer)
    file_hash = Column(String, index=True)
    dataset_source = Column(String)        # common_crawl | wikimedia | freesound
    crawl_id = Column(String)              # CC crawl identifier
    license_detected = Column(String)      # license found in page metadata
    title_detected = Column(String)
    author_detected = Column(String)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    indexed = Column(Boolean, default=False)


# ─────────────────────────────────────────
# Backward-compat: keep original tables
# ─────────────────────────────────────────

class APIGate(Base):
    __tablename__ = "api_gates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_name = Column(String, nullable=False)
    organization_domain = Column(String)
    is_blocked = Column(Boolean, default=True)
    block_reason = Column(Text)
    blocked_date = Column(DateTime, default=datetime.utcnow)
