import Header from '../components/layout/Header'
import Footer from '../components/layout/Footer'

// Placeholder until the backend's Car model/endpoints exist (Phase 4).
// Deliberately its own page now so the real listing UI slots in later
// without reshuffling the site's routes/navigation.
export default function BrowseCars() {
  return (
    <div className="min-h-screen flex flex-col bg-ink-50">
      <Header />
      <main className="flex-1 flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-ink-900">Car listings coming soon</h1>
          <p className="mt-2 text-ink-600">We're still building this — check back soon.</p>
        </div>
      </main>
      <Footer />
    </div>
  )
}
