"""
Siamese and Triplet network architectures for copyright detection.
Fine-tunes ResNet for similarity learning.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
from typing import Optional


class SiameseNetwork(nn.Module):
    """
    Siamese Network using ResNet backbone.
    Shares weights between twin networks for comparing image pairs.
    """

    def __init__(
        self,
        backbone: str = 'resnet50',
        pretrained: bool = True,
        embedding_dim: int = 128,
        freeze_backbone: bool = False
    ):
        """
        Args:
            backbone: ResNet variant ('resnet50', 'resnet101', 'resnet152')
            pretrained: Use ImageNet pretrained weights
            embedding_dim: Dimension of output embedding
            freeze_backbone: Freeze backbone weights during training
        """
        super(SiameseNetwork, self).__init__()

        self.embedding_dim = embedding_dim

        # Load ResNet backbone
        if backbone == 'resnet50':
            if pretrained:
                self.backbone = models.resnet50(weights='IMAGENET1K_V2')
            else:
                self.backbone = models.resnet50(weights=None)
            feature_dim = 2048
        elif backbone == 'resnet101':
            if pretrained:
                self.backbone = models.resnet101(weights='IMAGENET1K_V2')
            else:
                self.backbone = models.resnet101(weights=None)
            feature_dim = 2048
        elif backbone == 'resnet152':
            if pretrained:
                self.backbone = models.resnet152(weights='IMAGENET1K_V2')
            else:
                self.backbone = models.resnet152(weights=None)
            feature_dim = 2048
        else:
            raise ValueError(f"Unknown backbone: {backbone}")

        # Remove final classification layer
        self.backbone = nn.Sequential(*list(self.backbone.children())[:-1])

        # Freeze backbone if specified
        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False

        # Embedding projection head
        self.embedding_head = nn.Sequential(
            nn.Linear(feature_dim, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, embedding_dim)
        )

    def forward_one(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for a single image.

        Args:
            x: Input image tensor [B, C, H, W]

        Returns:
            Embedding vector [B, embedding_dim]
        """
        # Extract features
        features = self.backbone(x)
        features = features.view(features.size(0), -1)

        # Project to embedding space
        embedding = self.embedding_head(features)

        # L2 normalize
        embedding = F.normalize(embedding, p=2, dim=1)

        return embedding

    def forward(self, x1: torch.Tensor, x2: torch.Tensor) -> tuple:
        """
        Forward pass for image pair.

        Args:
            x1: First image tensor [B, C, H, W]
            x2: Second image tensor [B, C, H, W]

        Returns:
            (embedding1, embedding2)
        """
        embedding1 = self.forward_one(x1)
        embedding2 = self.forward_one(x2)

        return embedding1, embedding2


class TripletNetwork(nn.Module):
    """
    Triplet Network using ResNet backbone.
    Processes anchor, positive, and negative samples.
    """

    def __init__(
        self,
        backbone: str = 'resnet50',
        pretrained: bool = True,
        embedding_dim: int = 128,
        freeze_backbone: bool = False
    ):
        """
        Args:
            backbone: ResNet variant
            pretrained: Use ImageNet pretrained weights
            embedding_dim: Dimension of output embedding
            freeze_backbone: Freeze backbone weights during training
        """
        super(TripletNetwork, self).__init__()

        self.embedding_dim = embedding_dim

        # Load ResNet backbone
        if backbone == 'resnet50':
            if pretrained:
                self.backbone = models.resnet50(weights='IMAGENET1K_V2')
            else:
                self.backbone = models.resnet50(weights=None)
            feature_dim = 2048
        elif backbone == 'resnet101':
            if pretrained:
                self.backbone = models.resnet101(weights='IMAGENET1K_V2')
            else:
                self.backbone = models.resnet101(weights=None)
            feature_dim = 2048
        elif backbone == 'resnet152':
            if pretrained:
                self.backbone = models.resnet152(weights='IMAGENET1K_V2')
            else:
                self.backbone = models.resnet152(weights=None)
            feature_dim = 2048
        else:
            raise ValueError(f"Unknown backbone: {backbone}")

        # Remove final classification layer
        self.backbone = nn.Sequential(*list(self.backbone.children())[:-1])

        # Freeze backbone if specified
        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False

        # Embedding projection head
        self.embedding_head = nn.Sequential(
            nn.Linear(feature_dim, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, embedding_dim)
        )

    def forward_one(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass for a single image"""
        features = self.backbone(x)
        features = features.view(features.size(0), -1)
        embedding = self.embedding_head(features)
        embedding = F.normalize(embedding, p=2, dim=1)
        return embedding

    def forward(
        self,
        anchor: torch.Tensor,
        positive: torch.Tensor,
        negative: torch.Tensor
    ) -> tuple:
        """
        Forward pass for triplet.

        Args:
            anchor: Anchor image tensor
            positive: Positive image tensor
            negative: Negative image tensor

        Returns:
            (anchor_embedding, positive_embedding, negative_embedding)
        """
        anchor_embedding = self.forward_one(anchor)
        positive_embedding = self.forward_one(positive)
        negative_embedding = self.forward_one(negative)

        return anchor_embedding, positive_embedding, negative_embedding


class EmbeddingNetwork(nn.Module):
    """
    Single embedding network for metric learning.
    Can be used with various loss functions.
    """

    def __init__(
        self,
        backbone: str = 'resnet50',
        pretrained: bool = True,
        embedding_dim: int = 128,
        freeze_backbone: bool = False,
        use_attention: bool = False
    ):
        """
        Args:
            backbone: ResNet variant
            pretrained: Use ImageNet pretrained weights
            embedding_dim: Dimension of output embedding
            freeze_backbone: Freeze backbone weights
            use_attention: Add attention mechanism
        """
        super(EmbeddingNetwork, self).__init__()

        self.embedding_dim = embedding_dim
        self.use_attention = use_attention

        # Load ResNet backbone
        if backbone == 'resnet50':
            if pretrained:
                resnet = models.resnet50(weights='IMAGENET1K_V2')
            else:
                resnet = models.resnet50(weights=None)
            feature_dim = 2048
        elif backbone == 'resnet101':
            if pretrained:
                resnet = models.resnet101(weights='IMAGENET1K_V2')
            else:
                resnet = models.resnet101(weights=None)
            feature_dim = 2048
        elif backbone == 'resnet152':
            if pretrained:
                resnet = models.resnet152(weights='IMAGENET1K_V2')
            else:
                resnet = models.resnet152(weights=None)
            feature_dim = 2048
        else:
            raise ValueError(f"Unknown backbone: {backbone}")

        # Extract layers before final pooling
        self.conv_layers = nn.Sequential(*list(resnet.children())[:-2])
        self.avg_pool = nn.AdaptiveAvgPool2d((1, 1))

        # Freeze backbone if specified
        if freeze_backbone:
            for param in self.conv_layers.parameters():
                param.requires_grad = False

        # Optional attention mechanism
        if use_attention:
            self.attention = nn.Sequential(
                nn.Conv2d(feature_dim, feature_dim // 8, 1),
                nn.ReLU(inplace=True),
                nn.Conv2d(feature_dim // 8, 1, 1),
                nn.Sigmoid()
            )

        # Embedding projection head
        self.embedding_head = nn.Sequential(
            nn.Linear(feature_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, embedding_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input image tensor [B, C, H, W]

        Returns:
            Normalized embedding [B, embedding_dim]
        """
        # Convolutional features
        features = self.conv_layers(x)  # [B, 2048, 7, 7]

        # Apply attention if enabled
        if self.use_attention:
            attention_weights = self.attention(features)  # [B, 1, 7, 7]
            features = features * attention_weights  # Weighted features

        # Global average pooling
        features = self.avg_pool(features)  # [B, 2048, 1, 1]
        features = features.view(features.size(0), -1)  # [B, 2048]

        # Project to embedding space
        embedding = self.embedding_head(features)  # [B, embedding_dim]

        # L2 normalize
        embedding = F.normalize(embedding, p=2, dim=1)

        return embedding


def create_model(
    model_type: str = 'siamese',
    backbone: str = 'resnet50',
    pretrained: bool = True,
    embedding_dim: int = 128,
    freeze_backbone: bool = False,
    **kwargs
) -> nn.Module:
    """
    Factory function to create models.

    Args:
        model_type: 'siamese', 'triplet', or 'embedding'
        backbone: ResNet variant
        pretrained: Use pretrained weights
        embedding_dim: Embedding dimension
        freeze_backbone: Freeze backbone
        **kwargs: Additional model-specific arguments

    Returns:
        Model instance
    """
    if model_type == 'siamese':
        return SiameseNetwork(
            backbone=backbone,
            pretrained=pretrained,
            embedding_dim=embedding_dim,
            freeze_backbone=freeze_backbone
        )
    elif model_type == 'triplet':
        return TripletNetwork(
            backbone=backbone,
            pretrained=pretrained,
            embedding_dim=embedding_dim,
            freeze_backbone=freeze_backbone
        )
    elif model_type == 'embedding':
        return EmbeddingNetwork(
            backbone=backbone,
            pretrained=pretrained,
            embedding_dim=embedding_dim,
            freeze_backbone=freeze_backbone,
            **kwargs
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
