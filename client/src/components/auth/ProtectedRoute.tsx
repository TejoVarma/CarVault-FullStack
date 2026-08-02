import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

// Wraps protected routes. Renders nothing meaningful until the initial
// fetchCurrentUser() check (in App.tsx) has resolved — otherwise we'd
// briefly redirect a genuinely logged-in user to /login before we've
// actually heard back from the server about who they are.
export default function ProtectedRoute() {
  const { user, isInitialized } = useAuthStore()

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-slate-500">Loading...</p>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  // Outlet renders whichever child route matched (see App.tsx) — this
  // lets one ProtectedRoute wrap many different protected pages.
  return <Outlet />
}
