from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Artist(Base):
    """Artist/User model"""
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    api_key = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Privacy Settings
    storage_mode = Column(String, default='features_only')  # 'features_only', 'encrypted', 'full'
    auto_delete_images = Column(Boolean, default=True)  # Delete images after feature extraction
    data_retention_days = Column(Integer, default=30)  # How long to keep feature data
    consent_privacy_policy = Column(Boolean, default=False)  # GDPR/CCPA consent
    consent_notifications = Column(Boolean, default=False)  # Email notification consent
    consent_date = Column(DateTime)  # When consent was given

    # Relationships
    artworks = relationship("Artwork", back_populates="artist")
    api_gates = relationship("APIGate", back_populates="artist")
    detection_results = relationship("DetectionResult", back_populates="artist")
    privacy_settings = relationship("ArtistPrivacySettings", back_populates="artist", uselist=False)


class Artwork(Base):
    """Original artwork uploaded by artists"""
    __tablename__ = "artworks"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    file_path = Column(String)  # Nullable now - may not store actual file
    file_hash = Column(String, unique=True, index=True)  # SHA-256 hash
    feature_path = Column(String)  # Path to extracted features (always stored)
    upload_date = Column(DateTime, default=datetime.utcnow)
    is_public = Column(Boolean, default=True)
    metadata = Column(JSON)  # Store additional metadata

    # Art Style & Detection Settings
    art_style = Column(String, default='general')  # photorealistic, digital_art, abstract, etc.
    complexity = Column(String, default='medium')  # simple, medium, complex
    custom_threshold = Column(Float)  # Artist can override default threshold

    # Privacy & Security
    storage_mode = Column(String, default='features_only')  # How this artwork is stored
    image_deleted = Column(Boolean, default=False)  # Was original image deleted?
    image_deleted_date = Column(DateTime)  # When was image deleted
    scheduled_deletion_date = Column(DateTime)  # Auto-delete on this date

    # Cryptographic Proof
    upload_proof_hash = Column(String)  # SHA-256(image + timestamp + artist_id)
    upload_signature = Column(String)  # Cryptographic signature
    blockchain_tx = Column(String)  # Optional: blockchain transaction ID

    # Relationships
    artist = relationship("Artist", back_populates="artworks")
    detection_results = relationship("DetectionResult", back_populates="original_artwork")


class AIGeneratedArt(Base):
    """AI-generated artwork for comparison"""
    __tablename__ = "ai_generated_art"

    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String)
    source_platform = Column(String)  # e.g., "midjourney", "stable-diffusion", etc.
    file_path = Column(String, nullable=False)
    file_hash = Column(String, unique=True, index=True)
    feature_path = Column(String)
    model_used = Column(String)  # Which AI model generated it
    prompt = Column(Text)  # If available
    indexed_date = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)


class DetectionResult(Base):
    """Results from copyright detection scans"""
    __tablename__ = "detection_results"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    scan_date = Column(DateTime, default=datetime.utcnow)
    total_scanned = Column(Integer, default=0)
    matches_found = Column(Integer, default=0)
    threshold_used = Column(Float, default=0.85)

    # Relationships
    artist = relationship("Artist", back_populates="detection_results")
    original_artwork = relationship("Artwork", back_populates="detection_results")
    matches = relationship("CopyrightMatch", back_populates="detection_result")


class CopyrightMatch(Base):
    """Individual copyright matches found during detection"""
    __tablename__ = "copyright_matches"

    id = Column(Integer, primary_key=True, index=True)
    detection_result_id = Column(Integer, ForeignKey("detection_results.id"), nullable=False)
    ai_artwork_id = Column(Integer, ForeignKey("ai_generated_art.id"))
    ai_artwork_path = Column(String, nullable=False)
    similarity_score = Column(Float, nullable=False)
    is_confirmed = Column(Boolean, default=False)  # Artist confirmation
    reported_date = Column(DateTime)
    notes = Column(Text)

    # Relationships
    detection_result = relationship("DetectionResult", back_populates="matches")


class APIGate(Base):
    """API gating rules for blocking organizations"""
    __tablename__ = "api_gates"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)
    organization_name = Column(String, nullable=False)
    organization_domain = Column(String)  # e.g., "openai.com"
    is_blocked = Column(Boolean, default=True)
    block_reason = Column(Text)
    blocked_date = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)

    # Relationships
    artist = relationship("Artist", back_populates="api_gates")
    access_logs = relationship("AccessLog", back_populates="api_gate")


class AccessLog(Base):
    """Log of access attempts to artwork"""
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    api_gate_id = Column(Integer, ForeignKey("api_gates.id"))
    ip_address = Column(String)
    user_agent = Column(String)
    requested_artwork_id = Column(Integer, ForeignKey("artworks.id"))
    access_granted = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)

    # Relationships
    api_gate = relationship("APIGate", back_populates="access_logs")


class ArtistPrivacySettings(Base):
    """Detailed privacy settings and audit trail for artists"""
    __tablename__ = "artist_privacy_settings"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False, unique=True)

    # Data Storage Preferences
    prefer_features_only = Column(Boolean, default=True)
    allow_image_caching = Column(Boolean, default=False)
    allow_analytics = Column(Boolean, default=False)

    # Notification Preferences
    notify_on_match = Column(Boolean, default=True)
    notify_on_scan = Column(Boolean, default=False)
    notify_on_data_access = Column(Boolean, default=True)

    # Data Export & Deletion
    last_data_export = Column(DateTime)
    data_export_count = Column(Integer, default=0)
    deletion_requested = Column(Boolean, default=False)
    deletion_request_date = Column(DateTime)
    deletion_scheduled_date = Column(DateTime)

    # Audit Trail
    settings_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_artworks_uploaded = Column(Integer, default=0)
    total_images_deleted = Column(Integer, default=0)

    # Relationships
    artist = relationship("Artist", back_populates="privacy_settings")


class UploadProof(Base):
    """Cryptographic proof of artwork upload for ownership verification"""
    __tablename__ = "upload_proofs"

    id = Column(Integer, primary_key=True, index=True)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)

    # Cryptographic Data
    file_hash = Column(String, nullable=False)  # SHA-256 of original file
    proof_hash = Column(String, unique=True, index=True, nullable=False)  # Composite hash
    signature = Column(String)  # Digital signature
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Blockchain Integration (optional)
    blockchain_network = Column(String)  # ethereum, polygon, etc.
    blockchain_tx_hash = Column(String)  # Transaction hash
    blockchain_block_number = Column(Integer)  # Block number
    blockchain_confirmed = Column(Boolean, default=False)

    # Verification
    verification_url = Column(String)  # Public URL to verify proof
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)

    # Metadata
    proof_data = Column(JSON)  # Additional proof metadata
