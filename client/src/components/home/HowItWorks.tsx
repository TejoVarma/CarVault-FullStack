const steps = [
  { title: 'Sign up', description: 'Create your account as a renter, a car owner, or both.' },
  { title: 'Browse & book', description: 'Find a car that fits, check availability, and book it.' },
  { title: 'Drive', description: 'Pick up the car and go — pay securely through CarVault.' },
]

export default function HowItWorks() {
  return (
    <section className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-center text-ink-900">How it works</h2>
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, i) => (
            <div key={step.title} className="text-center">
              <div className="mx-auto w-11 h-11 rounded-full bg-brand-600 text-white flex items-center justify-center font-bold text-lg">
                {i + 1}
              </div>
              <h3 className="mt-4 text-lg font-semibold text-ink-900">{step.title}</h3>
              <p className="mt-2 text-ink-600">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
