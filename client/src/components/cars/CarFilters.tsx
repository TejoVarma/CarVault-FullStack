import { forwardRef, useEffect, useRef, useState, type InputHTMLAttributes, type Ref } from 'react'
import { CAR_CATEGORIES, type CarFilters as Filters } from '../../types/car'

export const FILTER_DEBOUNCE_MS = 300

type Props = {
  filters: Filters
  onChange: (name: keyof Filters, value: string) => void
  cityInputRef?: Ref<HTMLInputElement>
}

const trim = (value: string) => value.trim()

export default function CarFilters({ filters, onChange, cityInputRef }: Props) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <DebouncedInput
        ref={cityInputRef}
        label="City"
        placeholder="e.g. Hyderabad"
        value={filters.city}
        normalize={trim}
        onCommit={(value) => onChange('city', value)}
      />
      <label className="flex flex-col gap-1 text-sm font-medium text-ink-800">
        Category
        <select
          className="rounded-lg border border-ink-200 bg-white px-3 py-2 font-normal capitalize"
          value={filters.category}
          onChange={(event) => onChange('category', event.target.value)}
        >
          <option value="">All categories</option>
          {CAR_CATEGORIES.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </label>
      <DebouncedInput
        label="Min price / day"
        type="number"
        min={0}
        inputMode="numeric"
        placeholder="₹"
        value={filters.min_price}
        onCommit={(value) => onChange('min_price', value)}
      />
      <DebouncedInput
        label="Max price / day"
        type="number"
        min={0}
        inputMode="numeric"
        placeholder="₹"
        value={filters.max_price}
        onCommit={(value) => onChange('max_price', value)}
      />
    </div>
  )
}

type DebouncedInputProps = {
  label: string
  value: string
  onCommit: (value: string) => void
  normalize?: (value: string) => string
} & Omit<InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'>

// Shows exactly what the user types, but only reports it once they pause,
// so "Hyderabad" is one search instead of nine.
const DebouncedInput = forwardRef<HTMLInputElement, DebouncedInputProps>(function DebouncedInput(
  { label, value, onCommit, normalize = (text) => text, ...inputProps },
  ref,
) {
  const [draft, setDraft] = useState(value)
  const draftRef = useRef(value)
  const timer = useRef<ReturnType<typeof setTimeout>>()
  const latest = useRef({ value, onCommit, normalize })
  latest.current = { value, onCommit, normalize }

  // The value can change from outside (e.g. "Clear filters"). If the draft
  // already means the same thing ("New " vs "New"), leave the user's text alone.
  useEffect(() => {
    if (latest.current.normalize(draftRef.current) === value) return
    clearTimeout(timer.current)
    draftRef.current = value
    setDraft(value)
  }, [value])

  useEffect(() => () => clearTimeout(timer.current), [])

  function handleChange(text: string) {
    draftRef.current = text
    setDraft(text)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => {
      const { value: committed, onCommit: commit, normalize: clean } = latest.current
      if (clean(text) !== committed) commit(clean(text))
    }, FILTER_DEBOUNCE_MS)
  }

  return (
    <label className="flex flex-col gap-1 text-sm font-medium text-ink-800">
      {label}
      <input
        ref={ref}
        className="rounded-lg border border-ink-200 bg-white px-3 py-2 font-normal"
        value={draft}
        onChange={(event) => handleChange(event.target.value)}
        {...inputProps}
      />
    </label>
  )
})
