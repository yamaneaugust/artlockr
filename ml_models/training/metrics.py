"""
Evaluation metrics for copyright detection models.
Includes similarity metrics, retrieval metrics, and visualization.
"""
import torch
import torch.nn as nn
import numpy as np
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt
from pathlib import Path


class SimilarityMetrics:
    """
    Calculate various similarity and retrieval metrics.
    """

    @staticmethod
    def euclidean_distance(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate Euclidean distance"""
        return np.linalg.norm(emb1 - emb2)

    @staticmethod
    def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        return np.dot(emb1, emb2) / (
            np.linalg.norm(emb1) * np.linalg.norm(emb2) + 1e-8
        )

    @staticmethod
    def manhattan_distance(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate Manhattan distance"""
        return np.sum(np.abs(emb1 - emb2))


def calculate_accuracy_at_threshold(
    distances: np.ndarray,
    labels: np.ndarray,
    threshold: float
) -> float:
    """
    Calculate accuracy at a specific threshold.

    Args:
        distances: Pairwise distances
        labels: True labels (0 = similar, 1 = dissimilar)
        threshold: Distance threshold

    Returns:
        Accuracy
    """
    predictions = (distances < threshold).astype(int)
    accuracy = np.mean(predictions == (1 - labels))
    return accuracy


def calculate_roc_auc(
    distances: np.ndarray,
    labels: np.ndarray
) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate ROC curve and AUC.

    Args:
        distances: Pairwise distances
        labels: True labels (0 = similar, 1 = dissimilar)

    Returns:
        AUC score, false positive rates, true positive rates, thresholds
    """
    # Convert distances to similarity scores (inverse)
    similarities = 1 - (distances / (distances.max() + 1e-8))

    # Convert labels (0 = similar -> 1, 1 = dissimilar -> 0)
    binary_labels = 1 - labels

    fpr, tpr, thresholds = roc_curve(binary_labels, similarities)
    roc_auc = auc(fpr, tpr)

    return roc_auc, fpr, tpr, thresholds


def calculate_precision_recall(
    distances: np.ndarray,
    labels: np.ndarray
) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate precision-recall curve and average precision.

    Args:
        distances: Pairwise distances
        labels: True labels

    Returns:
        Average precision, precision values, recall values, thresholds
    """
    similarities = 1 - (distances / (distances.max() + 1e-8))
    binary_labels = 1 - labels

    precision, recall, thresholds = precision_recall_curve(
        binary_labels, similarities
    )
    avg_precision = average_precision_score(binary_labels, similarities)

    return avg_precision, precision, recall, thresholds


def calculate_retrieval_metrics(
    query_embeddings: np.ndarray,
    gallery_embeddings: np.ndarray,
    query_labels: np.ndarray,
    gallery_labels: np.ndarray,
    k_values: List[int] = [1, 5, 10, 20]
) -> Dict[str, float]:
    """
    Calculate retrieval metrics (Precision@K, Recall@K, mAP).

    Args:
        query_embeddings: Query image embeddings [N, D]
        gallery_embeddings: Gallery image embeddings [M, D]
        query_labels: Query labels [N]
        gallery_labels: Gallery labels [M]
        k_values: K values for precision/recall@K

    Returns:
        Dictionary of metrics
    """
    metrics = {}
    num_queries = len(query_embeddings)

    # Calculate pairwise distances
    distances = np.zeros((num_queries, len(gallery_embeddings)))
    for i in range(num_queries):
        for j in range(len(gallery_embeddings)):
            distances[i, j] = np.linalg.norm(
                query_embeddings[i] - gallery_embeddings[j]
            )

    # Calculate metrics for each K
    for k in k_values:
        precision_at_k = []
        recall_at_k = []

        for i in range(num_queries):
            # Get top-K nearest neighbors
            sorted_indices = np.argsort(distances[i])[:k]
            retrieved_labels = gallery_labels[sorted_indices]

            # Calculate precision and recall
            relevant = np.sum(retrieved_labels == query_labels[i])
            total_relevant = np.sum(gallery_labels == query_labels[i])

            precision = relevant / k if k > 0 else 0
            recall = relevant / total_relevant if total_relevant > 0 else 0

            precision_at_k.append(precision)
            recall_at_k.append(recall)

        metrics[f'precision@{k}'] = np.mean(precision_at_k)
        metrics[f'recall@{k}'] = np.mean(recall_at_k)

    # Calculate mAP (mean Average Precision)
    average_precisions = []
    for i in range(num_queries):
        sorted_indices = np.argsort(distances[i])
        retrieved_labels = gallery_labels[sorted_indices]

        precisions = []
        num_relevant = 0

        for j, label in enumerate(retrieved_labels):
            if label == query_labels[i]:
                num_relevant += 1
                precision = num_relevant / (j + 1)
                precisions.append(precision)

        if precisions:
            average_precisions.append(np.mean(precisions))

    metrics['mAP'] = np.mean(average_precisions) if average_precisions else 0.0

    return metrics


def evaluate_model(
    model: nn.Module,
    dataloader: torch.utils.data.DataLoader,
    device: torch.device,
    model_type: str = 'siamese'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Evaluate model on a dataset.

    Args:
        model: Trained model
        dataloader: Data loader
        device: Device
        model_type: 'siamese' or 'triplet'

    Returns:
        (distances, labels)
    """
    model.eval()
    all_distances = []
    all_labels = []

    with torch.no_grad():
        for batch_data in dataloader:
            if model_type == 'siamese':
                img1, img2, labels = batch_data
                img1 = img1.to(device)
                img2 = img2.to(device)

                # Get embeddings
                if hasattr(model, 'forward_one'):
                    emb1 = model.forward_one(img1)
                    emb2 = model.forward_one(img2)
                else:
                    emb1, emb2 = model(img1, img2)

                # Calculate distances
                distances = torch.nn.functional.pairwise_distance(
                    emb1, emb2
                ).cpu().numpy()

                all_distances.extend(distances)
                all_labels.extend(labels.cpu().numpy())

    return np.array(all_distances), np.array(all_labels)


def plot_training_history(history: Dict, save_path: str = None):
    """
    Plot training history.

    Args:
        history: Training history dictionary
        save_path: Path to save plot
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Loss plot
    axes[0, 0].plot(history['train_loss'], label='Train Loss')
    axes[0, 0].plot(history['val_loss'], label='Val Loss')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].set_title('Training and Validation Loss')
    axes[0, 0].legend()
    axes[0, 0].grid(True)

    # Learning rate plot
    axes[0, 1].plot(history['learning_rate'])
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('Learning Rate')
    axes[0, 1].set_title('Learning Rate Schedule')
    axes[0, 1].grid(True)
    axes[0, 1].set_yscale('log')

    # Epoch time plot
    axes[1, 0].plot(history['epoch_time'])
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('Time (seconds)')
    axes[1, 0].set_title('Epoch Training Time')
    axes[1, 0].grid(True)

    # Loss difference plot
    loss_diff = np.array(history['train_loss']) - np.array(history['val_loss'])
    axes[1, 1].plot(loss_diff)
    axes[1, 1].axhline(y=0, color='r', linestyle='--')
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].set_ylabel('Train Loss - Val Loss')
    axes[1, 1].set_title('Overfitting Monitor')
    axes[1, 1].grid(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved training history plot to {save_path}")

    plt.close()


def plot_roc_curve(
    fpr: np.ndarray,
    tpr: np.ndarray,
    roc_auc: float,
    save_path: str = None
):
    """
    Plot ROC curve.

    Args:
        fpr: False positive rates
        tpr: True positive rates
        roc_auc: AUC score
        save_path: Path to save plot
    """
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.legend()
    plt.grid(True)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved ROC curve to {save_path}")

    plt.close()


def plot_precision_recall_curve(
    precision: np.ndarray,
    recall: np.ndarray,
    avg_precision: float,
    save_path: str = None
):
    """
    Plot precision-recall curve.

    Args:
        precision: Precision values
        recall: Recall values
        avg_precision: Average precision score
        save_path: Path to save plot
    """
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, label=f'PR Curve (AP = {avg_precision:.3f})')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend()
    plt.grid(True)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved PR curve to {save_path}")

    plt.close()


def find_optimal_threshold(
    distances: np.ndarray,
    labels: np.ndarray,
    metric: str = 'accuracy'
) -> Tuple[float, float]:
    """
    Find optimal distance threshold.

    Args:
        distances: Pairwise distances
        labels: True labels
        metric: 'accuracy', 'f1', or 'balanced'

    Returns:
        (optimal_threshold, metric_value)
    """
    thresholds = np.linspace(distances.min(), distances.max(), 100)
    best_threshold = 0
    best_score = 0

    for threshold in thresholds:
        predictions = (distances < threshold).astype(int)
        true_labels = 1 - labels  # Convert to match predictions

        if metric == 'accuracy':
            score = np.mean(predictions == true_labels)
        elif metric == 'f1':
            tp = np.sum((predictions == 1) & (true_labels == 1))
            fp = np.sum((predictions == 1) & (true_labels == 0))
            fn = np.sum((predictions == 0) & (true_labels == 1))

            precision = tp / (tp + fp + 1e-8)
            recall = tp / (tp + fn + 1e-8)
            score = 2 * (precision * recall) / (precision + recall + 1e-8)
        else:
            # Balanced accuracy
            tp = np.sum((predictions == 1) & (true_labels == 1))
            tn = np.sum((predictions == 0) & (true_labels == 0))
            fp = np.sum((predictions == 1) & (true_labels == 0))
            fn = np.sum((predictions == 0) & (true_labels == 1))

            sensitivity = tp / (tp + fn + 1e-8)
            specificity = tn / (tn + fp + 1e-8)
            score = (sensitivity + specificity) / 2

        if score > best_score:
            best_score = score
            best_threshold = threshold

    return best_threshold, best_score


def print_evaluation_report(
    distances: np.ndarray,
    labels: np.ndarray,
    threshold: float = None
):
    """
    Print comprehensive evaluation report.

    Args:
        distances: Pairwise distances
        labels: True labels
        threshold: Distance threshold (auto-calculated if None)
    """
    print("\n" + "=" * 60)
    print("EVALUATION REPORT")
    print("=" * 60)

    # Calculate ROC AUC
    roc_auc, _, _, _ = calculate_roc_auc(distances, labels)
    print(f"\nROC AUC Score: {roc_auc:.4f}")

    # Calculate Average Precision
    avg_precision, _, _, _ = calculate_precision_recall(distances, labels)
    print(f"Average Precision: {avg_precision:.4f}")

    # Find optimal threshold if not provided
    if threshold is None:
        threshold, accuracy = find_optimal_threshold(distances, labels, 'accuracy')
        print(f"\nOptimal Threshold: {threshold:.4f}")
        print(f"Accuracy at Optimal Threshold: {accuracy:.4f}")
    else:
        accuracy = calculate_accuracy_at_threshold(distances, labels, threshold)
        print(f"\nThreshold: {threshold:.4f}")
        print(f"Accuracy: {accuracy:.4f}")

    # Calculate confusion matrix
    predictions = (distances < threshold).astype(int)
    true_labels = 1 - labels

    tp = np.sum((predictions == 1) & (true_labels == 1))
    tn = np.sum((predictions == 0) & (true_labels == 0))
    fp = np.sum((predictions == 1) & (true_labels == 0))
    fn = np.sum((predictions == 0) & (true_labels == 1))

    print(f"\nConfusion Matrix:")
    print(f"  True Positives:  {tp}")
    print(f"  True Negatives:  {tn}")
    print(f"  False Positives: {fp}")
    print(f"  False Negatives: {fn}")

    precision = tp / (tp + fp + 1e-8)
    recall = tp / (tp + fn + 1e-8)
    f1 = 2 * (precision * recall) / (precision + recall + 1e-8)

    print(f"\nPrecision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")

    print("=" * 60 + "\n")
