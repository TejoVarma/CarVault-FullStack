import { ReactNode } from 'react'

interface FormFieldProps {
  label: string
  required?: boolean
  error?: string | null
  hint?: string
  children: ReactNode
}

// Consistent required-asterisk + inline error/hint text across every form
// in the app. The actual <input> is passed as children so this works for
// text, email, password, tel, select, etc. without duplicating markup.
export default function FormField({ label, required, error, hint, children }: FormFieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-ink-800">
        {label}
        {required && (
          <span className="text-brand-600 ml-0.5" aria-label="required">
            *
          </span>
        )}
      </label>
      <div className="mt-1">{children}</div>
      {error ? (
        <p className="mt-1 text-xs text-red-600">{error}</p>
      ) : hint ? (
        <p className="mt-1 text-xs text-ink-400">{hint}</p>
      ) : null}
    </div>
  )
}

// Shared input styling, with an error state — used directly on every
// <input>/<select> so validation state is visually obvious, not just text.
export function inputClass(hasError?: boolean): string {
  return `w-full rounded-lg border px-3 py-2 text-ink-900 placeholder:text-ink-400 focus:outline-none focus:ring-2 focus:ring-brand-500/50 ${
    hasError ? 'border-red-400 focus:border-red-400' : 'border-ink-200 focus:border-brand-500'
  }`
}
