# Quick Start Guide

Get ArtLockr up and running in 5 minutes!

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ (or use Docker)

## Option 1: Quick Start with Docker (Recommended)

1. **Clone and start services**
```bash
git clone <repository-url>
cd artlockr
docker-compose up -d
```

2. **Initialize database**
```bash
docker-compose exec api python scripts/init_database.py
```

3. **Access the API**
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs

That's it! Skip to [Usage Examples](#usage-examples)

## Option 2: Local Development Setup

1. **Install dependencies**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

2. **Set up database**
```bash
# Create PostgreSQL database
createdb artlockr_db

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings
```

3. **Initialize database**
```bash
python scripts/init_database.py
```

4. **Start the server**
```bash
cd backend
python -m app.main
```

## Usage Examples

### 1. Upload Your Artwork

```bash
curl -X POST "http://localhost:8000/api/v1/upload-artwork" \
  -F "file=@/path/to/your/artwork.jpg" \
  -F "title=My Artwork"
```

### 2. Detect Copyright Infringement

```bash
# Replace {artwork_id} with the ID from upload response
curl -X POST "http://localhost:8000/api/v1/detect-copyright/{artwork_id}?threshold=0.85"
```

### 3. Block Organizations

```bash
curl -X POST "http://localhost:8000/api/v1/api-gate/block" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "UnauthorizedAI",
    "organization_domain": "unauthorizedai.com",
    "reason": "Used my art without permission"
  }'
```

### 4. View Interactive API Docs

Open your browser: http://localhost:8000/docs

## Testing with Sample Data

1. **Add AI-generated images** (for testing detection)
```bash
# Copy some AI-generated images to:
mkdir -p data/ai_generated
# Add images to this directory
```

2. **Index the images**
```bash
python scripts/index_ai_artwork.py --device cpu
```

3. **Run detection** as shown above

## Example Python Script

```python
import requests

# Upload artwork
files = {'file': open('artwork.jpg', 'rb')}
data = {'title': 'My Art'}
response = requests.post('http://localhost:8000/api/v1/upload-artwork',
                        files=files, data=data)
artwork_id = response.json()['id']

# Detect copyright
response = requests.post(f'http://localhost:8000/api/v1/detect-copyright/{artwork_id}')
matches = response.json()['matches']

print(f"Found {len(matches)} potential infringements")
for match in matches:
    print(f"- {match['image_name']}: {match['similarity_score']}% similar")
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the interactive API docs at `/docs`
- Run the example script: `python scripts/example_usage.py`
- Configure your `.env` file for production use

## Common Issues

**Database connection error:**
- Make sure PostgreSQL is running
- Check DATABASE_URL in .env file

**CUDA not available:**
- Set `DEVICE=cpu` in .env file
- Or install CUDA toolkit for GPU acceleration

**Import errors:**
- Make sure you're in the virtual environment
- Run `pip install -r backend/requirements.txt`

## Getting Help

- Check the [README.md](README.md) for detailed docs
- Open an issue on GitHub
- Review the example scripts in `scripts/`

---

Happy copyright protecting! 🎨🔒
