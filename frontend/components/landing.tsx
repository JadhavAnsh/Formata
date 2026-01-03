import { Navbar } from "@/components/Navbar"
import { Hero } from "@/components/hero"
import { Features } from "@/components/features"
import { HowItWorks } from "@/components/how-it-works"
import { CTA } from "@/components/cta"

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />
      <Hero />

      {/* Differentiation Section */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-4xl md:text-5xl font-bold mb-6">Built for Speed, Built for Scale</h2>
              <p className="text-muted-foreground text-lg mb-8 leading-relaxed">
                Formata keeps your data pipeline transparent, resilient, and fast—so teams focus on insights, not
                cleanup.
              </p>
              <div className="space-y-4">
                {["No manual scripts", "No fragile pipelines", "No hidden failures"].map((point) => (
                  <div key={point} className="flex items-center gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                    <span className="font-medium">{point}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="aspect-square bg-gradient-to-br from-white/5 to-transparent rounded-3xl border border-white/10 flex items-center justify-center p-12 overflow-hidden">
                <div className="grid grid-cols-4 gap-4 w-full h-full opacity-40">
                  {Array.from({ length: 16 }).map((_, i) => (
                    <div
                      key={i}
                      className="bg-white/10 rounded-lg animate-pulse"
                      style={{ animationDelay: `${i * 0.1}s` }}
                    />
                  ))}
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-32 h-32 rounded-full border border-primary/20 flex items-center justify-center">
                    <div className="w-24 h-24 rounded-full border border-primary/40 flex items-center justify-center">
                      <div className="w-16 h-16 rounded-full bg-primary/20 blur-sm" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Features />
      <HowItWorks />
      <CTA />

      <footer className="py-12 px-6 border-t border-white/5 text-center">
        <p className="text-muted-foreground text-sm">© 2026 Formata AI. All rights reserved.</p>
      </footer>
    </main>
  )
}
