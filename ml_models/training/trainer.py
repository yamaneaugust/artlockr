"""
Training loop with validation, checkpointing, and early stopping
for copyright detection models.
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import Dict, Optional, Tuple, List
import time
from pathlib import Path
import json
from datetime import datetime
import numpy as np


class ModelTrainer:
    """
    Comprehensive trainer for Siamese and Triplet networks.
    Handles training, validation, checkpointing, and logging.
    """

    def __init__(
        self,
        model: nn.Module,
        loss_fn: nn.Module,
        optimizer: optim.Optimizer,
        device: torch.device,
        checkpoint_dir: str = 'checkpoints',
        log_dir: str = 'logs',
        model_type: str = 'siamese'
    ):
        """
        Args:
            model: Neural network model
            loss_fn: Loss function
            optimizer: Optimizer
            device: Training device (cuda/cpu)
            checkpoint_dir: Directory for model checkpoints
            log_dir: Directory for training logs
            model_type: 'siamese' or 'triplet'
        """
        self.model = model.to(device)
        self.loss_fn = loss_fn
        self.optimizer = optimizer
        self.device = device
        self.model_type = model_type

        # Create directories
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'learning_rate': [],
            'epoch_time': []
        }

        # Best model tracking
        self.best_val_loss = float('inf')
        self.best_epoch = 0

    def train_epoch(self, train_loader: DataLoader) -> float:
        """
        Train for one epoch.

        Args:
            train_loader: Training data loader

        Returns:
            Average training loss
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch_idx, batch_data in enumerate(train_loader):
            # Handle different data formats
            if self.model_type == 'siamese':
                img1, img2, labels = batch_data
                img1 = img1.to(self.device)
                img2 = img2.to(self.device)
                labels = labels.to(self.device)

                # Forward pass
                embedding1, embedding2 = self.model(img1, img2)

                # Calculate loss
                loss = self.loss_fn(embedding1, embedding2, labels)

            elif self.model_type == 'triplet':
                anchor, positive, negative = batch_data
                anchor = anchor.to(self.device)
                positive = positive.to(self.device)
                negative = negative.to(self.device)

                # Forward pass
                anchor_emb, positive_emb, negative_emb = self.model(
                    anchor, positive, negative
                )

                # Calculate loss
                loss = self.loss_fn(anchor_emb, positive_emb, negative_emb)

            else:
                raise ValueError(f"Unknown model type: {self.model_type}")

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

            # Print progress
            if (batch_idx + 1) % 10 == 0:
                print(f"  Batch [{batch_idx + 1}/{len(train_loader)}], "
                      f"Loss: {loss.item():.4f}")

        avg_loss = total_loss / num_batches
        return avg_loss

    def validate(self, val_loader: DataLoader) -> float:
        """
        Validate the model.

        Args:
            val_loader: Validation data loader

        Returns:
            Average validation loss
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch_data in val_loader:
                # Handle different data formats
                if self.model_type == 'siamese':
                    img1, img2, labels = batch_data
                    img1 = img1.to(self.device)
                    img2 = img2.to(self.device)
                    labels = labels.to(self.device)

                    embedding1, embedding2 = self.model(img1, img2)
                    loss = self.loss_fn(embedding1, embedding2, labels)

                elif self.model_type == 'triplet':
                    anchor, positive, negative = batch_data
                    anchor = anchor.to(self.device)
                    positive = positive.to(self.device)
                    negative = negative.to(self.device)

                    anchor_emb, positive_emb, negative_emb = self.model(
                        anchor, positive, negative
                    )
                    loss = self.loss_fn(anchor_emb, positive_emb, negative_emb)

                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches
        return avg_loss

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int,
        scheduler: Optional[optim.lr_scheduler._LRScheduler] = None,
        early_stopping_patience: int = 10,
        save_frequency: int = 5
    ) -> Dict:
        """
        Full training loop.

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            num_epochs: Number of training epochs
            scheduler: Learning rate scheduler
            early_stopping_patience: Patience for early stopping
            save_frequency: Save checkpoint every N epochs

        Returns:
            Training history
        """
        print(f"\n{'='*60}")
        print(f"Starting Training - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Model: {self.model.__class__.__name__}")
        print(f"Device: {self.device}")
        print(f"Epochs: {num_epochs}")
        print(f"{'='*60}\n")

        patience_counter = 0

        for epoch in range(1, num_epochs + 1):
            epoch_start_time = time.time()

            print(f"\nEpoch {epoch}/{num_epochs}")
            print("-" * 40)

            # Training
            train_loss = self.train_epoch(train_loader)

            # Validation
            val_loss = self.validate(val_loader)

            # Learning rate scheduling
            if scheduler is not None:
                if isinstance(scheduler, optim.lr_scheduler.ReduceLROnPlateau):
                    scheduler.step(val_loss)
                else:
                    scheduler.step()

            # Calculate epoch time
            epoch_time = time.time() - epoch_start_time

            # Get current learning rate
            current_lr = self.optimizer.param_groups[0]['lr']

            # Update history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['learning_rate'].append(current_lr)
            self.history['epoch_time'].append(epoch_time)

            # Print epoch summary
            print(f"\n  Train Loss: {train_loss:.4f}")
            print(f"  Val Loss:   {val_loss:.4f}")
            print(f"  LR:         {current_lr:.6f}")
            print(f"  Time:       {epoch_time:.2f}s")

            # Save checkpoint
            is_best = val_loss < self.best_val_loss

            if is_best:
                self.best_val_loss = val_loss
                self.best_epoch = epoch
                patience_counter = 0
                print(f"  ✓ New best model! (Val Loss: {val_loss:.4f})")
                self.save_checkpoint(epoch, is_best=True)
            else:
                patience_counter += 1

            # Periodic checkpoint
            if epoch % save_frequency == 0:
                self.save_checkpoint(epoch, is_best=False)

            # Early stopping check
            if patience_counter >= early_stopping_patience:
                print(f"\n{'='*60}")
                print(f"Early stopping triggered after {epoch} epochs")
                print(f"Best model was at epoch {self.best_epoch} "
                      f"with val loss {self.best_val_loss:.4f}")
                print(f"{'='*60}")
                break

        # Save final history
        self.save_history()

        print(f"\n{'='*60}")
        print(f"Training Complete!")
        print(f"Best Epoch: {self.best_epoch}")
        print(f"Best Val Loss: {self.best_val_loss:.4f}")
        print(f"{'='*60}\n")

        return self.history

    def save_checkpoint(self, epoch: int, is_best: bool = False):
        """
        Save model checkpoint.

        Args:
            epoch: Current epoch
            is_best: Whether this is the best model so far
        """
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'train_loss': self.history['train_loss'][-1],
            'val_loss': self.history['val_loss'][-1],
            'best_val_loss': self.best_val_loss,
            'history': self.history
        }

        # Save regular checkpoint
        checkpoint_path = self.checkpoint_dir / f'checkpoint_epoch_{epoch}.pt'
        torch.save(checkpoint, checkpoint_path)

        # Save best model
        if is_best:
            best_path = self.checkpoint_dir / 'best_model.pt'
            torch.save(checkpoint, best_path)
            print(f"  Saved best model to {best_path}")

    def load_checkpoint(self, checkpoint_path: str):
        """
        Load model checkpoint.

        Args:
            checkpoint_path: Path to checkpoint file
        """
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.best_val_loss = checkpoint['best_val_loss']
        self.history = checkpoint['history']

        print(f"Loaded checkpoint from {checkpoint_path}")
        print(f"Epoch: {checkpoint['epoch']}, "
              f"Val Loss: {checkpoint['val_loss']:.4f}")

    def save_history(self):
        """Save training history to JSON"""
        history_path = self.log_dir / 'training_history.json'

        with open(history_path, 'w') as f:
            json.dump(self.history, f, indent=2)

        print(f"\nSaved training history to {history_path}")


class EarlyStopping:
    """
    Early stopping utility to stop training when validation loss stops improving.
    """

    def __init__(
        self,
        patience: int = 10,
        min_delta: float = 0.0,
        mode: str = 'min'
    ):
        """
        Args:
            patience: Number of epochs to wait
            min_delta: Minimum change to qualify as improvement
            mode: 'min' or 'max'
        """
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.counter = 0
        self.best_score = None
        self.early_stop = False

    def __call__(self, val_metric: float) -> bool:
        """
        Check if training should stop.

        Args:
            val_metric: Validation metric value

        Returns:
            True if should stop, False otherwise
        """
        score = -val_metric if self.mode == 'min' else val_metric

        if self.best_score is None:
            self.best_score = score
        elif score < self.best_score + self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.counter = 0

        return self.early_stop


def create_optimizer(
    model: nn.Module,
    optimizer_name: str = 'adam',
    lr: float = 0.001,
    weight_decay: float = 1e-4,
    **kwargs
) -> optim.Optimizer:
    """
    Create optimizer.

    Args:
        model: Model to optimize
        optimizer_name: 'adam', 'sgd', or 'adamw'
        lr: Learning rate
        weight_decay: Weight decay
        **kwargs: Additional optimizer parameters

    Returns:
        Optimizer instance
    """
    if optimizer_name == 'adam':
        return optim.Adam(
            model.parameters(),
            lr=lr,
            weight_decay=weight_decay,
            **kwargs
        )
    elif optimizer_name == 'sgd':
        return optim.SGD(
            model.parameters(),
            lr=lr,
            momentum=kwargs.get('momentum', 0.9),
            weight_decay=weight_decay,
            nesterov=kwargs.get('nesterov', True)
        )
    elif optimizer_name == 'adamw':
        return optim.AdamW(
            model.parameters(),
            lr=lr,
            weight_decay=weight_decay,
            **kwargs
        )
    else:
        raise ValueError(f"Unknown optimizer: {optimizer_name}")


def create_scheduler(
    optimizer: optim.Optimizer,
    scheduler_name: str = 'cosine',
    num_epochs: int = 100,
    **kwargs
) -> optim.lr_scheduler._LRScheduler:
    """
    Create learning rate scheduler.

    Args:
        optimizer: Optimizer
        scheduler_name: 'cosine', 'step', 'plateau', or 'exponential'
        num_epochs: Total number of epochs
        **kwargs: Additional scheduler parameters

    Returns:
        Scheduler instance
    """
    if scheduler_name == 'cosine':
        return optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=num_epochs,
            **kwargs
        )
    elif scheduler_name == 'step':
        return optim.lr_scheduler.StepLR(
            optimizer,
            step_size=kwargs.get('step_size', 30),
            gamma=kwargs.get('gamma', 0.1)
        )
    elif scheduler_name == 'plateau':
        return optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode='min',
            factor=kwargs.get('factor', 0.1),
            patience=kwargs.get('patience', 10),
            verbose=True
        )
    elif scheduler_name == 'exponential':
        return optim.lr_scheduler.ExponentialLR(
            optimizer,
            gamma=kwargs.get('gamma', 0.95)
        )
    else:
        raise ValueError(f"Unknown scheduler: {scheduler_name}")
