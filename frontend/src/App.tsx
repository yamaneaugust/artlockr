import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import Homepage from './pages/Homepage'
import Marketplace from './pages/Marketplace'
import ListingDetail from './pages/ListingDetail'
import Upload from './pages/Upload'
import Purchases from './pages/Purchases'
import PublicDatasets from './pages/PublicDatasets'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Detect from './pages/Detect'
import { useAuthStore } from './store/authStore'

function App() {
  return (
    <Router>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/" element={<Homepage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Layout />}>
          <Route path="marketplace" element={<Marketplace />} />
          <Route path="marketplace/:id" element={<ListingDetail />} />
          <Route path="datasets" element={<PublicDatasets />} />
          <Route
            path="dashboard"
            element={
              <Protected>
                <Dashboard />
              </Protected>
            }
          />
          <Route
            path="upload"
            element={
              <Protected role="artist">
                <Upload />
              </Protected>
            }
          />
          <Route
            path="detect"
            element={
              <Protected>
                <Detect />
              </Protected>
            }
          />
          <Route
            path="purchases"
            element={
              <Protected role="company">
                <Purchases />
              </Protected>
            }
          />
        </Route>
      </Routes>
    </Router>
  )
}

function Protected({
  children,
  role,
}: {
  children: React.ReactNode
  role?: 'artist' | 'company'
}) {
  const { isAuthenticated, user } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (role && user?.role !== role) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export default App
