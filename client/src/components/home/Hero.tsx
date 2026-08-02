import { Link } from 'react-router-dom'

export default function Hero() {
  return (
    <section className="relative bg-ink-900 text-white overflow-hidden">
      {/* Subtle warm glow, not a loud gradient — "minimalism with purpose" */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-700/20 via-transparent to-transparent" />
      <div className="relative max-w-6xl mx-auto px-4 py-28 text-center">
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight">
          Rent any car, from real people <span className="text-brand-400">near you</span>
        </h1>
        <p className="mt-5 text-lg text-ink-200 max-w-2xl mx-auto">
          CarVault connects car owners with renters directly — better prices for renters,
          real income for owners.
        </p>
        <div className="mt-9 flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/cars"
            className="px-6 py-3 rounded-lg bg-brand-600 text-white font-semibold hover:bg-brand-500 transition-colors"
          >
            Find a car
          </Link>
          <Link
            to="/register?role=car_owner"
            className="px-6 py-3 rounded-lg border border-ink-600 font-semibold hover:bg-ink-800 transition-colors"
          >
            List your car
          </Link>
        </div>
      </div>
    </section>
  )
}
