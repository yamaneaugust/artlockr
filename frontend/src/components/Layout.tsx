import { Outlet, Link, useLocation } from 'react-router-dom'
import { ShoppingBag, Upload, LayoutDashboard, Database, CreditCard, LogOut, Palette } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

export default function Layout() {
  const location = useLocation()
  const { user, logout, isAuthenticated } = useAuthStore()

  const navItems = [
    { name: 'Marketplace', href: '/marketplace', icon: ShoppingBag, always: true },
    { name: 'Public Datasets', href: '/datasets', icon: Database, always: true },
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, auth: true },
    { name: 'Upload Work', href: '/upload', icon: Upload, role: 'artist' },
    { name: 'My Licenses', href: '/purchases', icon: CreditCard, role: 'company' },
  ]

  const visibleNav = navItems.filter((item) => {
    if (item.always) return true
    if (item.auth && isAuthenticated) return true
    if (item.role && user?.role === item.role) return true
    return false
  })

  return (
    <div className="min-h-screen bg-[#0a0e27]">
      <nav className="bg-[#0a0e27] border-b border-blue-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2">
              <Palette className="h-7 w-7 text-orange-500" />
              <span className="text-xl font-bold text-white">ArtLock</span>
            </Link>

            <div className="hidden md:flex items-center space-x-1">
              {visibleNav.map(({ name, href, icon: Icon }) => (
                <Link
                  key={href}
                  to={href}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    location.pathname.startsWith(href)
                      ? 'bg-orange-500/10 text-orange-400'
                      : 'text-blue-300 hover:text-white hover:bg-blue-900'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {name}
                </Link>
              ))}
            </div>

            <div className="flex items-center gap-3">
              {isAuthenticated ? (
                <>
                  <span className="text-sm text-blue-300 hidden sm:block">
                    {user?.username}
                    <span className="ml-1.5 px-1.5 py-0.5 rounded text-xs font-medium bg-orange-500/20 text-orange-400 capitalize">
                      {user?.role}
                    </span>
                  </span>
                  <button
                    onClick={logout}
                    className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-blue-300 hover:text-white hover:bg-blue-900 rounded-lg transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    <span className="hidden sm:inline">Logout</span>
                  </button>
                </>
              ) : (
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-white bg-orange-500 hover:bg-orange-600 rounded-lg transition-colors"
                >
                  Sign in
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
