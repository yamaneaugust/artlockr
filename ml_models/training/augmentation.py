"""
Data augmentation strategies for artwork copyright detection training.
Includes both standard and artwork-specific augmentations.
"""
import torch
from torchvision import transforms
import random
from typing import Optional, Tuple
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np


class ArtworkAugmentation:
    """
    Custom augmentation pipeline for artwork images.
    Preserves artistic features while adding variation.
    """

    def __init__(
        self,
        image_size: int = 224,
        augmentation_level: str = 'medium'
    ):
        """
        Args:
            image_size: Target image size
            augmentation_level: 'light', 'medium', or 'heavy'
        """
        self.image_size = image_size
        self.augmentation_level = augmentation_level

        # Base transforms
        self.base_transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        # Training augmentation
        if augmentation_level == 'light':
            self.train_transform = self._light_augmentation()
        elif augmentation_level == 'medium':
            self.train_transform = self._medium_augmentation()
        elif augmentation_level == 'heavy':
            self.train_transform = self._heavy_augmentation()
        else:
            raise ValueError(f"Unknown augmentation level: {augmentation_level}")

    def _light_augmentation(self):
        """Light augmentation - minimal changes"""
        return transforms.Compose([
            transforms.Resize(256),
            transforms.RandomCrop(self.image_size),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def _medium_augmentation(self):
        """Medium augmentation - balanced"""
        return transforms.Compose([
            transforms.Resize(256),
            transforms.RandomResizedCrop(
                self.image_size,
                scale=(0.8, 1.0),
                ratio=(0.9, 1.1)
            ),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomApply([
                transforms.ColorJitter(
                    brightness=0.2,
                    contrast=0.2,
                    saturation=0.2,
                    hue=0.1
                )
            ], p=0.5),
            transforms.RandomApply([
                transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 2.0))
            ], p=0.3),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def _heavy_augmentation(self):
        """Heavy augmentation - maximum variation"""
        return transforms.Compose([
            transforms.Resize(256),
            transforms.RandomResizedCrop(
                self.image_size,
                scale=(0.7, 1.0),
                ratio=(0.8, 1.2)
            ),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=15),
            transforms.RandomApply([
                transforms.ColorJitter(
                    brightness=0.3,
                    contrast=0.3,
                    saturation=0.3,
                    hue=0.2
                )
            ], p=0.7),
            transforms.RandomApply([
                transforms.GaussianBlur(kernel_size=5, sigma=(0.1, 2.0))
            ], p=0.5),
            transforms.RandomGrayscale(p=0.1),
            transforms.ToTensor(),
            transforms.RandomApply([
                AddGaussianNoise(mean=0.0, std=0.05)
            ], p=0.3),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def get_train_transform(self):
        """Get training augmentation"""
        return self.train_transform

    def get_val_transform(self):
        """Get validation transform (no augmentation)"""
        return self.base_transform


class AddGaussianNoise:
    """Add Gaussian noise to tensor images"""

    def __init__(self, mean: float = 0.0, std: float = 0.1):
        self.mean = mean
        self.std = std

    def __call__(self, tensor: torch.Tensor) -> torch.Tensor:
        noise = torch.randn(tensor.size()) * self.std + self.mean
        return tensor + noise

    def __repr__(self):
        return f"{self.__class__.__name__}(mean={self.mean}, std={self.std})"


class CopyrightSimulationAugmentation:
    """
    Simulates common copyright infringement patterns.
    Helps model learn to detect AI-generated variations.
    """

    def __init__(self, p: float = 0.5):
        """
        Args:
            p: Probability of applying augmentation
        """
        self.p = p

    def __call__(self, img: Image.Image) -> Image.Image:
        """Apply copyright simulation augmentations"""
        if random.random() < self.p:
            # Randomly select an augmentation
            augmentation = random.choice([
                self._style_transfer_sim,
                self._compression_artifacts,
                self._watermark_removal_sim,
                self._color_grading,
                self._detail_modification
            ])
            img = augmentation(img)

        return img

    def _style_transfer_sim(self, img: Image.Image) -> Image.Image:
        """Simulate style transfer effects"""
        # Apply edge enhancement and smoothing
        img = img.filter(ImageFilter.SMOOTH_MORE)
        img = img.filter(ImageFilter.EDGE_ENHANCE)
        return img

    def _compression_artifacts(self, img: Image.Image) -> Image.Image:
        """Simulate compression artifacts"""
        # Apply JPEG compression
        import io
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=random.randint(60, 90))
        buffer.seek(0)
        img = Image.open(buffer)
        return img

    def _watermark_removal_sim(self, img: Image.Image) -> Image.Image:
        """Simulate watermark removal (inpainting-like blur)"""
        # Random region blur
        width, height = img.size
        x1 = random.randint(0, width // 2)
        y1 = random.randint(0, height // 2)
        x2 = x1 + random.randint(width // 4, width // 2)
        y2 = y1 + random.randint(height // 4, height // 2)

        region = img.crop((x1, y1, x2, y2))
        region = region.filter(ImageFilter.GaussianBlur(radius=5))
        img.paste(region, (x1, y1))

        return img

    def _color_grading(self, img: Image.Image) -> Image.Image:
        """Simulate color grading changes"""
        # Random color adjustments
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(random.uniform(0.8, 1.2))

        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(random.uniform(0.9, 1.1))

        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(random.uniform(0.9, 1.1))

        return img

    def _detail_modification(self, img: Image.Image) -> Image.Image:
        """Simulate detail modifications"""
        # Apply slight sharpening or smoothing
        if random.random() < 0.5:
            img = img.filter(ImageFilter.SHARPEN)
        else:
            img = img.filter(ImageFilter.SMOOTH)

        return img


class MixupAugmentation:
    """
    Mixup augmentation for metric learning.
    Mixes pairs of images to create synthetic training samples.
    """

    def __init__(self, alpha: float = 0.2):
        """
        Args:
            alpha: Mixup interpolation strength
        """
        self.alpha = alpha

    def __call__(
        self,
        img1: torch.Tensor,
        img2: torch.Tensor
    ) -> Tuple[torch.Tensor, float]:
        """
        Mix two images.

        Args:
            img1: First image tensor
            img2: Second image tensor

        Returns:
            Mixed image and mixing coefficient
        """
        if self.alpha > 0:
            lam = np.random.beta(self.alpha, self.alpha)
        else:
            lam = 1.0

        mixed_img = lam * img1 + (1 - lam) * img2

        return mixed_img, lam


class CutmixAugmentation:
    """
    Cutmix augmentation - cuts and pastes patches between images.
    """

    def __init__(self, alpha: float = 1.0):
        """
        Args:
            alpha: Cutmix patch size parameter
        """
        self.alpha = alpha

    def __call__(
        self,
        img1: torch.Tensor,
        img2: torch.Tensor
    ) -> Tuple[torch.Tensor, float]:
        """
        Apply cutmix.

        Args:
            img1: First image tensor [C, H, W]
            img2: Second image tensor [C, H, W]

        Returns:
            Mixed image and mixing ratio
        """
        lam = np.random.beta(self.alpha, self.alpha)

        _, h, w = img1.shape

        # Random bounding box
        cut_rat = np.sqrt(1.0 - lam)
        cut_w = int(w * cut_rat)
        cut_h = int(h * cut_rat)

        cx = np.random.randint(w)
        cy = np.random.randint(h)

        bbx1 = np.clip(cx - cut_w // 2, 0, w)
        bby1 = np.clip(cy - cut_h // 2, 0, h)
        bbx2 = np.clip(cx + cut_w // 2, 0, w)
        bby2 = np.clip(cy + cut_h // 2, 0, h)

        # Mix images
        mixed_img = img1.clone()
        mixed_img[:, bby1:bby2, bbx1:bbx2] = img2[:, bby1:bby2, bbx1:bbx2]

        # Adjust lambda to actual patch area
        lam = 1 - ((bbx2 - bbx1) * (bby2 - bby1) / (w * h))

        return mixed_img, lam


def get_augmentation_pipeline(
    augmentation_type: str = 'medium',
    image_size: int = 224,
    **kwargs
) -> transforms.Compose:
    """
    Factory function for augmentation pipelines.

    Args:
        augmentation_type: 'light', 'medium', 'heavy', or 'copyright_sim'
        image_size: Target image size
        **kwargs: Additional augmentation parameters

    Returns:
        Augmentation pipeline
    """
    if augmentation_type in ['light', 'medium', 'heavy']:
        aug = ArtworkAugmentation(
            image_size=image_size,
            augmentation_level=augmentation_type
        )
        return aug.get_train_transform()

    elif augmentation_type == 'copyright_sim':
        return transforms.Compose([
            CopyrightSimulationAugmentation(p=0.7),
            transforms.Resize(256),
            transforms.RandomCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    else:
        raise ValueError(f"Unknown augmentation type: {augmentation_type}")


# Standard validation transform (no augmentation)
def get_val_transform(image_size: int = 224) -> transforms.Compose:
    """Get validation transform without augmentation"""
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(image_size),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
