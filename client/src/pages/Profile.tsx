import { useEffect, useRef, useState, FormEvent, ChangeEvent } from 'react'
import toast from 'react-hot-toast'
import { AxiosError } from 'axios'
import Header from '../components/layout/Header'
import FormField, { inputClass } from '../components/ui/FormField'
import { api, resolveMediaUrl } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import {
  changePasswordSchema,
  businessProfileSchema,
  profileUpdateSchema,
  getFieldErrors,
} from '../lib/validation'
import type { UserProfile, UserProfileUpdatePayload } from '../types/auth'

function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return fallback
}

export default function Profile() {
  const authUser = useAuthStore((state) => state.user)
  const setUser = useAuthStore((state) => state.fetchCurrentUser)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  // Photo
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadingPhoto, setUploadingPhoto] = useState(false)

  // Editable profile fields
  const [phone, setPhone] = useState('')
  const [city, setCity] = useState('')
  const [state, setState] = useState('')
  const [country, setCountry] = useState('')
  const [emergencyName, setEmergencyName] = useState('')
  const [profileErrors, setProfileErrors] = useState<Record<string, string>>({})
  const [savingProfile, setSavingProfile] = useState(false)

  // Password change
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [passwordErrors, setPasswordErrors] = useState<Record<string, string>>({})
  const [changingPassword, setChangingPassword] = useState(false)

  // Become car owner
  const [businessName, setBusinessName] = useState('')
  const [businessPhone, setBusinessPhone] = useState('')
  const [ownerErrors, setOwnerErrors] = useState<Record<string, string>>({})
  const [becomingOwner, setBecomingOwner] = useState(false)

  function loadProfile() {
    return api
      .get<UserProfile>('/users/profile')
      .then((res) => {
        setProfile(res.data)
        setPhone(res.data.phone ?? '')
        setCity(res.data.city ?? '')
        setState(res.data.state ?? '')
        setCountry(res.data.country ?? '')
        setEmergencyName(res.data.emergency_contact_name ?? '')
      })
      .catch(() => toast.error('Could not load profile'))
  }

  useEffect(() => {
    loadProfile().finally(() => setLoading(false))
  }, [])

  async function handleSaveProfile(e: FormEvent) {
    e.preventDefault()
    const fieldErrors = await getFieldErrors(profileUpdateSchema, {
      phone,
      emergency_contact_phone: '', // not editable here yet, keeps schema happy
    })
    setProfileErrors(fieldErrors)
    if (Object.keys(fieldErrors).length > 0) return

    setSavingProfile(true)
    try {
      const payload: UserProfileUpdatePayload = {}
      if (phone) payload.phone = phone
      if (city) payload.city = city
      if (state) payload.state = state
      if (country) payload.country = country
      if (emergencyName) payload.emergency_contact_name = emergencyName

      const res = await api.patch<UserProfile>('/users/profile', payload)
      setProfile(res.data)
      toast.success('Profile updated')
    } catch (error) {
      toast.error(errorMessage(error, 'Could not update profile'))
    } finally {
      setSavingProfile(false)
    }
  }

  async function handleChangePassword(e: FormEvent) {
    e.preventDefault()
    const fieldErrors = await getFieldErrors(changePasswordSchema, {
      current_password: currentPassword,
      new_password: newPassword,
    })
    setPasswordErrors(fieldErrors)
    if (Object.keys(fieldErrors).length > 0) return

    setChangingPassword(true)
    try {
      await api.put('/users/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      toast.success('Password changed')
      setCurrentPassword('')
      setNewPassword('')
    } catch (error) {
      toast.error(errorMessage(error, 'Could not change password'))
    } finally {
      setChangingPassword(false)
    }
  }

  async function handleBecomeOwner(e: FormEvent) {
    e.preventDefault()
    const fieldErrors = await getFieldErrors(businessProfileSchema, {
      business_name: businessName,
      business_phone: businessPhone,
    })
    setOwnerErrors(fieldErrors)
    if (Object.keys(fieldErrors).length > 0) return

    setBecomingOwner(true)
    try {
      await api.post('/auth/become-car-owner', {
        business_name: businessName,
        business_phone: businessPhone,
      })
      toast.success('You are now a car owner!')
      await loadProfile()
    } catch (error) {
      toast.error(errorMessage(error, 'Could not upgrade account'))
    } finally {
      setBecomingOwner(false)
    }
  }

  async function handlePhotoChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      toast.error('Please choose an image file')
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Photo must be smaller than 5MB')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    setUploadingPhoto(true)
    try {
      const res = await api.post<UserProfile>('/users/profile/photo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setProfile(res.data)
      // Header shows the photo too — it reads from the auth store, so
      // refresh that from the server rather than duplicating update logic.
      await setUser()
      toast.success('Photo updated')
    } catch (error) {
      toast.error(errorMessage(error, 'Could not upload photo'))
    } finally {
      setUploadingPhoto(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-ink-400">Loading profile...</p>
        </main>
      </div>
    )
  }

  const photoUrl = resolveMediaUrl(profile?.profile_picture_url)

  return (
    <div className="min-h-screen flex flex-col bg-ink-50">
      <Header />
      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-8 sm:py-10 space-y-6 sm:space-y-8">
        <div className="flex items-center gap-4">
          <div className="relative shrink-0">
            {photoUrl ? (
              <img
                src={photoUrl}
                alt=""
                className="w-20 h-20 rounded-full object-cover border border-ink-200"
              />
            ) : (
              <div className="w-20 h-20 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-2xl font-bold">
                {authUser?.first_name[0]}
              </div>
            )}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingPhoto}
              className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-brand-600 text-white text-xs font-bold flex items-center justify-center border-2 border-ink-50 hover:bg-brand-700 disabled:opacity-50"
              aria-label="Change photo"
            >
              {uploadingPhoto ? '…' : '+'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handlePhotoChange}
              className="hidden"
            />
          </div>
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-ink-900 truncate">
              {authUser?.full_name}
            </h1>
            <p className="text-ink-600 truncate">{authUser?.email}</p>
            <div className="mt-2 flex gap-2 flex-wrap">
              {authUser?.roles.map((role) => (
                <span
                  key={role}
                  className="px-2 py-1 text-xs font-medium rounded-full bg-ink-200 text-ink-700"
                >
                  {role}
                </span>
              ))}
            </div>
          </div>
        </div>

        <form
          onSubmit={handleSaveProfile}
          className="bg-white rounded-xl p-5 sm:p-6 space-y-4 shadow-sm"
        >
          <h2 className="text-lg font-semibold text-ink-900">Profile details</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField label="Phone" error={profileErrors.phone}>
              <input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className={inputClass(!!profileErrors.phone)}
              />
            </FormField>
            <FormField label="City">
              <input
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className={inputClass()}
              />
            </FormField>
            <FormField label="State">
              <input
                value={state}
                onChange={(e) => setState(e.target.value)}
                className={inputClass()}
              />
            </FormField>
            <FormField label="Country">
              <input
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className={inputClass()}
              />
            </FormField>
          </div>
          <FormField label="Emergency contact name">
            <input
              value={emergencyName}
              onChange={(e) => setEmergencyName(e.target.value)}
              className={inputClass()}
            />
          </FormField>
          <button
            type="submit"
            disabled={savingProfile}
            className="px-4 py-2 rounded-lg bg-brand-600 text-white font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
          >
            {savingProfile ? 'Saving...' : 'Save changes'}
          </button>
        </form>

        <form
          onSubmit={handleChangePassword}
          className="bg-white rounded-xl p-5 sm:p-6 space-y-4 shadow-sm"
        >
          <h2 className="text-lg font-semibold text-ink-900">Change password</h2>
          <FormField label="Current password" required error={passwordErrors.current_password}>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className={inputClass(!!passwordErrors.current_password)}
            />
          </FormField>
          <FormField
            label="New password"
            required
            error={passwordErrors.new_password}
            hint="8+ characters, with uppercase, lowercase, and a digit"
          >
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className={inputClass(!!passwordErrors.new_password)}
            />
          </FormField>
          <button
            type="submit"
            disabled={changingPassword}
            className="px-4 py-2 rounded-lg bg-brand-600 text-white font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
          >
            {changingPassword ? 'Changing...' : 'Change password'}
          </button>
        </form>

        {profile && !profile.is_car_owner && (
          <form
            onSubmit={handleBecomeOwner}
            className="bg-white rounded-xl p-5 sm:p-6 space-y-4 shadow-sm border border-brand-200"
          >
            <h2 className="text-lg font-semibold text-ink-900">List your car</h2>
            <p className="text-sm text-ink-600">
              Become a car owner to start listing your vehicles on CarVault.
            </p>
            <FormField label="Business name" required error={ownerErrors.business_name}>
              <input
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                className={inputClass(!!ownerErrors.business_name)}
              />
            </FormField>
            <FormField label="Business phone" required error={ownerErrors.business_phone}>
              <input
                value={businessPhone}
                onChange={(e) => setBusinessPhone(e.target.value)}
                className={inputClass(!!ownerErrors.business_phone)}
              />
            </FormField>
            <button
              type="submit"
              disabled={becomingOwner}
              className="px-4 py-2 rounded-lg bg-brand-600 text-white font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
            >
              {becomingOwner ? 'Upgrading...' : 'Become a car owner'}
            </button>
          </form>
        )}
      </main>
    </div>
  )
}
