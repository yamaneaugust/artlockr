# ArtLock

**The marketplace where artists legally sell creative works to AI companies.**

ArtLock connects creators with AI companies through a transparent, fair marketplace. Artists upload their work, set their terms, and get paid instantly. Companies get verified, licensed datasets with full legal compliance.

---

## Features

### For Artists
- **Upload creative work** – Images, audio, video, text, datasets
- **Set your license** – CC0, CC-BY, non-exclusive, exclusive, or custom
- **Get paid instantly** – 90% of every sale via Stripe Connect
- **Track earnings** – Dashboard showing sales, revenue, and active listings

### For AI Companies
- **Browse licensed datasets** – Filter by type, license, and price
- **Instant access** – Purchase via Stripe Checkout, download immediately
- **License keys** – Every purchase includes a verified license key
- **Compliance ready** – Full legal paper trail for every dataset

### Public Datasets
- **Common Crawl** – Search for freely-licensed creative works
- **Wikimedia Commons** – Browse CC0/CC-BY images
- **Freesound** – Discover CC-licensed audio

---

## Tech Stack

**Backend**
- FastAPI + SQLAlchemy + PostgreSQL
- Stripe Connect (artist payouts) + Stripe Checkout (purchases)
- Alembic migrations
- Common Crawl CDX Index API
- FAISS vector search (optional, for similarity detection)

**Frontend**
- React 18 + TypeScript + Vite
- Tailwind CSS
- Zustand (state)
- React Router + React Hot Toast

**DevOps**
- Docker + Docker Compose
- GitHub Actions CI/CD
- Nginx reverse proxy

---

## Quick Start

### Option 1: Docker (recommended)

```bash
# Set up environment
cp .env.example .env
# Edit .env and add your Stripe keys

# Start all services
docker-compose up -d

# Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Option 2: Local development

```bash
# Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Set up database
cd ../backend
alembic upgrade head

# Start backend
uvicorn app.main:app --reload

# Start frontend (new terminal)
cd ../frontend
npm run dev
```

### Option 3: Demo mode (no ML dependencies)

```bash
./demo.sh
```

---

## Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=postgresql://artlock:password@localhost:5432/artlock_db

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Frontend
FRONTEND_URL=http://localhost:3000

# Optional: Public dataset APIs
FREESOUND_API_KEY=your_freesound_api_key
```

---

## Database Schema

- **users** – Artist/company accounts
- **artist_profiles** – Artist info, sales, earnings
- **company_profiles** – Company info, purchases, spend
- **creative_works** – Uploaded files (images/audio/video/text)
- **listings** – Marketplace listings (price, license, status)
- **purchases** – Purchase records (Stripe payment intent, license key)
- **public_dataset_entries** – Indexed CC/Wikimedia entries

---

## API Endpoints

### Marketplace
- `GET /marketplace/listings` – Browse with filters
- `GET /marketplace/listings/{id}` – Listing detail
- `POST /marketplace/works/upload` – Upload creative work
- `POST /marketplace/listings/create` – Create listing
- `POST /marketplace/listings/{id}/purchase` – Initiate purchase
- `GET /marketplace/purchases` – User's purchases
- `GET /marketplace/license/{key}` – Verify license key

### Stripe
- `POST /stripe/connect/onboard` – Start artist onboarding
- `GET /stripe/connect/status` – Check onboarding status
- `POST /stripe/webhook` – Process payment events

### Profiles
- `POST /profiles/register` – Create account (artist/company)
- `POST /profiles/login` – Sign in
- `GET /profiles/artist/{id}` – Artist profile + listings
- `GET /profiles/company/{id}` – Company profile + purchases

### Public Datasets
- `GET /marketplace/public-datasets` – Browse indexed entries
- `GET /marketplace/public-datasets/search/wikimedia` – Search Wikimedia

---

## Stripe Integration

ArtLock uses **Stripe Connect** for artist payouts and **Stripe Checkout** for company purchases.

### Payment Flow
1. Company clicks "Buy license" on a listing
2. Backend creates Stripe Checkout session with `application_fee_amount` (10%)
3. Company completes payment on Stripe Checkout
4. Stripe webhook fires `checkout.session.completed`
5. Backend generates license key, marks purchase complete
6. Artist receives 90% instantly; platform keeps 10%

### Artist Onboarding
1. Artist clicks "Set up Stripe" on dashboard
2. Backend creates Stripe Connect Express account
3. Artist completes onboarding on Stripe
4. Backend webhook receives `account.updated`
5. Artist can now receive payouts

---

## License

MIT – See [LICENSE](LICENSE) for details.

---

## Contributing

Pull requests welcome! For major changes, open an issue first.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a pull request

---

Built with ❤️ for artists and AI researchers who believe in fair compensation.
