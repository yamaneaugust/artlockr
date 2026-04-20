import { Link } from 'react-router-dom'
import { Lock, Camera, FileCheck, Search, FileText } from 'lucide-react'

export default function Homepage() {
  return (
    <div className="min-h-screen bg-[#0a0e27] text-white overflow-hidden">
      {/* Navigation */}
      <nav className="relative z-10 border-b border-blue-900/50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2">
              <Lock className="h-8 w-8 text-orange-500" fill="currentColor" />
              <span className="text-xl font-bold text-white">ArtLock</span>
            </Link>

            {/* Center Nav */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-300 hover:text-white transition-colors">
                Features
              </a>
              <a href="#verify" className="text-gray-300 hover:text-white transition-colors">
                Verify Datasets
              </a>
              <a href="#about" className="text-gray-300 hover:text-white transition-colors">
                About
              </a>
            </div>

            {/* Right Nav */}
            <div className="flex items-center gap-4">
              <Link
                to="/login"
                className="text-gray-300 hover:text-white transition-colors px-4 py-2"
              >
                Log In
              </Link>
              <Link
                to="/login?role=artist"
                className="bg-orange-500 hover:bg-orange-600 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 px-6 overflow-hidden">
        {/* Particle background effect */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-950 via-[#0a0e27] to-blue-900">
          <div className="absolute inset-0 opacity-30" style={{
            backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(255, 140, 0, 0.1) 0%, transparent 50%)',
            backgroundSize: '100px 100px'
          }} />
        </div>

        <div className="max-w-7xl mx-auto relative z-10">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            {/* Left: Text Content */}
            <div>
              <h1 className="text-5xl md:text-6xl font-bold leading-tight mb-6">
                Track, <span className="text-orange-500">license</span>, and{' '}
                <span className="text-orange-500">verify</span>
                <br />
                creative content used
                <br />
                in AI <span className="text-orange-500">datasets</span>.
              </h1>
              <p className="text-lg text-gray-400 mb-8 max-w-lg">
                Empowering creators and AI companies with a secure platform to manage permissions
                and audit datasets.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link
                  to="/login?role=artist"
                  className="px-8 py-4 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-lg transition-colors"
                >
                  I'm a Creator
                </Link>
                <Link
                  to="/login?role=company"
                  className="px-8 py-4 border-2 border-orange-500 text-orange-400 hover:bg-orange-500 hover:text-white font-semibold rounded-lg transition-colors"
                >
                  I'm an AI Company
                </Link>
              </div>
            </div>

            {/* Right: Holographic Visual */}
            <div className="hidden md:block relative h-96">
              <div className="absolute inset-0 flex items-center justify-center">
                {/* Simulated holographic interface */}
                <div className="relative w-full h-full">
                  <div className="absolute top-1/4 right-0 w-72 h-64 border border-orange-500/30 rounded-2xl bg-gradient-to-br from-orange-500/5 to-transparent backdrop-blur-sm transform rotate-6 shadow-2xl shadow-orange-500/20">
                    <div className="absolute top-4 left-4 w-24 h-24 rounded-full bg-gradient-to-br from-orange-500 to-orange-600 opacity-80 blur-sm" />
                    <div className="absolute top-8 left-8 w-16 h-16 rounded-full border-4 border-orange-400" style={{
                      background: 'radial-gradient(circle, rgba(255,140,0,0.4) 0%, transparent 70%)'
                    }} />
                  </div>
                  <div className="absolute bottom-1/4 left-0 w-48 h-48 border border-orange-500/20 rounded-xl bg-gradient-to-tl from-orange-500/10 to-transparent transform -rotate-12" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-20 px-6">
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h2 className="text-3xl md:text-4xl font-bold mb-12">
            Create an account today and join a{' '}
            <span className="text-orange-500">trustworthy ecosystem</span> designed for
            transparency and <span className="text-orange-500">control</span>.
          </h2>
          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            <Link
              to="/login?role=artist"
              className="px-12 py-5 bg-orange-500 hover:bg-orange-600 text-white text-lg font-semibold rounded-xl transition-colors"
            >
              I'm a Creator
            </Link>
            <Link
              to="/login?role=company"
              className="px-12 py-5 border-2 border-orange-500 text-orange-400 hover:bg-orange-500 hover:text-white text-lg font-semibold rounded-xl transition-colors"
            >
              I'm an AI Company
            </Link>
          </div>
        </div>

        {/* Holographic code background effect */}
        <div className="absolute inset-0 overflow-hidden opacity-20">
          <div className="absolute bottom-0 left-1/4 w-96 h-64 border border-orange-500/30 rounded-2xl bg-gradient-to-br from-orange-500/10 to-transparent transform -rotate-6" />
          <div className="absolute bottom-0 right-1/4 w-80 h-56 border border-orange-500/20 rounded-xl bg-gradient-to-tl from-orange-500/10 to-transparent transform rotate-12" />
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-20 px-6" id="features">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { icon: Camera, title: 'Register Your Work' },
              { icon: FileCheck, title: 'Define Licensing Rules' },
              { icon: Search, title: 'Verify Datasets' },
              { icon: FileText, title: 'Generate Audit Reports' },
            ].map(({ icon: Icon, title }) => (
              <div key={title} className="text-center group">
                <div className="mb-4 flex justify-center">
                  <div className="relative">
                    <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-orange-500/20 to-orange-600/10 border border-orange-500/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <Icon className="w-10 h-10 text-orange-500" strokeWidth={1.5} />
                    </div>
                    <div className="absolute inset-0 bg-orange-500/20 rounded-2xl blur-xl group-hover:bg-orange-500/30 transition-colors" />
                  </div>
                </div>
                <h3 className="text-white font-medium">{title}</h3>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-blue-900/50 py-8 px-6 mt-20">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-sm text-gray-500">© 2026 ArtLock.</p>
        </div>
      </footer>
    </div>
  )
}
