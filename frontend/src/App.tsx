import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import DetectionResults from './pages/DetectionResults'
import Privacy from './pages/Privacy'
import AdminPanel from './pages/AdminPanel'
import Login from './pages/Login'
import CookieConsent from './components/CookieConsent'
import { useAuthStore } from './store/authStore'

function App() {
  return (
    <Router>
      <Toaster position="top-right" />
      <CookieConsent />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
          <Route path="results" element={<ProtectedRoute><DetectionResults /></ProtectedRoute>} />
          <Route path="privacy" element={<ProtectedRoute><Privacy /></ProtectedRoute>} />
          <Route path="admin" element={<ProtectedRoute adminOnly><AdminPanel /></ProtectedRoute>} />
        </Route>
      </Routes>
    </Router>
  )
}

interface ProtectedRouteProps {
  children: React.ReactNode
  adminOnly?: boolean
}

function ProtectedRoute({ children, adminOnly = false }: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (adminOnly && user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}

export default App
