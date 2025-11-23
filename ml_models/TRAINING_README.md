# Copyright Detection Model Training Guide

This guide covers training ResNet-based models for artwork copyright detection using Siamese and Triplet networks.

## 📋 Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Data Preparation](#data-preparation)
- [Training](#training)
- [Evaluation](#evaluation)
- [Model Architectures](#model-architectures)
- [Configuration](#configuration)
- [Advanced Usage](#advanced-usage)

## 🎯 Overview

The training pipeline supports:

- **Siamese Networks**: Learn similarity between image pairs
- **Triplet Networks**: Learn relative distances (anchor-positive-negative)
- **Multiple Loss Functions**: Contrastive, Triplet, Online Triplet, Angular, ArcFace
- **Data Augmentation**: Standard and copyright-specific augmentations
- **Fine-tuning Strategies**: Frozen backbone or end-to-end training

## 📦 Installation

1. **Install training dependencies:**
```bash
pip install -r ml_models/requirements-training.txt
```

2. **Verify PyTorch GPU support** (optional but recommended):
```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## 📊 Data Preparation

### Directory Structure

Organize your data as follows:

```
data/
├── training_images/
│   ├── original/          # Original artwork
│   │   ├── art_1.jpg
│   │   ├── art_2.jpg
│   │   └── ...
│   └── ai_generated/      # AI-generated/copied artwork
│       ├── copy_1.jpg
│       ├── copy_2.jpg
│       └── ...
└── annotations/
    ├── pairs.json         # For Siamese training
    └── triplets.json      # For Triplet training
```

### Step 1: Setup Data Directory

```bash
python scripts/prepare_training_data.py --mode setup --image-dir data/training_images
```

### Step 2: Add Your Images

1. Add original artwork to `data/training_images/original/`
2. Add AI-generated images to `data/training_images/ai_generated/`

### Step 3: Generate Annotations

For **Siamese Network** (pair-based):
```bash
python scripts/prepare_training_data.py \
    --mode pair \
    --image-dir data/training_images \
    --output data/annotations/pairs.json \
    --similar-ratio 0.5
```

For **Triplet Network**:
```bash
python scripts/prepare_training_data.py \
    --mode triplet \
    --image-dir data/training_images \
    --output data/annotations/triplets.json \
    --num-triplets 1000
```

### Annotation Format

**Pairs (for Siamese):**
```json
{
  "pairs": [
    {
      "image1": "original/art_1.jpg",
      "image2": "ai_generated/copy_1.jpg",
      "label": 1,
      "similarity_score": 0.92
    },
    {
      "image1": "original/art_1.jpg",
      "image2": "original/art_2.jpg",
      "label": 0,
      "similarity_score": 0.23
    }
  ]
}
```

**Triplets:**
```json
{
  "triplets": [
    {
      "anchor": "original/art_1.jpg",
      "positive": "ai_generated/copy_1.jpg",
      "negative": "original/art_2.jpg"
    }
  ]
}
```

## 🚀 Training

### Quick Start with Presets

**1. Siamese Network (recommended for beginners):**
```bash
python scripts/train_model.py \
    --preset siamese \
    --data-file data/annotations/pairs.json \
    --image-dir data/training_images \
    --epochs 50 \
    --batch-size 32
```

**2. Triplet Network:**
```bash
python scripts/train_model.py \
    --preset triplet \
    --data-file data/annotations/triplets.json \
    --image-dir data/training_images \
    --epochs 50 \
    --batch-size 32
```

**3. Fine-tuning (faster training, frozen backbone):**
```bash
python scripts/train_model.py \
    --preset finetune \
    --data-file data/annotations/pairs.json \
    --image-dir data/training_images \
    --epochs 30 \
    --batch-size 64
```

**4. Full Training (best accuracy, slower):**
```bash
python scripts/train_model.py \
    --preset full \
    --data-file data/annotations/pairs.json \
    --image-dir data/training_images \
    --epochs 100 \
    --batch-size 16
```

### Command Line Arguments

```
--config          Path to custom config YAML file
--preset          Preset configuration (siamese/triplet/finetune/full)
--data-file       Path to annotation JSON
--image-dir       Path to image directory
--epochs          Number of training epochs
--batch-size      Batch size
--lr              Learning rate
--device          Device (cuda/cpu)
```

### Training Output

Training produces:
- **Checkpoints**: `ml_models/checkpoints/`
  - `best_model.pt` - Best model based on validation loss
  - `checkpoint_epoch_*.pt` - Periodic checkpoints
- **Logs**: `ml_models/logs/`
  - `training_history.json` - Full training metrics
- **Outputs**: `ml_models/outputs/`
  - Training curve plots
  - ROC curves
  - Configuration files

### Monitoring Training

Watch training progress:
```bash
# View training logs
tail -f ml_models/logs/training_history.json

# Monitor with TensorBoard (if installed)
tensorboard --logdir ml_models/logs
```

## 📈 Evaluation

Evaluate a trained model:

```bash
python scripts/evaluate_model.py \
    --checkpoint ml_models/checkpoints/best_model.pt \
    --data-file data/annotations/test_pairs.json \
    --image-dir data/training_images \
    --model-type siamese \
    --backbone resnet50 \
    --embedding-dim 128 \
    --output-dir ml_models/outputs/evaluation
```

Evaluation outputs:
- **Metrics**: ROC AUC, Average Precision, Accuracy, F1 Score
- **Plots**: ROC curve, Precision-Recall curve
- **Results JSON**: Detailed evaluation results

## 🏗️ Model Architectures

### Siamese Network

Uses shared weights to process image pairs:

```
Input Pair (img1, img2)
    ↓
ResNet Backbone (shared weights)
    ↓
Feature Vectors (2048-dim)
    ↓
Projection Head (2048 → 512 → embedding_dim)
    ↓
L2 Normalization
    ↓
Embeddings (embedding_dim)
    ↓
Contrastive Loss
```

**Use Cases:**
- Binary similarity detection (similar/dissimilar)
- When you have labeled pairs
- Faster training than triplet

### Triplet Network

Learns relative distances with anchor-positive-negative triplets:

```
Triplet (anchor, positive, negative)
    ↓
ResNet Backbone (shared weights)
    ↓
Projection Head
    ↓
Embeddings (a, p, n)
    ↓
Triplet Loss: max(d(a,p) - d(a,n) + margin, 0)
```

**Use Cases:**
- Learning fine-grained similarities
- Ranking-based retrieval
- Better embedding quality (more training data needed)

## ⚙️ Configuration

### Creating Custom Configurations

Create a YAML config file:

```yaml
experiment_name: my_custom_training

model:
  model_type: siamese
  backbone: resnet50
  pretrained: true
  embedding_dim: 256
  freeze_backbone: false
  use_attention: true

data:
  data_file: data/annotations/pairs.json
  image_dir: data/training_images
  dataset_type: pair
  batch_size: 32
  num_workers: 4
  train_split: 0.8
  augmentation_level: heavy
  image_size: 224

training:
  num_epochs: 100
  learning_rate: 0.0001
  weight_decay: 0.0001
  optimizer: adamw
  scheduler: cosine
  loss_type: contrastive
  loss_margin: 1.0
  early_stopping_patience: 20
  save_frequency: 5
  device: cuda
  seed: 42

paths:
  checkpoint_dir: ml_models/checkpoints
  log_dir: ml_models/logs
  output_dir: ml_models/outputs
```

Use custom config:
```bash
python scripts/train_model.py --config my_config.yaml
```

### Loss Functions

**Contrastive Loss** (Siamese):
- Pulls similar pairs closer
- Pushes dissimilar pairs apart
- `loss_margin`: Minimum distance for dissimilar pairs (default: 1.0)

**Triplet Loss**:
- Ensures positive closer than negative
- `loss_margin`: Minimum margin between positive and negative (default: 0.2)

**Online Triplet Loss**:
- Mines hard triplets from batches
- More efficient for large datasets

### Optimizers

- **Adam**: Default, works well for most cases
- **AdamW**: Better weight decay handling
- **SGD**: With momentum and Nesterov, for careful tuning

### Schedulers

- **Cosine**: Smooth decay to near-zero
- **Step**: Decay at fixed intervals
- **Plateau**: Reduce on validation plateau
- **Exponential**: Exponential decay

## 🎓 Advanced Usage

### 1. Two-Stage Training

**Stage 1: Freeze backbone**
```bash
python scripts/train_model.py \
    --preset finetune \
    --epochs 30 \
    --batch-size 64 \
    --lr 0.01
```

**Stage 2: Fine-tune end-to-end**
```bash
python scripts/train_model.py \
    --preset full \
    --epochs 50 \
    --batch-size 16 \
    --lr 0.0001
```

### 2. Learning Rate Finding

```python
# Add to your custom training script
from ml_models.training.trainer import ModelTrainer

trainer = ModelTrainer(...)
lr_finder = trainer.find_learning_rate(
    train_loader=train_loader,
    start_lr=1e-7,
    end_lr=10,
    num_iter=100
)
```

### 3. Custom Augmentations

```python
from ml_models.training.augmentation import CopyrightSimulationAugmentation
from torchvision import transforms

custom_transform = transforms.Compose([
    CopyrightSimulationAugmentation(p=0.7),
    transforms.Resize(256),
    transforms.RandomCrop(224),
    # Add more transformations...
])
```

### 4. Using Trained Model for Inference

```python
import torch
from ml_models.training.models import create_model

# Load model
model = create_model(
    model_type='siamese',
    backbone='resnet50',
    embedding_dim=128
)

checkpoint = torch.load('ml_models/checkpoints/best_model.pt')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Get embeddings
with torch.no_grad():
    embedding = model.forward_one(image_tensor)
```

## 📊 Performance Tips

1. **Start with frozen backbone** (faster, good baseline)
2. **Use larger batch sizes** when possible (better gradient estimates)
3. **Heavy augmentation** helps generalization
4. **Monitor train/val gap** for overfitting
5. **Try different loss margins** for your specific data
6. **Use GPU** for 5-10x speedup

## 🐛 Troubleshooting

**Out of Memory:**
- Reduce batch size
- Use gradient accumulation
- Freeze backbone
- Use mixed precision training

**Poor Validation Performance:**
- Increase augmentation
- Add more training data
- Reduce learning rate
- Check data quality

**Training Not Converging:**
- Adjust learning rate
- Try different optimizer
- Check loss function margin
- Verify data labels

## 📚 Example Workflows

### Complete Training Pipeline

```bash
# 1. Setup data structure
python scripts/prepare_training_data.py --mode setup

# 2. Add your images to data/training_images/

# 3. Create annotations
python scripts/prepare_training_data.py --mode pair \
    --image-dir data/training_images \
    --output data/annotations/pairs.json

# 4. Train model
python scripts/train_model.py \
    --preset siamese \
    --data-file data/annotations/pairs.json \
    --image-dir data/training_images \
    --epochs 50 \
    --device cuda

# 5. Evaluate
python scripts/evaluate_model.py \
    --checkpoint ml_models/checkpoints/best_model.pt \
    --data-file data/annotations/test_pairs.json \
    --image-dir data/training_images

# 6. Use in production (integrate with backend API)
cp ml_models/checkpoints/best_model.pt backend/models/
```

## 📖 Further Reading

- [ResNet Paper](https://arxiv.org/abs/1512.03385)
- [Siamese Networks](https://www.cs.cmu.edu/~rsalakhu/papers/oneshot1.pdf)
- [Triplet Loss](https://arxiv.org/abs/1503.03832)
- [Contrastive Learning](https://arxiv.org/abs/2002.05709)

---

For questions or issues, please check the main README or open an issue on GitHub.
