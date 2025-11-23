"""
Training configuration for copyright detection models.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import yaml
from pathlib import Path


@dataclass
class ModelConfig:
    """Model architecture configuration"""
    model_type: str = 'siamese'  # 'siamese', 'triplet', or 'embedding'
    backbone: str = 'resnet50'  # 'resnet50', 'resnet101', 'resnet152'
    pretrained: bool = True
    embedding_dim: int = 128
    freeze_backbone: bool = False
    use_attention: bool = False


@dataclass
class DataConfig:
    """Data configuration"""
    data_file: str = 'data/annotations/pairs.json'
    image_dir: str = 'data/training_images'
    dataset_type: str = 'pair'  # 'pair', 'triplet', or 'online'
    batch_size: int = 32
    num_workers: int = 4
    train_split: float = 0.8
    augmentation_level: str = 'medium'  # 'light', 'medium', 'heavy', 'copyright_sim'
    image_size: int = 224


@dataclass
class TrainingConfig:
    """Training configuration"""
    num_epochs: int = 100
    learning_rate: float = 0.001
    weight_decay: float = 1e-4
    optimizer: str = 'adam'  # 'adam', 'sgd', 'adamw'
    scheduler: str = 'cosine'  # 'cosine', 'step', 'plateau', 'exponential'
    loss_type: str = 'contrastive'  # 'contrastive', 'triplet', 'online_triplet'
    loss_margin: float = 0.2
    early_stopping_patience: int = 15
    save_frequency: int = 5
    device: str = 'cuda'  # 'cuda' or 'cpu'
    seed: int = 42


@dataclass
class PathConfig:
    """Path configuration"""
    checkpoint_dir: str = 'ml_models/checkpoints'
    log_dir: str = 'ml_models/logs'
    output_dir: str = 'ml_models/outputs'


@dataclass
class ExperimentConfig:
    """Complete experiment configuration"""
    experiment_name: str = 'copyright_detection_baseline'
    model: ModelConfig = field(default_factory=ModelConfig)
    data: DataConfig = field(default_factory=DataConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    paths: PathConfig = field(default_factory=PathConfig)

    def save_to_yaml(self, filepath: str):
        """Save configuration to YAML file"""
        config_dict = {
            'experiment_name': self.experiment_name,
            'model': {
                'model_type': self.model.model_type,
                'backbone': self.model.backbone,
                'pretrained': self.model.pretrained,
                'embedding_dim': self.model.embedding_dim,
                'freeze_backbone': self.model.freeze_backbone,
                'use_attention': self.model.use_attention
            },
            'data': {
                'data_file': self.data.data_file,
                'image_dir': self.data.image_dir,
                'dataset_type': self.data.dataset_type,
                'batch_size': self.data.batch_size,
                'num_workers': self.data.num_workers,
                'train_split': self.data.train_split,
                'augmentation_level': self.data.augmentation_level,
                'image_size': self.data.image_size
            },
            'training': {
                'num_epochs': self.training.num_epochs,
                'learning_rate': self.training.learning_rate,
                'weight_decay': self.training.weight_decay,
                'optimizer': self.training.optimizer,
                'scheduler': self.training.scheduler,
                'loss_type': self.training.loss_type,
                'loss_margin': self.training.loss_margin,
                'early_stopping_patience': self.training.early_stopping_patience,
                'save_frequency': self.training.save_frequency,
                'device': self.training.device,
                'seed': self.training.seed
            },
            'paths': {
                'checkpoint_dir': self.paths.checkpoint_dir,
                'log_dir': self.paths.log_dir,
                'output_dir': self.paths.output_dir
            }
        }

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

        print(f"Configuration saved to {filepath}")

    @classmethod
    def load_from_yaml(cls, filepath: str) -> 'ExperimentConfig':
        """Load configuration from YAML file"""
        with open(filepath, 'r') as f:
            config_dict = yaml.safe_load(f)

        model_config = ModelConfig(**config_dict['model'])
        data_config = DataConfig(**config_dict['data'])
        training_config = TrainingConfig(**config_dict['training'])
        path_config = PathConfig(**config_dict['paths'])

        return cls(
            experiment_name=config_dict['experiment_name'],
            model=model_config,
            data=data_config,
            training=training_config,
            paths=path_config
        )


# Default configurations for different scenarios

def get_siamese_config() -> ExperimentConfig:
    """Get configuration for Siamese network training"""
    return ExperimentConfig(
        experiment_name='siamese_resnet50_contrastive',
        model=ModelConfig(
            model_type='siamese',
            backbone='resnet50',
            embedding_dim=128
        ),
        data=DataConfig(
            dataset_type='pair',
            batch_size=32,
            augmentation_level='medium'
        ),
        training=TrainingConfig(
            num_epochs=100,
            learning_rate=0.001,
            loss_type='contrastive',
            loss_margin=1.0
        )
    )


def get_triplet_config() -> ExperimentConfig:
    """Get configuration for Triplet network training"""
    return ExperimentConfig(
        experiment_name='triplet_resnet50_hard',
        model=ModelConfig(
            model_type='triplet',
            backbone='resnet50',
            embedding_dim=128
        ),
        data=DataConfig(
            dataset_type='triplet',
            batch_size=32,
            augmentation_level='medium'
        ),
        training=TrainingConfig(
            num_epochs=100,
            learning_rate=0.001,
            loss_type='triplet',
            loss_margin=0.2
        )
    )


def get_fine_tuning_config() -> ExperimentConfig:
    """Get configuration for fine-tuning with frozen backbone"""
    return ExperimentConfig(
        experiment_name='finetune_resnet50_frozen',
        model=ModelConfig(
            model_type='siamese',
            backbone='resnet50',
            embedding_dim=128,
            freeze_backbone=True  # Freeze backbone, train only embedding head
        ),
        data=DataConfig(
            dataset_type='pair',
            batch_size=64,  # Larger batch since less memory needed
            augmentation_level='heavy'
        ),
        training=TrainingConfig(
            num_epochs=50,
            learning_rate=0.01,  # Higher LR for head-only training
            loss_type='contrastive'
        )
    )


def get_full_training_config() -> ExperimentConfig:
    """Get configuration for full end-to-end training"""
    return ExperimentConfig(
        experiment_name='full_training_resnet50',
        model=ModelConfig(
            model_type='siamese',
            backbone='resnet50',
            embedding_dim=256,  # Larger embedding
            freeze_backbone=False,
            use_attention=True  # Use attention mechanism
        ),
        data=DataConfig(
            dataset_type='pair',
            batch_size=16,  # Smaller batch for full training
            augmentation_level='heavy'
        ),
        training=TrainingConfig(
            num_epochs=200,
            learning_rate=0.0001,  # Lower LR for fine-tuning
            optimizer='adamw',
            scheduler='cosine',
            loss_type='contrastive'
        )
    )
