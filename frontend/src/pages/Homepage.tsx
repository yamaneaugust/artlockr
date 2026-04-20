import { Link } from 'react-router-dom'
import { Palette, Shield, DollarSign, Zap, Users, Globe, CheckCircle } from 'lucide-react'

export default function Homepage() {
  return (
    <div className="min-h-screen bg-blue-950">
      {/* Hero */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center max-w-3xl mx-auto">
          <div className="flex items-center justify-center gap-3 mb-6">
            <Palette className="h-12 w-12 text-orange-500" />
            <h1 className="text-5xl font-bold text-white">ArtLock</h1>
          </div>
          <p className="text-xl text-blue-200 mb-8">
            The marketplace where artists legally sell creative works to AI companies
          </p>
          <p className="text-lg text-blue-300 mb-10 max-w-2xl mx-auto">
            Upload your art, set your terms, get paid. AI companies get
            verified, licensed datasets. Everyone wins.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link
              to="/login?role=artist"
              className="px-8 py-4 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl transition-colors shadow-lg"
            >
              I'm a creator
            </Link>
            <Link
              to="/login?role=company"
              className="px-8 py-4 border-2 border-orange-500 text-orange-400 font-semibold rounded-xl hover:bg-orange-500 hover:text-white transition-colors"
            >
              I'm an AI company
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 max-w-4xl mx-auto mt-20">
          {[
            { icon: Users, label: 'Artists & Companies', value: 'Join the community' },
            { icon: Shield, label: 'Licensed & Legal', value: 'Every sale' },
            { icon: DollarSign, label: 'Stripe Payouts', value: 'Instant payments' },
            { icon: Globe, label: 'Public Datasets', value: 'CC & Wikimedia' },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="text-center">
              <Icon className="h-8 w-8 mx-auto text-orange-500 mb-2" />
              <p className="text-sm font-semibold text-white">{value}</p>
              <p className="text-xs text-blue-400">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* How it works */}
      <div className="bg-blue-900 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-white mb-4">
            How it works
          </h2>
          <p className="text-center text-blue-300 mb-16 max-w-2xl mx-auto">
            Simple, transparent, and fair for everyone
          </p>

          <div className="grid md:grid-cols-2 gap-12">
            {/* For Creators */}
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-6">
                <Palette className="h-8 w-8 text-orange-500" />
                <h3 className="text-2xl font-bold text-white">For Creators</h3>
              </div>
              {[
                { step: '1', text: 'Upload your creative work (images, audio, video, text)' },
                { step: '2', text: 'Set your license type and price' },
                { step: '3', text: 'Connect Stripe to receive payouts' },
                { step: '4', text: 'Earn 90% of every sale, instantly' },
              ].map(({ step, text }) => (
                <div key={step} className="flex gap-4 items-start">
                  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-orange-500 text-white font-bold flex items-center justify-center text-sm">
                    {step}
                  </div>
                  <p className="text-blue-200 pt-1">{text}</p>
                </div>
              ))}
            </div>

            {/* For Companies */}
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-6">
                <Zap className="h-8 w-8 text-orange-500" />
                <h3 className="text-2xl font-bold text-white">For AI Companies</h3>
              </div>
              {[
                { step: '1', text: 'Browse verified, licensed creative datasets' },
                { step: '2', text: 'Filter by type, license, and price' },
                { step: '3', text: 'Purchase via Stripe Checkout (instant access)' },
                { step: '4', text: 'Download with license key for compliance' },
              ].map(({ step, text }) => (
                <div key={step} className="flex gap-4 items-start">
                  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-700 text-white font-bold flex items-center justify-center text-sm">
                    {step}
                  </div>
                  <p className="text-blue-200 pt-1">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="bg-blue-950 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-white mb-16">
            Why ArtLock?
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Shield,
                title: 'Fully licensed',
                desc: 'Every sale includes a verified license key. No legal gray areas.',
              },
              {
                icon: DollarSign,
                title: 'Fair pricing',
                desc: 'Artists keep 90%. Platform takes 10%. Paid instantly via Stripe.',
              },
              {
                icon: Globe,
                title: 'Public datasets',
                desc: 'Discover CC0/CC-BY works from Wikimedia, Common Crawl, Freesound.',
              },
              {
                icon: CheckCircle,
                title: 'Multi-format',
                desc: 'Images, audio, video, text, and full datasets. All supported.',
              },
              {
                icon: Zap,
                title: 'Instant access',
                desc: 'Purchase → receive license key → download immediately.',
              },
              {
                icon: Users,
                title: 'Community-first',
                desc: 'Built for artists and AI researchers who believe in fair compensation.',
              },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="bg-blue-900 rounded-2xl border border-blue-800 p-6 hover:border-orange-500 transition-colors">
                <Icon className="h-10 w-10 text-orange-500 mb-4" />
                <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
                <p className="text-sm text-blue-300">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-blue-950 border-t border-blue-900 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <Palette className="h-6 w-6 text-orange-500" />
              <span className="text-white font-bold text-lg">ArtLock</span>
            </div>
            <div className="flex flex-wrap gap-6 text-sm text-blue-400">
              <Link to="/marketplace" className="hover:text-white transition-colors">
                Marketplace
              </Link>
              <Link to="/datasets" className="hover:text-white transition-colors">
                Public Datasets
              </Link>
              <Link to="/login" className="hover:text-white transition-colors">
                Sign in
              </Link>
            </div>
            <p className="text-sm text-blue-500">
              © 2026 ArtLock.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
