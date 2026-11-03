import { api } from './api'
import type { CarFilters, CarPage } from '../types/car'

export const PAGE_SIZE = 12

export async function fetchCars(
  filters: CarFilters,
  cursor: string | null,
  signal?: AbortSignal,
): Promise<CarPage> {
  const params: Record<string, string | number> = { limit: PAGE_SIZE }
  for (const [name, value] of Object.entries(filters)) {
    if (value) params[name] = value
  }
  if (cursor) params.cursor = cursor

  const { data } = await api.get<CarPage>('/cars', { params, signal })
  return data
}
