import { Outlet, Link, useLocation } from 'react-router-dom'
import { Shield, Upload, BarChart3, Settings, LogOut, Lock } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

export default function Layout() {
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
    { name: 'Upload Artwork', href: '/upload', icon: Upload },
    { name: 'Detection Results', href: '/results', icon: Shield },
    { name: 'Privacy Settings', href: '/privacy', icon: Lock },
  ]

  if (user?.role === 'admin') {
    navigation.push({ name: 'Admin Panel', href: '/admin', icon: Settings })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">ArtLockr</span>
            </div>

            {/* Navigation Links */}
            <div className="hidden md:flex space-x-4">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {item.name}
                  </Link>
                )
              })}
            </div>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">{user?.name}</span>
              <button
                onClick={logout}
                className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
