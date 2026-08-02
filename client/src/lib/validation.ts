import * as yup from 'yup'

// Schemas mirror the validation rules actually enforced by the backend
// (schemas/auth.py's @validator methods). The backend remains the source
// of truth and re-validates everything regardless — these exist purely so
// the frontend can give instant feedback instead of a round trip to find
// out a password is too weak.

const passwordRule = yup
  .string()
  .required('Password is required')
  .min(8, 'Password must be at least 8 characters long')
  .matches(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .matches(/[a-z]/, 'Password must contain at least one lowercase letter')
  .matches(/[0-9]/, 'Password must contain at least one digit')

// Phone isn't a simple regex here — the backend strips non-digit characters
// and checks length, so mirror that exactly rather than rejecting valid
// input like "(555) 123-4567" that a stricter pattern would flag.
const phoneDigitsTest = (value: string | undefined) =>
  !value || value.replace(/\D/g, '').length >= 10

export const loginSchema = yup.object({
  email: yup.string().required('Email is required').email('Enter a valid email'),
  password: yup.string().required('Password is required'),
})

export const registerSchema = yup.object({
  first_name: yup.string().required('First name is required').min(2, 'First name must be at least 2 characters'),
  last_name: yup.string().required('Last name is required').min(2, 'Last name must be at least 2 characters'),
  email: yup.string().required('Email is required').email('Enter a valid email'),
  password: passwordRule,
  role: yup.string().oneOf(['customer', 'car_owner']).required(),
  phone: yup
    .string()
    .test('phone-digits', 'Phone number must contain at least 10 digits', phoneDigitsTest)
    .when('role', {
      is: 'car_owner',
      then: (schema) => schema.required('Phone number is required for car owners'),
    }),
})

export const changePasswordSchema = yup.object({
  current_password: yup.string().required('Current password is required'),
  new_password: passwordRule,
})

export const businessProfileSchema = yup.object({
  business_name: yup
    .string()
    .required('Business name is required')
    .min(2, 'Business name must be at least 2 characters'),
  business_phone: yup
    .string()
    .required('Business phone is required')
    .test('phone-digits', 'Phone number must contain at least 10 digits', phoneDigitsTest),
})

export const profileUpdateSchema = yup.object({
  phone: yup
    .string()
    .test('phone-digits', 'Phone number must contain at least 10 digits', phoneDigitsTest),
  emergency_contact_phone: yup
    .string()
    .test('phone-digits', 'Phone number must contain at least 10 digits', phoneDigitsTest),
})

// Runs a yup schema against a set of values and returns a flat field->message
// map instead of throwing, so form components can render errors per-field.
export async function getFieldErrors<T extends yup.AnyObject>(
  schema: yup.ObjectSchema<T>,
  values: unknown,
): Promise<Record<string, string>> {
  try {
    await schema.validate(values, { abortEarly: false })
    return {}
  } catch (err) {
    if (err instanceof yup.ValidationError) {
      const errors: Record<string, string> = {}
      for (const inner of err.inner) {
        if (inner.path && !errors[inner.path]) errors[inner.path] = inner.message
      }
      return errors
    }
    throw err
  }
}
