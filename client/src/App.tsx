import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Profile from './pages/Profile'
import BrowseCars from './pages/BrowseCars'
import ProtectedRoute from './components/auth/ProtectedRoute'
import { useAuthStore } from './store/authStore'

function App() {
  const fetchCurrentUser = useAuthStore((state) => state.fetchCurrentUser)

  // On every app load, ask the backend "am I logged in?" — there's no
  // local token to check (it's in an httpOnly cookie we can't read), so
  // this is the only way to know.
  useEffect(() => {
    fetchCurrentUser()
  }, [fetchCurrentUser])

  return (
    <BrowserRouter>
      <Toaster position="top-center" />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/cars" element={<BrowseCars />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/profile" element={<Profile />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
