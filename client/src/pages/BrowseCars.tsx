import { useEffect, useMemo, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import Header from '../components/layout/Header'
import Footer from '../components/layout/Footer'
import CarFilters from '../components/cars/CarFilters'
import { CarCard, CarCardSkeleton } from '../components/cars/CarCard'
import { useCarFeed } from '../hooks/useCarFeed'
import type { CarFilters as Filters } from '../types/car'

const FILTER_NAMES: (keyof Filters)[] = ['city', 'category', 'min_price', 'max_price']

export default function BrowseCars() {
  const [searchParams, setSearchParams] = useSearchParams()
  const city = searchParams.get('city') ?? ''
  const category = searchParams.get('category') ?? ''
  const minPrice = searchParams.get('min_price') ?? ''
  const maxPrice = searchParams.get('max_price') ?? ''

  const filters = useMemo(
    () => ({ city, category, min_price: minPrice, max_price: maxPrice }),
    [city, category, minPrice, maxPrice],
  )
  const feed = useCarFeed(filters)
  const { hasMore, loadingMore, moreFailed, loadMore } = feed
  const hasFilters = FILTER_NAMES.some((name) => filters[name])

  const heading = useRef<HTMLHeadingElement>(null)
  const cityInput = useRef<HTMLInputElement>(null)
  const sentinel = useRef<HTMLDivElement>(null)

  function updateFilter(name: keyof Filters, value: string) {
    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current)
        if (value) next.set(name, value)
        else next.delete(name)
        return next
      },
      { replace: true },
    )
  }

  function clearFilters() {
    setSearchParams({}, { replace: true })
    cityInput.current?.focus()
  }

  function retryFirstPage() {
    feed.retry()
    heading.current?.focus()
  }

  useEffect(() => {
    const node = sentinel.current
    if (!node || !hasMore || moreFailed || typeof IntersectionObserver === 'undefined') return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) loadMore()
      },
      { rootMargin: '400px' },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [hasMore, moreFailed, loadMore])

  let announcement = ''
  if (feed.status === 'loading') announcement = 'Loading cars…'
  else if (feed.status === 'error') announcement = "Couldn't load cars."
  else if (feed.cars.length === 0) announcement = hasFilters ? 'No cars match these filters.' : 'No cars listed yet.'
  else if (loadingMore) announcement = 'Loading more cars…'
  else if (moreFailed) announcement = "Couldn't load more cars."
  else announcement = `${feed.cars.length} cars shown${hasMore ? ', more available' : ''}.`

  return (
    <div className="min-h-screen flex flex-col bg-ink-50">
      <Header />
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        <h1 ref={heading} tabIndex={-1} className="text-2xl font-bold text-ink-900 outline-none">
          Browse cars
        </h1>
        <div className="mt-6">
          <CarFilters filters={filters} onChange={updateFilter} cityInputRef={cityInput} />
        </div>

        <p role="status" className="sr-only">
          {announcement}
        </p>

        <section className="mt-8">
          {feed.status === 'loading' && (
            <div aria-hidden className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }, (_, i) => (
                <CarCardSkeleton key={i} />
              ))}
            </div>
          )}

          {feed.status === 'error' && (
            <div className="rounded-xl border border-ink-200 bg-white p-10 text-center">
              <p className="font-medium text-ink-900">Couldn't load cars.</p>
              <p className="mt-1 text-sm text-ink-600">Check your connection and try again.</p>
              <button
                onClick={retryFirstPage}
                className="mt-4 rounded-lg bg-brand-600 px-4 py-2 font-semibold text-white hover:bg-brand-500"
              >
                Retry
              </button>
            </div>
          )}

          {feed.status === 'ready' && feed.cars.length === 0 && (
            <div className="rounded-xl border border-ink-200 bg-white p-10 text-center">
              <p className="font-medium text-ink-900">
                {hasFilters ? 'No cars match these filters.' : 'No cars listed yet.'}
              </p>
              {hasFilters && (
                <button onClick={clearFilters} className="mt-4 font-semibold text-brand-600 hover:text-brand-700">
                  Clear filters
                </button>
              )}
            </div>
          )}

          {feed.status === 'ready' && feed.cars.length > 0 && (
            <>
              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {feed.cars.map((car) => (
                  <CarCard key={car.id} car={car} />
                ))}
              </div>

              <div ref={sentinel} className="mt-8 flex flex-col items-center gap-2 text-sm text-ink-600">
                {moreFailed && <p>Couldn't load more.</p>}
                {/* One button that changes label, so keyboard focus survives loading and retrying. */}
                {hasMore && (
                  <button
                    onClick={moreFailed ? feed.retry : loadMore}
                    aria-disabled={loadingMore}
                    aria-busy={loadingMore}
                    className="rounded-lg border border-ink-200 bg-white px-4 py-2 font-semibold text-ink-800 hover:bg-ink-100 aria-disabled:cursor-wait aria-disabled:opacity-60"
                  >
                    {loadingMore ? 'Loading…' : moreFailed ? 'Retry' : 'Load more'}
                  </button>
                )}
                {!hasMore && <p>You've seen all {feed.cars.length} cars.</p>}
              </div>
            </>
          )}
        </section>
      </main>
      <Footer />
    </div>
  )
}
