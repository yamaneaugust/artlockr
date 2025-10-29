# ArtLockr - AI-Powered Copyright Detection for Artists

ArtLockr is an AI-powered copyright detection system that helps artists protect their intellectual property by identifying AI-generated artwork that may have been trained on or copied from their original works. Built with ResNet deep learning models, ArtLockr provides accurate similarity detection and comprehensive API gating capabilities.

## Features

- **Artwork Upload & Protection**: Artists can upload their original artwork for copyright monitoring
- **AI-Powered Detection**: Uses ResNet-based deep learning models for accurate similarity detection
- **Copyright Infringement Detection**: Compares original artwork against databases of AI-generated images
- **Similarity Scoring**: Provides detailed similarity percentages for potential matches
- **API Gating**: Block specific organizations from accessing or using protected artwork
- **Access Logging**: Track all access attempts to protected artwork
- **Comprehensive Reporting**: Detailed statistics and reports on copyright detections
- **RESTful API**: Easy-to-use API for integration with other tools

## Architecture

### Backend Stack
- **FastAPI**: Modern, high-performance web framework
- **PostgreSQL**: Robust database for storing artwork metadata and detection results
- **SQLAlchemy**: ORM for database operations
- **PyTorch + torchvision**: Deep learning framework for ResNet models

### ML Model
- **ResNet (50/101/152)**: Pre-trained convolutional neural networks for feature extraction
- **Feature Extraction**: 2048-dimensional feature vectors for each image
- **Cosine Similarity**: Efficient similarity comparison between artworks
- **Batch Processing**: Optimized for processing large image datasets

## Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- CUDA-capable GPU (optional, but recommended for faster processing)
- 10GB+ disk space for storing artwork and features

### Setup Instructions

1. **Clone the repository**
```bash
git clone <repository-url>
cd artlockr
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r backend/requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Set up PostgreSQL database**
```bash
# Create database
createdb artlockr_db

# Create user
psql -c "CREATE USER artlockr WITH PASSWORD 'artlockr';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE artlockr_db TO artlockr;"
```

6. **Initialize database**
```bash
python scripts/init_database.py
```

7. **Index AI-generated artwork** (optional, for testing)
```bash
# Add some AI-generated images to data/ai_generated/
python scripts/index_ai_artwork.py --device cuda
```

8. **Start the API server**
```bash
cd backend
python -m app.main

# Or with uvicorn directly:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Usage

### API Documentation

Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation.

### Basic Workflow

1. **Upload Original Artwork**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-artwork" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/artwork.jpg" \
  -F "title=My Artwork" \
  -F "description=Original artwork by me"
```

Response:
```json
{
  "id": 1,
  "title": "My Artwork",
  "file_path": "data/uploads/1/abc123_artwork.jpg",
  "feature_extracted": true,
  "message": "Artwork uploaded successfully"
}
```

2. **Detect Copyright Infringement**
```bash
curl -X POST "http://localhost:8000/api/v1/detect-copyright/1?threshold=0.85&top_k=10"
```

Response:
```json
{
  "detection_id": 1,
  "artwork_id": 1,
  "matches_found": 3,
  "threshold": 0.85,
  "matches": [
    {
      "image_path": "data/ai_generated/image1.jpg",
      "image_name": "image1.jpg",
      "similarity_score": 92.5,
      "is_infringement": true
    },
    {
      "image_path": "data/ai_generated/image2.jpg",
      "image_name": "image2.jpg",
      "similarity_score": 88.3,
      "is_infringement": true
    }
  ]
}
```

3. **Block Organizations**
```bash
curl -X POST "http://localhost:8000/api/v1/api-gate/block" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "BadAI Corp",
    "organization_domain": "badai.com",
    "reason": "Found copyright infringement in their training data"
  }'
```

4. **Get Statistics**
```bash
curl "http://localhost:8000/api/v1/statistics"
```

Response:
```json
{
  "total_artworks": 15,
  "total_detections": 8,
  "total_matches_found": 23,
  "blocked_organizations": 2
}
```

## Configuration

Edit `.env` file to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_NAME` | ResNet model variant | `resnet50` |
| `SIMILARITY_THRESHOLD` | Similarity threshold (0-1) | `0.85` |
| `DEVICE` | Compute device (cuda/cpu) | `cuda` |
| `MAX_UPLOAD_SIZE` | Max file upload size (bytes) | `10485760` |
| `ENABLE_API_GATING` | Enable/disable API gating | `True` |

## Project Structure

```
artlockr/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints.py       # API endpoint definitions
│   │   ├── core/
│   │   │   └── config.py          # Application configuration
│   │   ├── db/
│   │   │   └── session.py         # Database session management
│   │   ├── models/
│   │   │   └── database.py        # SQLAlchemy models
│   │   └── main.py                # FastAPI application
│   ├── requirements.txt           # Python dependencies
│   └── tests/                     # Unit tests
├── ml_models/
│   ├── inference/
│   │   └── copyright_detector.py  # ResNet-based detection model
│   └── training/                  # Model training scripts
├── data/
│   ├── uploads/                   # Original artwork uploads
│   ├── ai_generated/              # AI-generated images for comparison
│   └── features/                  # Extracted feature vectors
├── scripts/
│   ├── init_database.py           # Database initialization
│   └── index_ai_artwork.py        # Index AI-generated artwork
├── .env.example                   # Environment configuration template
└── README.md                      # This file
```

## How It Works

### 1. Feature Extraction
When an artist uploads their artwork, ArtLockr:
- Preprocesses the image (resize, normalize)
- Passes it through a pre-trained ResNet model
- Extracts a 2048-dimensional feature vector
- Stores the features for fast comparison

### 2. Copyright Detection
When detecting copyright infringement:
- Extracts features from the original artwork
- Compares against all AI-generated images in the database
- Uses cosine similarity to compute match scores
- Returns matches above the similarity threshold

### 3. API Gating
When an organization is blocked:
- Access attempts are logged with IP and user agent
- Requests matching blocked domains are rejected
- Artists maintain full control over their content

## Use Cases

### For Individual Artists
- Monitor if AI models have been trained on your artwork
- Discover unauthorized use in AI-generated content
- Build evidence for DMCA takedown requests
- Protect your portfolio from AI scraping

### For Art Platforms
- Integrate copyright detection into upload workflows
- Provide copyright protection as a service
- Build trust with artist communities
- Comply with copyright regulations

### For Researchers
- Study AI training data attribution
- Analyze style transfer and copying in generative models
- Build datasets of copyright infringement cases

## Performance

- **Feature Extraction**: ~50ms per image (GPU) / ~200ms (CPU)
- **Similarity Search**: ~0.1ms per comparison
- **Batch Processing**: ~30 images/second (GPU)
- **Database Queries**: <10ms for typical operations

## Limitations

- Detection accuracy depends on the similarity threshold
- May flag legitimate style similarities as infringement
- Requires a database of AI-generated images for comparison
- GPU recommended for large-scale deployments

## Future Enhancements

- [ ] Web-based user interface
- [ ] Real-time monitoring of art platforms
- [ ] Integration with web scrapers for AI art sites
- [ ] Advanced similarity metrics (SSIM, perceptual loss)
- [ ] Blockchain-based copyright timestamping
- [ ] Mobile app for artists
- [ ] Automated DMCA takedown generation
- [ ] Multi-artist collaboration features

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Specify your license here]

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

- PyTorch and torchvision teams for pre-trained ResNet models
- FastAPI community for the excellent web framework
- Artists fighting for copyright protection in the AI era

---

**Note**: This system is designed to help artists identify potential copyright infringement. Legal advice should be sought before taking action based on detection results.
