import { Link } from 'react-router-dom'
import { Camera, FileCheck, Search, FileText, ShoppingBag, Lock } from 'lucide-react'

export default function Features() {
  return (
    <div className="min-h-screen bg-artlock-dark text-white overflow-hidden relative">
      {/* Starfield background */}
      <div className="fixed inset-0 opacity-50">
        <div className="absolute inset-0" style={{
          backgroundImage: `
            radial-gradient(2px 2px at 20% 30%, white, transparent),
            radial-gradient(2px 2px at 60% 70%, white, transparent),
            radial-gradient(1px 1px at 50% 50%, white, transparent),
            radial-gradient(1px 1px at 80% 10%, white, transparent),
            radial-gradient(2px 2px at 90% 60%, white, transparent),
            radial-gradient(1px 1px at 33% 85%, white, transparent),
            radial-gradient(1px 1px at 75% 40%, white, transparent)
          `,
          backgroundSize: '200% 200%',
          backgroundPosition: '50% 50%'
        }} />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 border-b border-blue-900/30">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div></div>

            {/* Center Nav */}
            <div className="hidden md:flex items-center gap-8">
              <Link to="/features" className="text-gray-300 hover:text-white transition-colors">
                Features
              </Link>
              <Link to="/detect" className="text-gray-300 hover:text-white transition-colors">
                Verify Datasets
              </Link>
              <Link to="/marketplace" className="text-gray-300 hover:text-white transition-colors">
                Marketplace
              </Link>
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

      <div className="relative z-10 p-6">
        <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16 pt-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Powerful Features for <span className="text-orange-500">Creators</span> and{' '}
            <span className="text-orange-500">AI Companies</span>
          </h1>
          <p className="text-lg text-blue-300 max-w-2xl mx-auto">
            Everything you need to track, license, and verify creative content used in AI datasets.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-16">
          {[
            {
              icon: Camera,
              title: 'Register Your Work',
              description:
                'Upload and register your creative works with cryptographic fingerprinting. Every piece carries a provable signature of ownership that can be verified anywhere.',
            },
            {
              icon: FileCheck,
              title: 'Define Licensing Rules',
              description:
                'Set custom licensing terms and pricing for your work. Choose from standard Creative Commons licenses or create custom agreements tailored to your needs.',
            },
            {
              icon: Search,
              title: 'Verify Datasets',
              description:
                'Scan AI training datasets to detect if your work has been used without permission. Our detection system checks against indexed datasets and public crawls.',
            },
            {
              icon: FileText,
              title: 'Generate Audit Reports',
              description:
                'Create comprehensive audit trails and provenance reports for compliance. Perfect for AI companies that need transparent, auditable licensing documentation.',
            },
            {
              icon: ShoppingBag,
              title: 'Buy Legal Data',
              description:
                'Access a curated marketplace of properly licensed creative works for AI training. Browse verified datasets with transparent licensing and full provenance documentation.',
            },
          ].map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-2xl border border-blue-900/30 p-8 hover:border-orange-500/30 transition-all group"
            >
              <div className="flex items-start gap-4">
                <div className="relative flex-shrink-0">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-600/30 to-orange-800/20 border border-blue-900/30 flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg shadow-orange-500/20">
                    <Icon className="w-8 h-8 text-orange-400" strokeWidth={1.5} />
                  </div>
                  <div className="absolute inset-0 bg-orange-500/30 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white mb-3">{title}</h3>
                  <p className="text-blue-300 leading-relaxed">{description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
        </div>
      </div>
    </div>
  )
}
