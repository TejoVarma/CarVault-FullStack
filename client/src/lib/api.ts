import axios from 'axios'

// Vite only exposes env vars prefixed with VITE_ to client-side code —
// a deliberate safety boundary so server-only secrets in a .env file
// can't accidentally end up bundled into the browser JS.
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  // Sends the httpOnly auth cookie automatically on every request to
  // the backend. Without this, the browser will NOT include cookies
  // on cross-origin requests (client on :3000, backend on :8000 count
  // as different origins) even though the cookie exists.
  withCredentials: true,
})

// Uploaded media (profile photos) is now stored as a full Cloudinary URL
// (see plan_docs/design-decisions.md), so this is mostly a pass-through —
// it still handles a bare relative path gracefully in case any old local
// (/uploads/...) URLs are still sitting in the database from before the
// Cloudinary migration.
export function resolveMediaUrl(url: string | null | undefined): string | null {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  return `${API_URL}${url}`
}
