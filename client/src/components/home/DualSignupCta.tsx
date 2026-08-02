import { Link } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

export default function DualSignupCta() {
  const { user } = useAuthStore()

  // Don't show a "sign up" pitch to someone who's already logged in.
  if (user) return null

  return (
    <section className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-4 grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="rounded-xl border border-ink-200 p-8 text-center hover:border-brand-300 transition-colors">
          <h3 className="text-xl font-semibold text-ink-900">Looking to rent?</h3>
          <p className="mt-2 text-ink-600">Browse cars near you and book in minutes.</p>
          <Link
            to="/register?role=customer"
            className="mt-6 inline-block px-6 py-3 rounded-lg bg-brand-600 text-white font-semibold hover:bg-brand-700 transition-colors"
          >
            Sign up to rent
          </Link>
        </div>
        <div className="rounded-xl border border-ink-200 p-8 text-center hover:border-brand-300 transition-colors">
          <h3 className="text-xl font-semibold text-ink-900">Have a car to share?</h3>
          <p className="mt-2 text-ink-600">List it on CarVault and start earning from it.</p>
          <Link
            to="/register?role=car_owner"
            className="mt-6 inline-block px-6 py-3 rounded-lg border border-ink-900 text-ink-900 font-semibold hover:bg-ink-50 transition-colors"
          >
            Become a host
          </Link>
        </div>
      </div>
    </section>
  )
}
