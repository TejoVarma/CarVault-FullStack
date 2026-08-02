export default function Footer() {
  return (
    <footer className="border-t border-ink-200 bg-white">
      <div className="max-w-6xl mx-auto px-4 py-8 text-center text-sm text-ink-400">
        © {new Date().getFullYear()} CarVault. Built as a learning project.
      </div>
    </footer>
  )
}
