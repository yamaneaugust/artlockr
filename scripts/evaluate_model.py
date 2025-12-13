"""
Evaluate trained copyright detection models.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import torch
import argparse
import json

from ml_models.training.models import create_model
from ml_models.training.datasets import get_dataloaders
from ml_models.training.metrics import (
    evaluate_model,
    calculate_roc_auc,
    calculate_precision_recall,
    print_evaluation_report,
    plot_roc_curve,
    plot_precision_recall_curve,
    find_optimal_threshold
)
from ml_models.training.config import ExperimentConfig


def evaluate(
    checkpoint_path: str,
    data_file: str,
    image_dir: str,
    model_type: str = 'siamese',
    backbone: str = 'resnet50',
    embedding_dim: int = 128,
    batch_size: int = 32,
    device: str = 'cuda',
    output_dir: str = 'ml_models/outputs'
):
    """
    Evaluate a trained model.

    Args:
        checkpoint_path: Path to model checkpoint
        data_file: Path to test data annotations
        image_dir: Path to image directory
        model_type: Model architecture type
        backbone: ResNet backbone
        embedding_dim: Embedding dimension
        batch_size: Batch size for evaluation
        device: Device to use
        output_dir: Directory for saving outputs
    """
    print(f"\n{'='*70}")
    print("MODEL EVALUATION")
    print(f"{'='*70}")

    # Set device
    device = torch.device(device if torch.cuda.is_available() else 'cpu')
    print(f"\nDevice: {device}")

    # Load model
    print(f"\nLoading model from {checkpoint_path}...")
    model = create_model(
        model_type=model_type,
        backbone=backbone,
        pretrained=False,  # Don't load pretrained weights
        embedding_dim=embedding_dim
    )

    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()

    print(f"Checkpoint epoch: {checkpoint['epoch']}")
    print(f"Checkpoint val loss: {checkpoint['val_loss']:.4f}")

    # Load test data
    print(f"\nLoading test data from {data_file}...")
    _, test_loader = get_dataloaders(
        data_file=data_file,
        image_dir=image_dir,
        batch_size=batch_size,
        num_workers=4,
        dataset_type='pair' if model_type == 'siamese' else 'triplet',
        train_split=0.0  # Use all data for testing
    )
    print(f"Test batches: {len(test_loader)}")

    # Evaluate
    print("\nEvaluating model...")
    distances, labels = evaluate_model(
        model=model,
        dataloader=test_loader,
        device=device,
        model_type=model_type
    )

    # Print comprehensive report
    print_evaluation_report(distances, labels)

    # Calculate and save metrics
    roc_auc, fpr, tpr, thresholds = calculate_roc_auc(distances, labels)
    avg_precision, precision, recall, _ = calculate_precision_recall(distances, labels)
    optimal_threshold, optimal_accuracy = find_optimal_threshold(distances, labels)

    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {
        'checkpoint_path': checkpoint_path,
        'roc_auc': float(roc_auc),
        'average_precision': float(avg_precision),
        'optimal_threshold': float(optimal_threshold),
        'optimal_accuracy': float(optimal_accuracy),
        'num_samples': len(distances)
    }

    results_file = output_path / 'evaluation_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_file}")

    # Plot ROC curve
    roc_plot_path = output_path / 'roc_curve.png'
    plot_roc_curve(fpr, tpr, roc_auc, save_path=str(roc_plot_path))

    # Plot PR curve
    pr_plot_path = output_path / 'pr_curve.png'
    plot_precision_recall_curve(
        precision, recall, avg_precision, save_path=str(pr_plot_path)
    )

    print(f"\n{'='*70}")
    print("EVALUATION COMPLETE!")
    print(f"{'='*70}\n")

    return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Evaluate trained copyright detection model'
    )

    parser.add_argument(
        '--checkpoint',
        type=str,
        required=True,
        help='Path to model checkpoint (.pt file)'
    )

    parser.add_argument(
        '--data-file',
        type=str,
        required=True,
        help='Path to test data annotations (JSON)'
    )

    parser.add_argument(
        '--image-dir',
        type=str,
        required=True,
        help='Path to image directory'
    )

    parser.add_argument(
        '--model-type',
        type=str,
        default='siamese',
        choices=['siamese', 'triplet', 'embedding'],
        help='Model architecture type'
    )

    parser.add_argument(
        '--backbone',
        type=str,
        default='resnet50',
        choices=['resnet50', 'resnet101', 'resnet152'],
        help='ResNet backbone'
    )

    parser.add_argument(
        '--embedding-dim',
        type=int,
        default=128,
        help='Embedding dimension'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size'
    )

    parser.add_argument(
        '--device',
        type=str,
        default='cuda',
        choices=['cuda', 'cpu'],
        help='Device to use'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='ml_models/outputs/evaluation',
        help='Output directory'
    )

    args = parser.parse_args()

    # Evaluate
    evaluate(
        checkpoint_path=args.checkpoint,
        data_file=args.data_file,
        image_dir=args.image_dir,
        model_type=args.model_type,
        backbone=args.backbone,
        embedding_dim=args.embedding_dim,
        batch_size=args.batch_size,
        device=args.device,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
