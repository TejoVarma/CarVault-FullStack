import { useState, FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import Header from '../components/layout/Header'
import FormField, { inputClass } from '../components/ui/FormField'
import { useAuthStore } from '../store/authStore'
import { registerSchema, getFieldErrors } from '../lib/validation'

export default function Register() {
  const [searchParams] = useSearchParams()
  const initialRole = searchParams.get('role') === 'car_owner' ? 'car_owner' : 'customer'

  const [role, setRole] = useState<'customer' | 'car_owner'>(initialRole)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [phone, setPhone] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)

  const register = useAuthStore((state) => state.register)
  const navigate = useNavigate()

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const fieldErrors = await getFieldErrors(registerSchema, {
      first_name: firstName,
      last_name: lastName,
      email,
      password,
      phone,
      role,
    })
    setErrors(fieldErrors)
    if (Object.keys(fieldErrors).length > 0) return

    setSubmitting(true)
    try {
      await register({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        ...(phone ? { phone } : {}),
        initial_role: role,
      })
      toast.success('Account created!')
      navigate('/profile')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Registration failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-ink-50">
      <Header />
      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
          <h1 className="text-2xl font-bold text-ink-900 text-center">Sign up</h1>

          <div className="flex rounded-lg border border-ink-200 overflow-hidden">
            <button
              type="button"
              onClick={() => setRole('customer')}
              className={`flex-1 py-2 text-sm font-medium transition-colors ${
                role === 'customer' ? 'bg-brand-600 text-white' : 'bg-white text-ink-600'
              }`}
            >
              Rent a car
            </button>
            <button
              type="button"
              onClick={() => setRole('car_owner')}
              className={`flex-1 py-2 text-sm font-medium transition-colors ${
                role === 'car_owner' ? 'bg-brand-600 text-white' : 'bg-white text-ink-600'
              }`}
            >
              List my car
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <FormField label="First name" required error={errors.first_name}>
              <input
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className={inputClass(!!errors.first_name)}
              />
            </FormField>
            <FormField label="Last name" required error={errors.last_name}>
              <input
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className={inputClass(!!errors.last_name)}
              />
            </FormField>
          </div>

          <FormField label="Email" required error={errors.email}>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass(!!errors.email)}
            />
          </FormField>

          <FormField
            label="Phone"
            required={role === 'car_owner'}
            error={errors.phone}
            hint={role === 'customer' ? 'Optional' : undefined}
          >
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className={inputClass(!!errors.phone)}
            />
          </FormField>

          <FormField
            label="Password"
            required
            error={errors.password}
            hint="8+ characters, with uppercase, lowercase, and a digit"
          >
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass(!!errors.password)}
            />
          </FormField>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2.5 rounded-lg bg-brand-600 text-white font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
          >
            {submitting ? 'Creating account...' : 'Sign up'}
          </button>

          <p className="text-center text-sm text-ink-600">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-600 font-medium hover:underline">
              Log in
            </Link>
          </p>
        </form>
      </main>
    </div>
  )
}
