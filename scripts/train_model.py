"""
Main training script for copyright detection models.
Supports Siamese and Triplet networks with configurable training.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import torch
import random
import numpy as np
import argparse

from ml_models.training.config import (
    ExperimentConfig,
    get_siamese_config,
    get_triplet_config,
    get_fine_tuning_config,
    get_full_training_config
)
from ml_models.training.models import create_model
from ml_models.training.losses import get_loss_function
from ml_models.training.datasets import get_dataloaders
from ml_models.training.trainer import ModelTrainer, create_optimizer, create_scheduler
from ml_models.training.metrics import (
    evaluate_model,
    calculate_roc_auc,
    print_evaluation_report,
    plot_training_history,
    plot_roc_curve
)


def set_seed(seed: int):
    """Set random seed for reproducibility"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def train(config: ExperimentConfig):
    """
    Main training function.

    Args:
        config: Experiment configuration
    """
    print(f"\n{'='*70}")
    print(f"TRAINING CONFIGURATION: {config.experiment_name}")
    print(f"{'='*70}")

    # Set seed for reproducibility
    set_seed(config.training.seed)
    print(f"\nRandom seed set to: {config.training.seed}")

    # Set device
    device = torch.device(
        config.training.device if torch.cuda.is_available() else 'cpu'
    )
    print(f"Using device: {device}")

    # Create dataloaders
    print("\nLoading data...")
    try:
        train_loader, val_loader = get_dataloaders(
            data_file=config.data.data_file,
            image_dir=config.data.image_dir,
            batch_size=config.data.batch_size,
            num_workers=config.data.num_workers,
            dataset_type=config.data.dataset_type,
            train_split=config.data.train_split
        )
        print(f"Train batches: {len(train_loader)}")
        print(f"Val batches: {len(val_loader)}")
    except Exception as e:
        print(f"\nError loading data: {e}")
        print("\nPlease ensure:")
        print(f"1. Data file exists: {config.data.data_file}")
        print(f"2. Image directory exists: {config.data.image_dir}")
        print("3. Data file format matches the expected structure")
        return

    # Create model
    print(f"\nCreating {config.model.model_type} model...")
    model = create_model(
        model_type=config.model.model_type,
        backbone=config.model.backbone,
        pretrained=config.model.pretrained,
        embedding_dim=config.model.embedding_dim,
        freeze_backbone=config.model.freeze_backbone,
        use_attention=config.model.use_attention
    )
    print(f"Model: {config.model.backbone} with embedding dim {config.model.embedding_dim}")

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")

    # Create loss function
    print(f"\nLoss function: {config.training.loss_type}")
    loss_fn = get_loss_function(
        loss_type=config.training.loss_type,
        margin=config.training.loss_margin
    )

    # Create optimizer
    print(f"Optimizer: {config.training.optimizer}")
    optimizer = create_optimizer(
        model=model,
        optimizer_name=config.training.optimizer,
        lr=config.training.learning_rate,
        weight_decay=config.training.weight_decay
    )

    # Create scheduler
    print(f"Scheduler: {config.training.scheduler}")
    scheduler = create_scheduler(
        optimizer=optimizer,
        scheduler_name=config.training.scheduler,
        num_epochs=config.training.num_epochs
    )

    # Create trainer
    trainer = ModelTrainer(
        model=model,
        loss_fn=loss_fn,
        optimizer=optimizer,
        device=device,
        checkpoint_dir=config.paths.checkpoint_dir,
        log_dir=config.paths.log_dir,
        model_type=config.model.model_type
    )

    # Save configuration
    config_path = Path(config.paths.output_dir) / f"{config.experiment_name}_config.yaml"
    config.save_to_yaml(str(config_path))

    # Train
    print("\nStarting training...")
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=config.training.num_epochs,
        scheduler=scheduler,
        early_stopping_patience=config.training.early_stopping_patience,
        save_frequency=config.training.save_frequency
    )

    # Plot training history
    print("\nGenerating training plots...")
    plot_path = Path(config.paths.output_dir) / f"{config.experiment_name}_history.png"
    plot_training_history(history, save_path=str(plot_path))

    # Evaluate on validation set
    print("\nEvaluating on validation set...")
    distances, labels = evaluate_model(
        model=model,
        dataloader=val_loader,
        device=device,
        model_type=config.model.model_type
    )

    # Print evaluation report
    print_evaluation_report(distances, labels)

    # Plot ROC curve
    roc_auc, fpr, tpr, _ = calculate_roc_auc(distances, labels)
    roc_path = Path(config.paths.output_dir) / f"{config.experiment_name}_roc.png"
    plot_roc_curve(fpr, tpr, roc_auc, save_path=str(roc_path))

    print(f"\n{'='*70}")
    print("TRAINING COMPLETE!")
    print(f"{'='*70}")
    print(f"Best model saved to: {config.paths.checkpoint_dir}/best_model.pt")
    print(f"Logs saved to: {config.paths.log_dir}")
    print(f"Outputs saved to: {config.paths.output_dir}")
    print(f"{'='*70}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Train copyright detection models'
    )

    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to config YAML file'
    )

    parser.add_argument(
        '--preset',
        type=str,
        default='siamese',
        choices=['siamese', 'triplet', 'finetune', 'full'],
        help='Use preset configuration'
    )

    parser.add_argument(
        '--data-file',
        type=str,
        default=None,
        help='Override data file path'
    )

    parser.add_argument(
        '--image-dir',
        type=str,
        default=None,
        help='Override image directory path'
    )

    parser.add_argument(
        '--epochs',
        type=int,
        default=None,
        help='Override number of epochs'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=None,
        help='Override batch size'
    )

    parser.add_argument(
        '--lr',
        type=float,
        default=None,
        help='Override learning rate'
    )

    parser.add_argument(
        '--device',
        type=str,
        default=None,
        choices=['cuda', 'cpu'],
        help='Override device'
    )

    args = parser.parse_args()

    # Load or create configuration
    if args.config:
        print(f"Loading configuration from {args.config}")
        config = ExperimentConfig.load_from_yaml(args.config)
    else:
        print(f"Using preset configuration: {args.preset}")
        if args.preset == 'siamese':
            config = get_siamese_config()
        elif args.preset == 'triplet':
            config = get_triplet_config()
        elif args.preset == 'finetune':
            config = get_fine_tuning_config()
        elif args.preset == 'full':
            config = get_full_training_config()

    # Override with command line arguments
    if args.data_file:
        config.data.data_file = args.data_file
    if args.image_dir:
        config.data.image_dir = args.image_dir
    if args.epochs:
        config.training.num_epochs = args.epochs
    if args.batch_size:
        config.data.batch_size = args.batch_size
    if args.lr:
        config.training.learning_rate = args.lr
    if args.device:
        config.training.device = args.device

    # Train model
    train(config)


if __name__ == "__main__":
    main()
