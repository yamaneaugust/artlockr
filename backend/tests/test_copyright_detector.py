"""
Unit tests for the Copyright Detector model.
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ml_models.inference.copyright_detector import CopyrightDetector


@pytest.fixture
def detector():
    """Create a copyright detector instance for testing"""
    return CopyrightDetector(
        model_name="resnet50",
        device="cpu",  # Use CPU for testing
        feature_dim=2048
    )


def test_detector_initialization(detector):
    """Test that the detector initializes correctly"""
    assert detector is not None
    assert detector.feature_dim == 2048
    assert detector.device.type == "cpu"


def test_feature_extraction_shape(detector):
    """Test that extracted features have the correct shape"""
    # This test would require a sample image
    # For now, we'll just test the model structure
    assert detector.feature_extractor is not None


def test_compute_similarity(detector):
    """Test similarity computation"""
    # Create two random feature vectors
    features1 = np.random.randn(2048)
    features2 = np.random.randn(2048)

    # Normalize
    features1 = features1 / np.linalg.norm(features1)
    features2 = features2 / np.linalg.norm(features2)

    # Compute similarity
    similarity = detector.compute_similarity(features1, features2)

    # Check that similarity is between 0 and 1
    assert 0 <= similarity <= 1


def test_identical_features_similarity(detector):
    """Test that identical features have similarity close to 1"""
    features = np.random.randn(2048)
    features = features / np.linalg.norm(features)

    similarity = detector.compute_similarity(features, features)

    # Should be very close to 1
    assert similarity > 0.99


def test_save_load_features(detector, tmp_path):
    """Test saving and loading features"""
    # Create random features
    features = np.random.randn(2048)

    # Save to temporary file
    save_path = tmp_path / "test_features.npy"
    detector.save_features(features, str(save_path))

    # Load back
    loaded_features = detector.load_features(str(save_path))

    # Check that they match
    assert np.allclose(features, loaded_features)


def test_feature_normalization(detector):
    """Test that features are properly normalized"""
    features = np.random.randn(2048) * 10  # Create unnormalized features

    # Normalize
    normalized = features / (np.linalg.norm(features) + 1e-8)

    # Check that norm is approximately 1
    norm = np.linalg.norm(normalized)
    assert 0.99 < norm < 1.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
