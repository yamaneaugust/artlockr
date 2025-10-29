import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
from typing import List, Tuple, Dict
import os
from pathlib import Path


class CopyrightDetector:
    """
    ResNet-based copyright detection model for artwork.
    Uses feature extraction and similarity matching to detect copied artwork.
    """

    def __init__(
        self,
        model_name: str = "resnet50",
        weights: str = "IMAGENET1K_V2",
        device: str = "cuda",
        feature_dim: int = 2048
    ):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.feature_dim = feature_dim

        # Load pretrained ResNet model
        if model_name == "resnet50":
            self.model = models.resnet50(weights=weights)
        elif model_name == "resnet101":
            self.model = models.resnet101(weights=weights)
        elif model_name == "resnet152":
            self.model = models.resnet152(weights=weights)
        else:
            raise ValueError(f"Unsupported model: {model_name}")

        # Remove the final classification layer to get features
        self.feature_extractor = nn.Sequential(*list(self.model.children())[:-1])
        self.feature_extractor.eval()
        self.feature_extractor.to(self.device)

        # Image preprocessing pipeline
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def extract_features(self, image_path: str) -> np.ndarray:
        """
        Extract feature vector from an image using ResNet.

        Args:
            image_path: Path to the image file

        Returns:
            Feature vector as numpy array
        """
        # Load and preprocess image
        image = Image.open(image_path).convert('RGB')
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)

        # Extract features
        with torch.no_grad():
            features = self.feature_extractor(image_tensor)
            features = features.squeeze().cpu().numpy()

        # Normalize features
        features = features / (np.linalg.norm(features) + 1e-8)

        return features

    def compute_similarity(
        self,
        features1: np.ndarray,
        features2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two feature vectors.

        Args:
            features1: First feature vector
            features2: Second feature vector

        Returns:
            Similarity score between 0 and 1
        """
        # Cosine similarity
        similarity = np.dot(features1, features2) / (
            np.linalg.norm(features1) * np.linalg.norm(features2) + 1e-8
        )

        # Convert to 0-1 range
        similarity = (similarity + 1) / 2

        return float(similarity)

    def detect_copyright_infringement(
        self,
        original_image_path: str,
        ai_generated_images_dir: str,
        threshold: float = 0.85,
        top_k: int = 10
    ) -> List[Dict[str, any]]:
        """
        Detect potential copyright infringement by comparing original artwork
        against a database of AI-generated images.

        Args:
            original_image_path: Path to the original artwork
            ai_generated_images_dir: Directory containing AI-generated images
            threshold: Similarity threshold (0-1) for flagging potential infringement
            top_k: Number of top matches to return

        Returns:
            List of dictionaries containing match information
        """
        # Extract features from original artwork
        original_features = self.extract_features(original_image_path)

        matches = []

        # Compare against all AI-generated images
        ai_images_dir = Path(ai_generated_images_dir)
        for image_file in ai_images_dir.glob("**/*"):
            if image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                try:
                    # Extract features from AI-generated image
                    ai_features = self.extract_features(str(image_file))

                    # Compute similarity
                    similarity = self.compute_similarity(original_features, ai_features)

                    # Store if above threshold
                    if similarity >= threshold:
                        matches.append({
                            "image_path": str(image_file),
                            "image_name": image_file.name,
                            "similarity_score": round(similarity * 100, 2),
                            "is_infringement": True
                        })

                except Exception as e:
                    print(f"Error processing {image_file}: {e}")
                    continue

        # Sort by similarity score (descending) and return top K
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        return matches[:top_k]

    def batch_extract_features(
        self,
        image_paths: List[str],
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Extract features from multiple images in batches for efficiency.

        Args:
            image_paths: List of image file paths
            batch_size: Batch size for processing

        Returns:
            Array of feature vectors
        """
        features_list = []

        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_tensors = []

            for path in batch_paths:
                try:
                    image = Image.open(path).convert('RGB')
                    image_tensor = self.transform(image)
                    batch_tensors.append(image_tensor)
                except Exception as e:
                    print(f"Error loading {path}: {e}")
                    continue

            if not batch_tensors:
                continue

            # Stack into batch
            batch = torch.stack(batch_tensors).to(self.device)

            # Extract features
            with torch.no_grad():
                batch_features = self.feature_extractor(batch)
                batch_features = batch_features.squeeze().cpu().numpy()

            # Normalize
            if len(batch_features.shape) == 1:
                batch_features = batch_features.reshape(1, -1)

            for j in range(batch_features.shape[0]):
                feature = batch_features[j]
                feature = feature / (np.linalg.norm(feature) + 1e-8)
                features_list.append(feature)

        return np.array(features_list)

    def save_features(self, features: np.ndarray, save_path: str):
        """Save extracted features to disk."""
        np.save(save_path, features)

    def load_features(self, load_path: str) -> np.ndarray:
        """Load extracted features from disk."""
        return np.load(load_path)
