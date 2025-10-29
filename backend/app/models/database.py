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

    # Relationships
    artworks = relationship("Artwork", back_populates="artist")
    api_gates = relationship("APIGate", back_populates="artist")
    detection_results = relationship("DetectionResult", back_populates="artist")


class Artwork(Base):
    """Original artwork uploaded by artists"""
    __tablename__ = "artworks"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    file_path = Column(String, nullable=False)
    file_hash = Column(String, unique=True, index=True)  # For deduplication
    feature_path = Column(String)  # Path to extracted features
    upload_date = Column(DateTime, default=datetime.utcnow)
    is_public = Column(Boolean, default=True)
    metadata = Column(JSON)  # Store additional metadata

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
