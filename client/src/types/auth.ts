// Mirrors app/schemas/auth.py's UserResponse — keep these in sync manually
// whenever the backend schema changes.
export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone: string | null
  roles: string[]
  is_active: boolean
  created_at: string
  last_login: string | null
  is_customer: boolean
  is_car_owner: boolean
  business_name: string | null
  profile_picture_url: string | null
}

// Mirrors UserRegister
export interface RegisterPayload {
  email: string
  password: string
  first_name: string
  last_name: string
  phone?: string
  initial_role: 'customer' | 'car_owner'
}

export interface LoginPayload {
  email: string
  password: string
}

// Mirrors UserProfile (GET /users/profile)
export interface UserProfile extends User {
  date_of_birth: string | null
  profile_picture_url: string | null
  address_line1: string | null
  address_line2: string | null
  city: string | null
  state: string | null
  postal_code: string | null
  country: string | null
  emergency_contact_name: string | null
  emergency_contact_phone: string | null
  emergency_contact_relationship: string | null
  updated_at: string
}

// Mirrors UserProfileUpdate — all optional, partial update (PATCH)
export interface UserProfileUpdatePayload {
  phone?: string
  date_of_birth?: string
  profile_picture_url?: string
  address_line1?: string
  address_line2?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  emergency_contact_relationship?: string
}

export interface BusinessProfilePayload {
  business_name: string
  business_description?: string
  business_phone: string
  pickup_instructions?: string
}
