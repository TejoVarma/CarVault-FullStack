import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import BrowseCars from './BrowseCars'
import { fetchCars } from '../lib/cars'
import type { Car, CarPage } from '../types/car'

vi.mock('../lib/cars', () => ({ fetchCars: vi.fn(), PAGE_SIZE: 12 }))
vi.mock('../components/layout/Header', () => ({ default: () => null }))
vi.mock('../components/layout/Footer', () => ({ default: () => null }))

const mockFetchCars = vi.mocked(fetchCars)

let observerCallback: IntersectionObserverCallback | null = null

class FakeIntersectionObserver {
  constructor(callback: IntersectionObserverCallback) {
    observerCallback = callback
  }
  observe() {}
  disconnect() {}
}

function scrollToBottom() {
  act(() => {
    observerCallback?.([{ isIntersecting: true } as IntersectionObserverEntry], {} as IntersectionObserver)
  })
}

function car(model: string, overrides: Partial<Car> = {}): Car {
  return {
    id: `id-${model}`,
    owner_id: 'owner-1',
    make: 'Maruti',
    model,
    year: 2022,
    category: 'hatchback',
    city: 'Hyderabad',
    state: null,
    daily_rate: '1800.00',
    description: null,
    is_active: true,
    created_at: '2026-11-03T10:00:00',
    updated_at: '2026-11-03T10:00:00',
    ...overrides,
  }
}

function page(items: Car[], next_cursor: string | null = null): CarPage {
  return { items, next_cursor }
}

function renderAt(url = '/cars') {
  return render(
    <MemoryRouter initialEntries={[url]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <BrowseCars />
    </MemoryRouter>,
  )
}

const NO_FILTERS = { city: '', category: '', min_price: '', max_price: '' }

beforeEach(() => {
  mockFetchCars.mockReset()
  observerCallback = null
  vi.stubGlobal('IntersectionObserver', FakeIntersectionObserver)
})

describe('BrowseCars', () => {
  it('shows skeletons while loading, then the cars', async () => {
    mockFetchCars.mockResolvedValue(page([car('Swift', { daily_rate: '1800.00' })]))

    renderAt()

    expect(screen.getByRole('status')).toHaveTextContent('Loading cars…')
    expect(await screen.findByText(/Maruti Swift/)).toBeInTheDocument()
    expect(screen.getByText('₹1,800')).toBeInTheDocument()
    expect(mockFetchCars).toHaveBeenCalledWith(NO_FILTERS, null, expect.any(AbortSignal))
  })

  it('shows an error with a retry that loads the cars', async () => {
    mockFetchCars.mockRejectedValueOnce(new Error('Network Error')).mockResolvedValueOnce(page([car('Swift')]))

    renderAt()
    await userEvent.click(await screen.findByRole('button', { name: 'Retry' }))

    expect(await screen.findByText(/Maruti Swift/)).toBeInTheDocument()
  })

  it('says when there are no cars at all', async () => {
    mockFetchCars.mockResolvedValue(page([]))

    renderAt()

    expect(await screen.findByText('No cars listed yet.', { selector: 'section p' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Clear filters' })).not.toBeInTheDocument()
  })

  it('reads filters from the URL and can clear them', async () => {
    mockFetchCars.mockResolvedValueOnce(page([])).mockResolvedValueOnce(page([car('Swift')]))

    renderAt('/cars?city=Pune&category=suv')

    expect(await screen.findByText('No cars match these filters.', { selector: 'section p' })).toBeInTheDocument()
    expect(mockFetchCars).toHaveBeenCalledWith(
      { ...NO_FILTERS, city: 'Pune', category: 'suv' },
      null,
      expect.any(AbortSignal),
    )

    await userEvent.click(screen.getByRole('button', { name: 'Clear filters' }))

    expect(await screen.findByText(/Maruti Swift/)).toBeInTheDocument()
    expect(mockFetchCars).toHaveBeenLastCalledWith(NO_FILTERS, null, expect.any(AbortSignal))
    expect(screen.getByLabelText('City')).toHaveValue('')
  })

  it('waits for the user to stop typing before searching', async () => {
    mockFetchCars.mockResolvedValue(page([car('Swift')]))
    renderAt()
    await screen.findByText(/Maruti Swift/)

    await userEvent.type(screen.getByLabelText('City'), 'Pune')

    await waitFor(() =>
      expect(mockFetchCars).toHaveBeenLastCalledWith({ ...NO_FILTERS, city: 'Pune' }, null, expect.any(AbortSignal)),
    )
    // One initial load plus one search, not one per letter.
    expect(mockFetchCars).toHaveBeenCalledTimes(2)
  })

  it('changing a filter starts a new search from the first page', async () => {
    mockFetchCars.mockResolvedValue(page([car('Swift')], 'cursor-1'))
    renderAt()
    await screen.findByText(/Maruti Swift/)

    await userEvent.selectOptions(screen.getByLabelText('Category'), 'suv')

    await waitFor(() =>
      expect(mockFetchCars).toHaveBeenLastCalledWith({ ...NO_FILTERS, category: 'suv' }, null, expect.any(AbortSignal)),
    )
  })

  it('loads the next page when the user scrolls to the bottom', async () => {
    mockFetchCars
      .mockResolvedValueOnce(page([car('Swift')], 'cursor-1'))
      .mockResolvedValueOnce(page([car('Dzire')], null))
    renderAt()
    await screen.findByText(/Maruti Swift/)

    scrollToBottom()

    expect(await screen.findByText(/Maruti Dzire/)).toBeInTheDocument()
    expect(screen.getByText(/Maruti Swift/)).toBeInTheDocument()
    expect(mockFetchCars).toHaveBeenLastCalledWith(NO_FILTERS, 'cursor-1', expect.any(AbortSignal))
    expect(screen.getByText("You've seen all 2 cars.")).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Load more' })).not.toBeInTheDocument()
  })

  it('has a Load more button for when scrolling does not trigger', async () => {
    mockFetchCars
      .mockResolvedValueOnce(page([car('Swift')], 'cursor-1'))
      .mockResolvedValueOnce(page([car('Dzire')], null))
    renderAt()

    await userEvent.click(await screen.findByRole('button', { name: 'Load more' }))

    expect(await screen.findByText(/Maruti Dzire/)).toBeInTheDocument()
  })

  it('keeps the cars it has when the next page fails', async () => {
    mockFetchCars
      .mockResolvedValueOnce(page([car('Swift')], 'cursor-1'))
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValueOnce(page([car('Dzire')], null))
    renderAt()
    await screen.findByText(/Maruti Swift/)

    scrollToBottom()

    expect(await screen.findByText("Couldn't load more.")).toBeInTheDocument()
    expect(screen.getByText(/Maruti Swift/)).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))

    expect(await screen.findByText(/Maruti Dzire/)).toBeInTheDocument()
    expect(mockFetchCars).toHaveBeenLastCalledWith(NO_FILTERS, 'cursor-1', expect.any(AbortSignal))
  })

  it('ignores a slow response for filters the user has already changed', async () => {
    let finishSlowRequest: (value: CarPage) => void = () => {}
    mockFetchCars
      .mockImplementationOnce(() => new Promise((resolve) => (finishSlowRequest = resolve)))
      .mockResolvedValueOnce(page([car('Creta', { category: 'suv' })]))

    renderAt()
    await userEvent.selectOptions(screen.getByLabelText('Category'), 'suv')
    expect(await screen.findByText(/Maruti Creta/)).toBeInTheDocument()

    const slowSignal = mockFetchCars.mock.calls[0][2] as AbortSignal
    expect(slowSignal.aborted).toBe(true)

    await act(async () => finishSlowRequest(page([car('Swift')])))

    expect(screen.queryByText(/Maruti Swift/)).not.toBeInTheDocument()
    expect(screen.getByText(/Maruti Creta/)).toBeInTheDocument()
  })

  it('keeps a space the user typed while pausing mid-word', async () => {
    mockFetchCars.mockResolvedValue(page([car('Swift')]))
    renderAt()
    await screen.findByText(/Maruti Swift/)
    const city = screen.getByLabelText('City')

    await userEvent.type(city, 'New ')
    await waitFor(() =>
      expect(mockFetchCars).toHaveBeenLastCalledWith({ ...NO_FILTERS, city: 'New' }, null, expect.any(AbortSignal)),
    )
    await userEvent.type(city, 'Delhi')

    expect(city).toHaveValue('New Delhi')
    await waitFor(() =>
      expect(mockFetchCars).toHaveBeenLastCalledWith({ ...NO_FILTERS, city: 'New Delhi' }, null, expect.any(AbortSignal)),
    )
  })

  it('searches again when a cleared filter is quickly typed back in', async () => {
    mockFetchCars.mockResolvedValueOnce(page([])).mockResolvedValue(page([car('Swift')]))
    renderAt('/cars?city=Pune')
    await userEvent.click(await screen.findByRole('button', { name: 'Clear filters' }))

    await userEvent.type(screen.getByLabelText('City'), 'Pune')

    await waitFor(() =>
      expect(mockFetchCars).toHaveBeenLastCalledWith({ ...NO_FILTERS, city: 'Pune' }, null, expect.any(AbortSignal)),
    )
    expect(mockFetchCars).toHaveBeenCalledTimes(3)
  })

  it('never asks for the old search\'s next page after the filters change', async () => {
    mockFetchCars
      .mockResolvedValueOnce(page([car('Swift')], 'cursor-1'))
      .mockImplementationOnce(() => new Promise(() => {}))
    renderAt()
    await screen.findByText(/Maruti Swift/)

    await userEvent.selectOptions(screen.getByLabelText('Category'), 'suv')
    scrollToBottom()

    expect(mockFetchCars).not.toHaveBeenCalledWith(expect.anything(), 'cursor-1', expect.anything())
  })

  it('keeps the Load more button in place, disabled, while loading', async () => {
    mockFetchCars
      .mockResolvedValueOnce(page([car('Swift')], 'cursor-1'))
      .mockImplementationOnce(() => new Promise(() => {}))
    renderAt()
    const button = await screen.findByRole('button', { name: 'Load more' })

    await userEvent.click(button)

    expect(button).toBeInTheDocument()
    expect(button).toHaveAttribute('aria-disabled', 'true')
    expect(button).toHaveFocus()
  })

  it('moves focus to the City filter after clearing filters', async () => {
    mockFetchCars.mockResolvedValueOnce(page([])).mockResolvedValue(page([car('Swift')]))
    renderAt('/cars?city=Pune')

    await userEvent.click(await screen.findByRole('button', { name: 'Clear filters' }))

    expect(screen.getByLabelText('City')).toHaveFocus()
  })

  it('announces results in one short status message', async () => {
    mockFetchCars.mockResolvedValueOnce(page([car('Swift'), car('Dzire')], 'cursor-1'))
    renderAt()

    expect(await screen.findByText('2 cars shown, more available.')).toBeInTheDocument()
    expect(screen.getAllByRole('status')).toHaveLength(1)
  })
})
