"""
Prepare training data annotations for copyright detection.
Creates sample annotation files for pair-based and triplet-based training.
"""
import json
import argparse
from pathlib import Path
import random
from typing import List, Dict


def create_pair_annotations(
    image_dir: str,
    output_file: str,
    similar_ratio: float = 0.5
):
    """
    Create pair annotations from image directory.

    Expected directory structure:
    image_dir/
        original/
            artwork_1.jpg
            artwork_2.jpg
            ...
        ai_generated/
            copy_1.jpg
            copy_2.jpg
            ...

    Args:
        image_dir: Root image directory
        output_file: Output JSON file path
        similar_ratio: Ratio of similar pairs to total pairs
    """
    image_path = Path(image_dir)
    original_dir = image_path / 'original'
    ai_dir = image_path / 'ai_generated'

    if not original_dir.exists() or not ai_dir.exists():
        print(f"Error: Expected 'original' and 'ai_generated' subdirectories in {image_dir}")
        print("\nDirectory structure should be:")
        print("image_dir/")
        print("  original/")
        print("    artwork_1.jpg")
        print("    artwork_2.jpg")
        print("  ai_generated/")
        print("    copy_1.jpg")
        print("    copy_2.jpg")
        return

    # Get all images
    original_images = list(original_dir.glob('*.jpg')) + list(original_dir.glob('*.png'))
    ai_images = list(ai_dir.glob('*.jpg')) + list(ai_dir.glob('*.png'))

    if len(original_images) == 0 or len(ai_images) == 0:
        print(f"Error: No images found in {original_dir} or {ai_dir}")
        return

    print(f"Found {len(original_images)} original images")
    print(f"Found {len(ai_images)} AI-generated images")

    pairs = []

    # Create similar pairs (original vs AI-generated)
    num_similar = int(len(original_images) * similar_ratio)
    for i in range(num_similar):
        original = random.choice(original_images)
        ai_copy = random.choice(ai_images)

        pairs.append({
            "image1": f"original/{original.name}",
            "image2": f"ai_generated/{ai_copy.name}",
            "label": 1,  # Similar
            "similarity_score": random.uniform(0.75, 0.95)
        })

    # Create dissimilar pairs (original vs different original)
    num_dissimilar = len(original_images) - num_similar
    for i in range(num_dissimilar):
        img1 = random.choice(original_images)
        img2 = random.choice(original_images)

        while img1 == img2:
            img2 = random.choice(original_images)

        pairs.append({
            "image1": f"original/{img1.name}",
            "image2": f"original/{img2.name}",
            "label": 0,  # Dissimilar
            "similarity_score": random.uniform(0.1, 0.4)
        })

    # Shuffle pairs
    random.shuffle(pairs)

    # Create annotations
    annotations = {
        "dataset": "copyright_detection_pairs",
        "num_pairs": len(pairs),
        "num_similar": num_similar,
        "num_dissimilar": num_dissimilar,
        "pairs": pairs
    }

    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(annotations, f, indent=2)

    print(f"\nCreated {len(pairs)} pairs ({num_similar} similar, {num_dissimilar} dissimilar)")
    print(f"Saved to {output_file}")


def create_triplet_annotations(
    image_dir: str,
    output_file: str,
    num_triplets: int = 1000
):
    """
    Create triplet annotations from image directory.

    Args:
        image_dir: Root image directory
        output_file: Output JSON file path
        num_triplets: Number of triplets to generate
    """
    image_path = Path(image_dir)
    original_dir = image_path / 'original'
    ai_dir = image_path / 'ai_generated'

    if not original_dir.exists() or not ai_dir.exists():
        print(f"Error: Expected 'original' and 'ai_generated' subdirectories in {image_dir}")
        return

    # Get all images
    original_images = list(original_dir.glob('*.jpg')) + list(original_dir.glob('*.png'))
    ai_images = list(ai_dir.glob('*.jpg')) + list(ai_dir.glob('*.png'))

    if len(original_images) < 2 or len(ai_images) == 0:
        print(f"Error: Need at least 2 original images and 1 AI image")
        return

    print(f"Found {len(original_images)} original images")
    print(f"Found {len(ai_images)} AI-generated images")

    triplets = []

    for i in range(num_triplets):
        # Anchor: random original image
        anchor = random.choice(original_images)

        # Positive: random AI-generated image (similar to anchor)
        positive = random.choice(ai_images)

        # Negative: different original image
        negative = random.choice(original_images)
        while negative == anchor:
            negative = random.choice(original_images)

        triplets.append({
            "anchor": f"original/{anchor.name}",
            "positive": f"ai_generated/{positive.name}",
            "negative": f"original/{negative.name}"
        })

    # Create annotations
    annotations = {
        "dataset": "copyright_detection_triplets",
        "num_triplets": len(triplets),
        "triplets": triplets
    }

    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(annotations, f, indent=2)

    print(f"\nCreated {len(triplets)} triplets")
    print(f"Saved to {output_file}")


def create_sample_data_structure(base_dir: str):
    """
    Create sample directory structure and README.

    Args:
        base_dir: Base directory to create structure
    """
    base_path = Path(base_dir)

    # Create directories
    (base_path / 'original').mkdir(parents=True, exist_ok=True)
    (base_path / 'ai_generated').mkdir(parents=True, exist_ok=True)

    # Create README
    readme_content = """# Training Data Directory

Place your training images in the following structure:

## Directory Structure

```
data/training_images/
├── original/           # Original artwork images
│   ├── artwork_1.jpg
│   ├── artwork_2.jpg
│   └── ...
└── ai_generated/       # AI-generated or copied artwork
    ├── copy_1.jpg
    ├── copy_2.jpg
    └── ...
```

## Guidelines

### Original Images
- Place authentic, original artwork in the `original/` directory
- Supported formats: JPG, PNG
- Minimum resolution: 224x224 pixels
- Recommended: High-quality images for best results

### AI-Generated Images
- Place AI-generated or potentially copied artwork in `ai_generated/`
- These should be images that may contain elements similar to originals
- Used to train the model to detect copyright infringement patterns

## Data Preparation

After organizing your images, run:

```bash
# For pair-based training (Siamese network)
python scripts/prepare_training_data.py \\
    --mode pair \\
    --image-dir data/training_images \\
    --output data/annotations/pairs.json

# For triplet-based training
python scripts/prepare_training_data.py \\
    --mode triplet \\
    --image-dir data/training_images \\
    --output data/annotations/triplets.json
```

## Tips

1. **Balance**: Maintain a good balance between similar and dissimilar pairs
2. **Diversity**: Include various art styles and AI generation patterns
3. **Quality**: Use high-quality images for better feature extraction
4. **Quantity**: More data = better model performance (aim for 1000+ pairs)
"""

    readme_path = base_path / 'README.md'
    with open(readme_path, 'w') as f:
        f.write(readme_content)

    print(f"\nCreated directory structure at {base_dir}")
    print(f"Created README at {readme_path}")
    print("\nNext steps:")
    print(f"1. Add original artwork images to {base_path / 'original'}")
    print(f"2. Add AI-generated images to {base_path / 'ai_generated'}")
    print("3. Run this script with --mode pair or --mode triplet to create annotations")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Prepare training data for copyright detection'
    )

    parser.add_argument(
        '--mode',
        type=str,
        required=True,
        choices=['pair', 'triplet', 'setup'],
        help='Preparation mode'
    )

    parser.add_argument(
        '--image-dir',
        type=str,
        default='data/training_images',
        help='Image directory'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output annotation file'
    )

    parser.add_argument(
        '--similar-ratio',
        type=float,
        default=0.5,
        help='Ratio of similar pairs (for pair mode)'
    )

    parser.add_argument(
        '--num-triplets',
        type=int,
        default=1000,
        help='Number of triplets to generate (for triplet mode)'
    )

    args = parser.parse_args()

    if args.mode == 'setup':
        create_sample_data_structure(args.image_dir)

    elif args.mode == 'pair':
        output_file = args.output or 'data/annotations/pairs.json'
        create_pair_annotations(
            image_dir=args.image_dir,
            output_file=output_file,
            similar_ratio=args.similar_ratio
        )

    elif args.mode == 'triplet':
        output_file = args.output or 'data/annotations/triplets.json'
        create_triplet_annotations(
            image_dir=args.image_dir,
            output_file=output_file,
            num_triplets=args.num_triplets
        )


if __name__ == "__main__":
    main()
