# ArtLock Frontend

Modern React + TypeScript frontend for ArtLock, the AI-powered copyright detection system for artists.

## Features

- **Artist Dashboard**: Upload and manage your artwork portfolio
- **Real-time Detection**: View copyright detection results with interactive visualizations
- **Privacy Controls**: Full GDPR/CCPA compliance with granular consent management
- **Cookie Management**: Customizable cookie preferences with transparency
- **Admin Panel**: System monitoring, security analytics, and compliance dashboard
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **React Router** - Client-side routing
- **Zustand** - Lightweight state management
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **React Dropzone** - File upload
- **React Hot Toast** - Notifications
- **Lucide React** - Modern icon library

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

The app will be available at http://localhost:3000

### Build for Production

```bash
# Type check
npm run type-check

# Build
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Layout.tsx       # Main layout with navigation
│   │   └── CookieConsent.tsx # Cookie consent banner
│   ├── pages/               # Page components
│   │   ├── Login.tsx        # Authentication
│   │   ├── Dashboard.tsx    # Artist dashboard
│   │   ├── Upload.tsx       # Artwork upload
│   │   ├── DetectionResults.tsx # Detection viewer
│   │   ├── Privacy.tsx      # Privacy settings
│   │   └── AdminPanel.tsx   # Admin monitoring
│   ├── services/            # API and business logic
│   │   └── api.ts          # API client
│   ├── store/               # State management
│   │   └── authStore.ts    # Authentication state
│   ├── App.tsx             # Root component with routing
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── public/                  # Static assets
├── index.html              # HTML template
├── vite.config.ts          # Vite configuration
├── tsconfig.json           # TypeScript config
├── tailwind.config.js      # Tailwind config
└── package.json            # Dependencies
```

## Key Features

### Privacy-First Design

- Features-only storage (no images stored)
- Immediate image deletion after processing
- Cryptographic ownership proofs
- Full data transparency and export
- GDPR/CCPA/COPPA compliance

### Advanced Detection

- Multi-metric similarity fusion (~95% accuracy)
- 5 similarity metrics: cosine, SSIM, perceptual, color histogram, multi-layer
- Art style-aware thresholds (8 presets)
- Complexity-adjusted detection
- Real-time visualization of results

### Security & Compliance

- Granular consent management (8 consent types)
- Cookie preferences (4 categories)
- IP reputation tracking
- Rate limiting visualization
- Adversarial attack detection
- Organization blocking

## API Integration

The frontend communicates with the FastAPI backend via the API client (`src/services/api.ts`). All API calls are automatically authenticated with JWT tokens stored in Zustand.

### Main Endpoints Used:

- `POST /upload-artwork-private` - Upload artwork with privacy
- `POST /detect-copyright-multimetric/{id}` - Run detection with multi-metric fusion
- `GET /privacy/my-data` - Export user data (GDPR)
- `POST /consent/grant` - Grant consent
- `POST /block-organization` - Block infringing organization
- `GET /security/analytics` - Admin security dashboard

## Development

### Code Style

- ESLint for linting
- TypeScript strict mode
- Tailwind CSS for styling
- Functional components with hooks

### State Management

- Zustand for global state (auth, preferences)
- React hooks for local state
- Persistent storage with `zustand/middleware`

### Routing

Protected routes require authentication:
```typescript
<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>
```

Admin routes require admin role:
```typescript
<ProtectedRoute adminOnly>
  <AdminPanel />
</ProtectedRoute>
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000/api/v1` |
| `VITE_ENV` | Environment | `development` |

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## License

Copyright © 2024 ArtLock. All rights reserved.
