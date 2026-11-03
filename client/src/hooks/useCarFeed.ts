import { useCallback, useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { fetchCars } from '../lib/cars'
import type { Car, CarFilters } from '../types/car'

type Status = 'loading' | 'error' | 'ready'

export function useCarFeed(filters: CarFilters) {
  const [cars, setCars] = useState<Car[]>([])
  const [hasMore, setHasMore] = useState(false)
  const [status, setStatus] = useState<Status>('loading')
  const [loadingMore, setLoadingMore] = useState(false)
  const [moreFailed, setMoreFailed] = useState(false)
  const inFlight = useRef<AbortController | null>(null)
  // Read by loadMore at call time rather than through a closure: the scroll
  // observer can hold a loadMore from before a filter change, and it must not
  // ask for the old search's next page.
  const progress = useRef<{ cursor: string | null; busy: boolean }>({ cursor: null, busy: true })

  const request = useCallback(
    async (after: string | null) => {
      // Only the newest request may touch state. Cancelling the previous one
      // stops a slow response for old filters landing on top of new results.
      inFlight.current?.abort()
      const controller = new AbortController()
      inFlight.current = controller
      progress.current = { cursor: after, busy: true }

      setMoreFailed(false)
      if (after) {
        setLoadingMore(true)
      } else {
        setStatus('loading')
        setLoadingMore(false)
        setCars([])
        setHasMore(false)
      }

      try {
        const page = await fetchCars(filters, after, controller.signal)
        if (controller.signal.aborted) return
        progress.current.cursor = page.next_cursor
        setCars((previous) => (after ? [...previous, ...page.items] : page.items))
        setHasMore(page.next_cursor !== null)
        setStatus('ready')
      } catch (error) {
        if (controller.signal.aborted || axios.isCancel(error)) return
        if (after) setMoreFailed(true)
        else setStatus('error')
      } finally {
        if (inFlight.current === controller) {
          progress.current.busy = false
          setLoadingMore(false)
        }
      }
    },
    [filters],
  )

  useEffect(() => {
    request(null)
    return () => inFlight.current?.abort()
  }, [request])

  const loadMore = useCallback(() => {
    const { cursor, busy } = progress.current
    if (cursor && !busy) request(cursor)
  }, [request])

  const retry = useCallback(() => {
    request(progress.current.cursor)
  }, [request])

  return { cars, status, hasMore, loadingMore, moreFailed, loadMore, retry }
}
