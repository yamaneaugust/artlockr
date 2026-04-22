import { Link } from 'react-router-dom'
import { Lock, Camera, FileCheck, Search, FileText } from 'lucide-react'

export default function Homepage() {
  return (
    <div className="min-h-screen bg-[#0a0e27] text-white">
      {/* Navigation */}
      <nav className="border-b border-blue-900/30">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2">
              <Lock className="h-6 w-6 text-orange-500" />
              <span className="text-lg font-semibold">ArtLock</span>
            </Link>

            <div className="hidden md:flex items-center gap-6">
              <a href="#features" className="text-sm text-blue-300 hover:text-white">
                Features
              </a>
              <Link to="/detect" className="text-sm text-blue-300 hover:text-white">
                Verify Datasets
              </Link>
              <Link to="/marketplace" className="text-sm text-blue-300 hover:text-white">
                Marketplace
              </Link>
            </div>

            <div className="flex items-center gap-3">
              <Link to="/login" className="text-sm text-blue-300 hover:text-white px-3 py-2">
                Log In
              </Link>
              <Link
                to="/login?role=artist"
                className="text-sm bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg"
              >
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="max-w-2xl">
          <h1 className="text-5xl font-bold leading-tight mb-6">
            License your creative work for AI training
          </h1>
          <p className="text-xl text-blue-200 mb-8 leading-relaxed">
            Register artwork, set license terms, and track usage in AI datasets. Get paid when
            companies use your work.
          </p>
          <div className="flex gap-3">
            <Link
              to="/login?role=artist"
              className="px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-medium rounded-lg"
            >
              I'm a Creator
            </Link>
            <Link
              to="/login?role=company"
              className="px-6 py-3 border border-orange-500 text-orange-400 hover:bg-orange-500 hover:text-white rounded-lg"
            >
              I'm an AI Company
            </Link>
          </div>
        </div>
      </section>

      {/* What It Does */}
      <section className="max-w-6xl mx-auto px-6 py-16 border-t border-blue-900/30">
        <div className="grid md:grid-cols-2 gap-16">
          <div>
            <h2 className="text-2xl font-bold mb-4">For Creators</h2>
            <ul className="space-y-3 text-blue-200">
              <li className="flex gap-3">
                <span className="text-orange-500 font-bold">→</span>
                <span>Upload and register your work with metadata and license terms</span>
              </li>
              <li className="flex gap-3">
                <span className="text-orange-500 font-bold">→</span>
                <span>Set pricing: one-time, subscription, or custom deals</span>
              </li>
              <li className="flex gap-3">
                <span className="text-orange-500 font-bold">→</span>
                <span>Check if your work appears in public datasets without permission</span>
              </li>
              <li className="flex gap-3">
                <span className="text-orange-500 font-bold">→</span>
                <span>Track sales and payouts through Stripe Connect</span>
              </li>
            </ul>
          </div>

          <div>
            <h2 className="text-2xl font-bold mb-4">For AI Companies</h2>
            <ul className="space-y-3 text-blue-200">
              <li className="flex gap-3">
                <span className="text-orange-500 font-bold">→</span>
                <span>Browse licensed datasets filtered by type, license, and price</span>
              </li>
              <li className="flex gap-3">
                <span className="text-orange-500 font-bold">→</span>
                <span>Purchase licenses with verifiable audit trails</span>
              </li>
              <li className="flex gap-3">
                <span className="text-orange-500 font-bold">→</span>
                <span>Prove compliance with creator consent and license terms</span>
              </li>
              <li className="flex gap-3">
                <span className="text-orange-500 font-bold">→</span>
                <span>Download datasets with usage rights documentation</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-16 border-t border-blue-900/30" id="features">
        <h2 className="text-2xl font-bold mb-8">Platform Features</h2>
        <div className="grid md:grid-cols-4 gap-6">
          {[
            {
              icon: Camera,
              title: 'Register Your Work',
              desc: 'Upload images, audio, video, or text with license metadata',
            },
            {
              icon: FileCheck,
              title: 'Define License Rules',
              desc: 'Set CC0, CC-BY, non-exclusive, exclusive, or custom terms',
            },
            {
              icon: Search,
              title: 'Verify Datasets',
              desc: 'Scan public datasets to detect unauthorized use',
            },
            {
              icon: FileText,
              title: 'Generate Reports',
              desc: 'Download audit trails and compliance documentation',
            },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="p-6 bg-blue-900/30 rounded-lg border border-blue-800/50">
              <Icon className="w-6 h-6 text-orange-500 mb-3" />
              <h3 className="font-semibold mb-2">{title}</h3>
              <p className="text-sm text-blue-300 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-6 py-16 border-t border-blue-900/30">
        <div className="max-w-2xl">
          <h2 className="text-3xl font-bold mb-4">Ready to get started?</h2>
          <p className="text-lg text-blue-200 mb-6">
            Create an account to register your work or browse the marketplace.
          </p>
          <div className="flex gap-3">
            <Link
              to="/login?role=artist"
              className="px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-medium rounded-lg"
            >
              Sign Up as Creator
            </Link>
            <Link
              to="/login?role=company"
              className="px-6 py-3 border border-blue-700 text-blue-300 hover:bg-blue-900/50 rounded-lg"
            >
              Sign Up as Company
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-blue-900/30 py-8 px-6 mt-8">
        <div className="max-w-6xl mx-auto text-center">
          <p className="text-sm text-blue-500">© 2026 ArtLock</p>
        </div>
      </footer>
    </div>
  )
}
