"""
Custom dataset loaders for copyright detection training.
Supports both pair-based (Siamese) and triplet-based training.
"""
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import numpy as np
import random
from pathlib import Path
from typing import Tuple, List, Optional, Dict
import json


class ArtworkPairDataset(Dataset):
    """
    Dataset for Siamese network training with positive and negative pairs.

    Positive pairs: (original, copied/similar artwork)
    Negative pairs: (original, different artwork)
    """

    def __init__(
        self,
        data_file: str,
        image_dir: str,
        transform: Optional[transforms.Compose] = None,
        augment: bool = True
    ):
        """
        Args:
            data_file: JSON file containing pair annotations
            image_dir: Root directory containing images
            transform: Image transformations
            augment: Whether to apply data augmentation
        """
        self.image_dir = Path(image_dir)
        self.transform = transform
        self.augment = augment

        # Load annotations
        with open(data_file, 'r') as f:
            self.annotations = json.load(f)

        self.pairs = self.annotations['pairs']

        # Default transform if none provided
        if self.transform is None:
            self.transform = self._default_transform()

    def _default_transform(self):
        """Default image preprocessing"""
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, int]:
        """
        Returns:
            img1: First image tensor
            img2: Second image tensor
            label: 1 for similar pair, 0 for dissimilar pair
        """
        pair = self.pairs[idx]

        img1_path = self.image_dir / pair['image1']
        img2_path = self.image_dir / pair['image2']
        label = pair['label']  # 1 = similar, 0 = dissimilar

        # Load images
        img1 = Image.open(img1_path).convert('RGB')
        img2 = Image.open(img2_path).convert('RGB')

        # Apply transformations
        if self.transform:
            img1 = self.transform(img1)
            img2 = self.transform(img2)

        return img1, img2, torch.tensor(label, dtype=torch.float32)


class ArtworkTripletDataset(Dataset):
    """
    Dataset for triplet network training.

    Each sample contains:
    - Anchor: Original artwork
    - Positive: Similar/copied artwork
    - Negative: Different artwork
    """

    def __init__(
        self,
        data_file: str,
        image_dir: str,
        transform: Optional[transforms.Compose] = None
    ):
        """
        Args:
            data_file: JSON file containing triplet annotations
            image_dir: Root directory containing images
            transform: Image transformations
        """
        self.image_dir = Path(image_dir)
        self.transform = transform

        # Load annotations
        with open(data_file, 'r') as f:
            self.annotations = json.load(f)

        self.triplets = self.annotations['triplets']

        if self.transform is None:
            self.transform = self._default_transform()

    def _default_transform(self):
        """Default image preprocessing"""
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def __len__(self):
        return len(self.triplets)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Returns:
            anchor: Anchor image tensor
            positive: Positive (similar) image tensor
            negative: Negative (dissimilar) image tensor
        """
        triplet = self.triplets[idx]

        anchor_path = self.image_dir / triplet['anchor']
        positive_path = self.image_dir / triplet['positive']
        negative_path = self.image_dir / triplet['negative']

        # Load images
        anchor = Image.open(anchor_path).convert('RGB')
        positive = Image.open(positive_path).convert('RGB')
        negative = Image.open(negative_path).convert('RGB')

        # Apply transformations
        if self.transform:
            anchor = self.transform(anchor)
            positive = self.transform(positive)
            negative = self.transform(negative)

        return anchor, positive, negative


class OnlineArtworkTripletDataset(Dataset):
    """
    Online triplet mining dataset.
    Generates triplets on-the-fly by selecting hard negatives.
    More efficient for large datasets.
    """

    def __init__(
        self,
        data_file: str,
        image_dir: str,
        transform: Optional[transforms.Compose] = None,
        samples_per_class: int = 4
    ):
        """
        Args:
            data_file: JSON file with image paths and class labels
            image_dir: Root directory containing images
            transform: Image transformations
            samples_per_class: Number of samples per class in each batch
        """
        self.image_dir = Path(image_dir)
        self.transform = transform
        self.samples_per_class = samples_per_class

        # Load annotations
        with open(data_file, 'r') as f:
            self.annotations = json.load(f)

        # Organize images by class (artwork ID)
        self.class_to_images = {}
        for item in self.annotations['images']:
            class_id = item['artwork_id']
            if class_id not in self.class_to_images:
                self.class_to_images[class_id] = []
            self.class_to_images[class_id].append(item['path'])

        self.classes = list(self.class_to_images.keys())

        if self.transform is None:
            self.transform = self._default_transform()

    def _default_transform(self):
        """Default image preprocessing"""
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def __len__(self):
        return len(self.classes) * self.samples_per_class

    def __getitem__(self, idx: int):
        """Generate a sample with its class label"""
        class_idx = idx // self.samples_per_class
        class_id = self.classes[class_idx]

        # Random image from this class
        image_path = random.choice(self.class_to_images[class_id])
        image_full_path = self.image_dir / image_path

        image = Image.open(image_full_path).convert('RGB')

        if self.transform:
            image = self.transform(image)

        return image, class_id


def create_sample_annotations():
    """
    Helper function to create sample annotation files.
    Use this as a template for your actual data.
    """

    # Sample pair annotations
    pair_annotations = {
        "pairs": [
            {
                "image1": "original/artwork_1.jpg",
                "image2": "ai_generated/copy_1.jpg",
                "label": 1,  # Similar
                "similarity_score": 0.92
            },
            {
                "image1": "original/artwork_1.jpg",
                "image2": "original/artwork_2.jpg",
                "label": 0,  # Dissimilar
                "similarity_score": 0.23
            },
            # Add more pairs...
        ]
    }

    # Sample triplet annotations
    triplet_annotations = {
        "triplets": [
            {
                "anchor": "original/artwork_1.jpg",
                "positive": "ai_generated/copy_1.jpg",
                "negative": "original/artwork_2.jpg"
            },
            # Add more triplets...
        ]
    }

    # Sample online mining annotations
    online_annotations = {
        "images": [
            {
                "path": "original/artwork_1.jpg",
                "artwork_id": "artwork_1"
            },
            {
                "path": "ai_generated/copy_1_variant1.jpg",
                "artwork_id": "artwork_1"
            },
            {
                "path": "ai_generated/copy_1_variant2.jpg",
                "artwork_id": "artwork_1"
            },
            {
                "path": "original/artwork_2.jpg",
                "artwork_id": "artwork_2"
            },
            # Add more images...
        ]
    }

    return pair_annotations, triplet_annotations, online_annotations


def get_dataloaders(
    data_file: str,
    image_dir: str,
    batch_size: int = 32,
    num_workers: int = 4,
    dataset_type: str = 'pair',
    train_split: float = 0.8
) -> Tuple[DataLoader, DataLoader]:
    """
    Create train and validation dataloaders.

    Args:
        data_file: Path to annotation file
        image_dir: Path to image directory
        batch_size: Batch size
        num_workers: Number of worker processes
        dataset_type: 'pair', 'triplet', or 'online'
        train_split: Proportion of data for training

    Returns:
        train_loader, val_loader
    """

    # Select dataset class
    if dataset_type == 'pair':
        dataset_class = ArtworkPairDataset
    elif dataset_type == 'triplet':
        dataset_class = ArtworkTripletDataset
    elif dataset_type == 'online':
        dataset_class = OnlineArtworkTripletDataset
    else:
        raise ValueError(f"Unknown dataset type: {dataset_type}")

    # Create full dataset
    full_dataset = dataset_class(
        data_file=data_file,
        image_dir=image_dir
    )

    # Split into train and validation
    dataset_size = len(full_dataset)
    train_size = int(train_split * dataset_size)
    val_size = dataset_size - train_size

    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset,
        [train_size, val_size]
    )

    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )

    return train_loader, val_loader
