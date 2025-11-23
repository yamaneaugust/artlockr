"""
Loss functions for similarity learning in copyright detection.
Includes Contrastive Loss, Triplet Loss, and variants.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class ContrastiveLoss(nn.Module):
    """
    Contrastive Loss for Siamese networks.

    Pulls similar pairs closer and pushes dissimilar pairs apart.
    Loss = (1 - label) * 0.5 * D^2 + label * 0.5 * max(margin - D, 0)^2

    Where:
    - D is the Euclidean distance between embeddings
    - label = 0 for similar pairs, 1 for dissimilar pairs
    - margin is the minimum distance for dissimilar pairs
    """

    def __init__(self, margin: float = 1.0):
        """
        Args:
            margin: Margin for dissimilar pairs
        """
        super(ContrastiveLoss, self).__init__()
        self.margin = margin

    def forward(
        self,
        embedding1: torch.Tensor,
        embedding2: torch.Tensor,
        label: torch.Tensor
    ) -> torch.Tensor:
        """
        Calculate contrastive loss.

        Args:
            embedding1: First embedding [B, D]
            embedding2: Second embedding [B, D]
            label: Labels [B], 0 for similar, 1 for dissimilar

        Returns:
            Loss value
        """
        # Calculate Euclidean distance
        distance = F.pairwise_distance(embedding1, embedding2, p=2)

        # Calculate loss
        # Similar pairs: minimize distance
        # Dissimilar pairs: maximize distance up to margin
        loss_similar = (1 - label) * torch.pow(distance, 2)
        loss_dissimilar = label * torch.pow(
            torch.clamp(self.margin - distance, min=0.0), 2
        )

        loss = 0.5 * (loss_similar + loss_dissimilar)

        return loss.mean()


class TripletLoss(nn.Module):
    """
    Triplet Loss with hard negative mining.

    Loss = max(D(anchor, positive) - D(anchor, negative) + margin, 0)

    Ensures that the positive is closer to the anchor than the negative by at least margin.
    """

    def __init__(self, margin: float = 0.2, mining: str = 'batch_hard'):
        """
        Args:
            margin: Margin between positive and negative distances
            mining: Mining strategy ('batch_hard', 'batch_all', 'none')
        """
        super(TripletLoss, self).__init__()
        self.margin = margin
        self.mining = mining

    def forward(
        self,
        anchor: torch.Tensor,
        positive: torch.Tensor,
        negative: torch.Tensor
    ) -> torch.Tensor:
        """
        Calculate triplet loss.

        Args:
            anchor: Anchor embeddings [B, D]
            positive: Positive embeddings [B, D]
            negative: Negative embeddings [B, D]

        Returns:
            Loss value
        """
        # Calculate distances
        pos_distance = F.pairwise_distance(anchor, positive, p=2)
        neg_distance = F.pairwise_distance(anchor, negative, p=2)

        # Triplet loss
        losses = torch.relu(pos_distance - neg_distance + self.margin)

        return losses.mean()

    def batch_hard_triplet_loss(
        self,
        embeddings: torch.Tensor,
        labels: torch.Tensor
    ) -> torch.Tensor:
        """
        Batch hard triplet loss with online mining.

        For each anchor:
        - Hardest positive: most distant sample with same label
        - Hardest negative: closest sample with different label

        Args:
            embeddings: All embeddings in batch [B, D]
            labels: Class labels [B]

        Returns:
            Loss value
        """
        # Compute pairwise distance matrix
        pairwise_dist = torch.cdist(embeddings, embeddings, p=2)

        # Create masks for positive and negative pairs
        labels = labels.unsqueeze(0)
        mask_positive = labels == labels.t()
        mask_negative = labels != labels.t()

        # For numerical stability
        mask_positive = mask_positive.float()
        mask_negative = mask_negative.float()

        # Find hardest positive for each anchor
        # (most distant positive)
        hardest_positive_dist, _ = (pairwise_dist * mask_positive).max(dim=1)

        # Find hardest negative for each anchor
        # (closest negative)
        max_anchor_negative_dist = pairwise_dist.max()
        hardest_negative_dist, _ = (
            pairwise_dist + max_anchor_negative_dist * (1.0 - mask_negative)
        ).min(dim=1)

        # Triplet loss
        losses = torch.relu(
            hardest_positive_dist - hardest_negative_dist + self.margin
        )

        return losses.mean()


class OnlineTripletLoss(nn.Module):
    """
    Online triplet loss with mining strategies.
    Mines triplets from a batch of embeddings and labels.
    """

    def __init__(
        self,
        margin: float = 0.2,
        mining_strategy: str = 'hard'
    ):
        """
        Args:
            margin: Triplet margin
            mining_strategy: 'hard', 'semi-hard', or 'all'
        """
        super(OnlineTripletLoss, self).__init__()
        self.margin = margin
        self.mining_strategy = mining_strategy

    def forward(
        self,
        embeddings: torch.Tensor,
        labels: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            embeddings: Batch of embeddings [B, D]
            labels: Class labels [B]

        Returns:
            Loss value
        """
        if self.mining_strategy == 'hard':
            return self._hard_mining(embeddings, labels)
        elif self.mining_strategy == 'semi-hard':
            return self._semi_hard_mining(embeddings, labels)
        elif self.mining_strategy == 'all':
            return self._all_triplets(embeddings, labels)
        else:
            raise ValueError(f"Unknown mining strategy: {self.mining_strategy}")

    def _hard_mining(
        self,
        embeddings: torch.Tensor,
        labels: torch.Tensor
    ) -> torch.Tensor:
        """Hard negative mining"""
        # Compute pairwise distances
        pairwise_dist = torch.cdist(embeddings, embeddings, p=2)

        # Create masks
        labels_equal = labels.unsqueeze(0) == labels.unsqueeze(1)
        labels_not_equal = ~labels_equal

        # Remove diagonal (self-comparisons)
        labels_equal = labels_equal.float()
        labels_equal = labels_equal - torch.eye(
            labels_equal.size(0), device=labels_equal.device
        )

        # Find hardest positive
        hardest_positive_dist, _ = (pairwise_dist * labels_equal).max(dim=1)

        # Find hardest negative
        max_dist = pairwise_dist.max()
        hardest_negative_dist, _ = (
            pairwise_dist + max_dist * (~labels_not_equal).float()
        ).min(dim=1)

        # Calculate loss
        losses = torch.relu(
            hardest_positive_dist - hardest_negative_dist + self.margin
        )

        return losses.mean()

    def _semi_hard_mining(
        self,
        embeddings: torch.Tensor,
        labels: torch.Tensor
    ) -> torch.Tensor:
        """
        Semi-hard negative mining.
        Negatives that are farther than positive but within margin.
        """
        pairwise_dist = torch.cdist(embeddings, embeddings, p=2)

        labels_equal = labels.unsqueeze(0) == labels.unsqueeze(1)
        labels_equal = labels_equal.float()
        labels_equal = labels_equal - torch.eye(
            labels_equal.size(0), device=labels_equal.device
        )

        # Calculate anchor-positive distances
        ap_distances = pairwise_dist * labels_equal

        # For each anchor, find all valid positives
        valid_positives = labels_equal > 0

        # Calculate all triplet losses
        losses = []
        for i in range(embeddings.size(0)):
            if valid_positives[i].sum() == 0:
                continue

            # Get positive distances for this anchor
            pos_dists = ap_distances[i][valid_positives[i]]

            # Get negative distances
            neg_mask = ~labels_equal[i].bool()
            neg_dists = pairwise_dist[i][neg_mask]

            # For each positive, find semi-hard negatives
            for pos_dist in pos_dists:
                # Semi-hard: d(a,n) > d(a,p) and d(a,n) < d(a,p) + margin
                semi_hard_negatives = (neg_dists > pos_dist) & (
                    neg_dists < pos_dist + self.margin
                )

                if semi_hard_negatives.sum() > 0:
                    # Use hardest semi-hard negative
                    neg_dist = neg_dists[semi_hard_negatives].min()
                    loss = pos_dist - neg_dist + self.margin
                    losses.append(loss)

        if len(losses) == 0:
            return torch.tensor(0.0, device=embeddings.device)

        return torch.stack(losses).mean()

    def _all_triplets(
        self,
        embeddings: torch.Tensor,
        labels: torch.Tensor
    ) -> torch.Tensor:
        """Use all valid triplets"""
        pairwise_dist = torch.cdist(embeddings, embeddings, p=2)

        labels_equal = labels.unsqueeze(0) == labels.unsqueeze(1)

        # Get anchor-positive pairs
        i_indices, j_indices = torch.where(
            labels_equal & ~torch.eye(
                labels.size(0), dtype=torch.bool, device=labels.device
            )
        )

        # Get anchor-negative pairs
        i_neg_indices, k_indices = torch.where(~labels_equal)

        # Form all valid triplets
        losses = []
        for i, j in zip(i_indices, j_indices):
            neg_indices = k_indices[i_neg_indices == i]
            for k in neg_indices:
                loss = torch.relu(
                    pairwise_dist[i, j] - pairwise_dist[i, k] + self.margin
                )
                losses.append(loss)

        if len(losses) == 0:
            return torch.tensor(0.0, device=embeddings.device)

        return torch.stack(losses).mean()


class AngularLoss(nn.Module):
    """
    Angular loss - alternative to triplet loss using angles.
    """

    def __init__(self, alpha: float = 45.0):
        """
        Args:
            alpha: Angular margin in degrees
        """
        super(AngularLoss, self).__init__()
        self.alpha = alpha * torch.pi / 180.0  # Convert to radians

    def forward(
        self,
        anchor: torch.Tensor,
        positive: torch.Tensor,
        negative: torch.Tensor
    ) -> torch.Tensor:
        """Calculate angular loss"""
        # Calculate angles
        ap_similarity = F.cosine_similarity(anchor, positive)
        an_similarity = F.cosine_similarity(anchor, negative)

        # Convert to angles (acos of cosine similarity)
        ap_angle = torch.acos(torch.clamp(ap_similarity, -1.0 + 1e-7, 1.0 - 1e-7))
        an_angle = torch.acos(torch.clamp(an_similarity, -1.0 + 1e-7, 1.0 - 1e-7))

        # Angular loss
        losses = torch.relu(ap_angle - an_angle + self.alpha)

        return losses.mean()


class ArcFaceLoss(nn.Module):
    """
    ArcFace loss for metric learning.
    Adds angular margin to improve feature discrimination.
    """

    def __init__(
        self,
        embedding_dim: int,
        num_classes: int,
        margin: float = 0.5,
        scale: float = 64.0
    ):
        """
        Args:
            embedding_dim: Dimension of embeddings
            num_classes: Number of classes
            margin: Angular margin
            scale: Feature scale
        """
        super(ArcFaceLoss, self).__init__()
        self.embedding_dim = embedding_dim
        self.num_classes = num_classes
        self.margin = margin
        self.scale = scale

        # Weight matrix
        self.weight = nn.Parameter(
            torch.FloatTensor(num_classes, embedding_dim)
        )
        nn.init.xavier_uniform_(self.weight)

        self.ce = nn.CrossEntropyLoss()

    def forward(
        self,
        embeddings: torch.Tensor,
        labels: torch.Tensor
    ) -> torch.Tensor:
        """Calculate ArcFace loss"""
        # Normalize embeddings and weights
        embeddings = F.normalize(embeddings, p=2, dim=1)
        weights = F.normalize(self.weight, p=2, dim=1)

        # Cosine similarity
        cosine = F.linear(embeddings, weights)

        # Add angular margin
        theta = torch.acos(torch.clamp(cosine, -1.0 + 1e-7, 1.0 - 1e-7))

        # One-hot encoding
        one_hot = torch.zeros_like(cosine)
        one_hot.scatter_(1, labels.view(-1, 1), 1)

        # Add margin to target class
        theta_m = theta + one_hot * self.margin

        # Convert back to cosine
        cosine_m = torch.cos(theta_m)

        # Scale
        output = cosine_m * self.scale

        # Cross entropy loss
        loss = self.ce(output, labels)

        return loss


def get_loss_function(
    loss_type: str,
    margin: float = 0.2,
    **kwargs
) -> nn.Module:
    """
    Factory function for loss functions.

    Args:
        loss_type: 'contrastive', 'triplet', 'online_triplet', 'angular', 'arcface'
        margin: Loss margin
        **kwargs: Additional loss-specific parameters

    Returns:
        Loss function instance
    """
    if loss_type == 'contrastive':
        return ContrastiveLoss(margin=margin)
    elif loss_type == 'triplet':
        return TripletLoss(margin=margin, **kwargs)
    elif loss_type == 'online_triplet':
        return OnlineTripletLoss(margin=margin, **kwargs)
    elif loss_type == 'angular':
        return AngularLoss(**kwargs)
    elif loss_type == 'arcface':
        return ArcFaceLoss(**kwargs)
    else:
        raise ValueError(f"Unknown loss type: {loss_type}")
