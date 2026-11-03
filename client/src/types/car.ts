// Mirrors app/schemas/car.py — keep these in sync whenever the backend schema changes.
export const CAR_CATEGORIES = ['sedan', 'suv', 'hatchback', 'truck', 'van', 'convertible', 'luxury'] as const

export interface Car {
  id: string
  owner_id: string
  make: string
  model: string
  year: number
  category: string
  city: string
  state: string | null
  daily_rate: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

// GET /cars
export interface CarPage {
  items: Car[]
  next_cursor: string | null
}

export interface CarFilters {
  city: string
  category: string
  min_price: string
  max_price: string
}
