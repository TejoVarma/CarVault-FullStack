import { FiShield, FiUsers, FiDollarSign } from 'react-icons/fi'

const features = [
  {
    icon: FiShield,
    title: 'Secure by design',
    description: 'Passwords are hashed, sessions use secure cookies, every booking is protected.',
  },
  {
    icon: FiUsers,
    title: 'Verified owners',
    description: 'Every car owner on CarVault is a verified account, not an anonymous listing.',
  },
  {
    icon: FiDollarSign,
    title: 'Fair pricing',
    description: 'No hidden fees — owners set their price, renters see the real total upfront.',
  },
]

export default function Features() {
  return (
    <section className="py-20 bg-ink-50">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-center text-ink-900">Why CarVault</h2>
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="w-11 h-11 rounded-lg bg-brand-100 flex items-center justify-center">
                <feature.icon className="w-6 h-6 text-brand-600" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-ink-900">{feature.title}</h3>
              <p className="mt-2 text-ink-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
