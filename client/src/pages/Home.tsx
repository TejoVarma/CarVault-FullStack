import Header from '../components/layout/Header'
import Footer from '../components/layout/Footer'
import Hero from '../components/home/Hero'
import HowItWorks from '../components/home/HowItWorks'
import Features from '../components/home/Features'
import DualSignupCta from '../components/home/DualSignupCta'

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Hero />
        <HowItWorks />
        <Features />
        <DualSignupCta />
      </main>
      <Footer />
    </div>
  )
}
