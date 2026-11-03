import { FaCar } from 'react-icons/fa'
import { FiMapPin } from 'react-icons/fi'
import { formatRupees } from '../../lib/format'
import type { Car } from '../../types/car'

export function CarCard({ car }: { car: Car }) {
  return (
    <article className="rounded-xl border border-ink-200 bg-white overflow-hidden">
      <div className="relative h-40 bg-ink-100 flex items-center justify-center text-ink-400">
        <FaCar className="text-5xl" aria-hidden />
        <span className="absolute top-3 left-3 rounded-full bg-white/90 px-2.5 py-0.5 text-xs font-medium capitalize text-ink-800">
          {car.category}
        </span>
      </div>
      <div className="p-4">
        <h2 className="font-semibold text-ink-900">
          {car.make} {car.model} <span className="font-normal text-ink-600">· {car.year}</span>
        </h2>
        <p className="mt-1 flex items-center gap-1 text-sm text-ink-600">
          <FiMapPin aria-hidden /> {car.city}
          {car.state && `, ${car.state}`}
        </p>
        <p className="mt-3 text-ink-900">
          <span className="text-lg font-bold">{formatRupees(car.daily_rate)}</span>
          <span className="text-sm text-ink-600"> / day</span>
        </p>
      </div>
    </article>
  )
}

export function CarCardSkeleton() {
  return (
    <div className="rounded-xl border border-ink-200 bg-white overflow-hidden animate-pulse" aria-hidden>
      <div className="h-40 bg-ink-100" />
      <div className="p-4 space-y-3">
        <div className="h-4 w-2/3 rounded bg-ink-100" />
        <div className="h-3 w-1/3 rounded bg-ink-100" />
        <div className="h-5 w-1/4 rounded bg-ink-100" />
      </div>
    </div>
  )
}
