import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { FiMenu, FiX } from 'react-icons/fi'
import { useAuthStore } from '../../store/authStore'
import { resolveMediaUrl } from '../../lib/api'

export default function Header() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  async function handleLogout() {
    setMenuOpen(false)
    await logout()
    toast.success('Logged out')
    navigate('/')
  }

  return (
    <header className="border-b border-ink-200 bg-ink-50/80 backdrop-blur sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link
          to="/"
          className="text-xl font-extrabold text-ink-900 tracking-tight"
          onClick={() => setMenuOpen(false)}
        >
          Car<span className="text-brand-600">Vault</span>
        </Link>

        {/* Desktop nav — hidden below md, shown at md and up */}
        <nav className="hidden md:flex items-center gap-6">
          <Link to="/cars" className="text-ink-600 hover:text-ink-900 font-medium">
            Browse Cars
          </Link>

          {user ? (
            <>
              <Link
                to="/profile"
                className="flex items-center gap-2 text-ink-600 hover:text-ink-900 font-medium"
              >
                {user.profile_picture_url ? (
                  <img
                    src={resolveMediaUrl(user.profile_picture_url)!}
                    alt=""
                    className="w-8 h-8 rounded-full object-cover border border-ink-200"
                  />
                ) : (
                  <span className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-sm font-semibold">
                    {user.first_name[0]}
                  </span>
                )}
                {user.full_name}
              </Link>
              <button
                onClick={handleLogout}
                className="px-4 py-2 rounded-lg bg-ink-100 text-ink-700 hover:bg-ink-200 font-medium transition-colors"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-ink-600 hover:text-ink-900 font-medium">
                Login
              </Link>
              <Link
                to="/register"
                className="px-4 py-2 rounded-lg bg-brand-600 text-white hover:bg-brand-700 font-medium transition-colors"
              >
                Sign Up
              </Link>
            </>
          )}
        </nav>

        {/* Mobile hamburger toggle — hidden at md and up */}
        <button
          className="md:hidden p-2 text-ink-700"
          onClick={() => setMenuOpen((open) => !open)}
          aria-label="Toggle menu"
        >
          {menuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
        </button>
      </div>

      {/* Mobile dropdown menu */}
      {menuOpen && (
        <nav className="md:hidden border-t border-ink-200 bg-white px-4 py-4 flex flex-col gap-4">
          <Link to="/cars" className="text-ink-600 font-medium" onClick={() => setMenuOpen(false)}>
            Browse Cars
          </Link>
          {user ? (
            <>
              <Link
                to="/profile"
                className="text-ink-600 font-medium"
                onClick={() => setMenuOpen(false)}
              >
                {user.full_name}
              </Link>
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2 rounded-lg bg-ink-100 text-ink-700 font-medium"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-ink-600 font-medium"
                onClick={() => setMenuOpen(false)}
              >
                Login
              </Link>
              <Link
                to="/register"
                className="px-4 py-2 rounded-lg bg-brand-600 text-white font-medium text-center"
                onClick={() => setMenuOpen(false)}
              >
                Sign Up
              </Link>
            </>
          )}
        </nav>
      )}
    </header>
  )
}
