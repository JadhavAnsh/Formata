"use client"

import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"

export function CTA() {
  return (
    <section className="py-32 px-6 relative overflow-hidden">
      {/* Decorative Blur */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/10 blur-[140px] rounded-full pointer-events-none" />

      <div className="max-w-4xl mx-auto text-center relative z-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          <h2 className="text-4xl md:text-7xl font-bold tracking-tight mb-8">
            Stop Cleaning Data. <br />
            <span className="text-muted-foreground">Start Building AI.</span>
          </h2>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <Button
              size="lg"
              className="rounded-full h-16 px-10 text-lg shadow-[0_0_40px_-10px_rgba(255,255,255,0.3)] hover:shadow-primary/40 transition-shadow"
            >
              Get Started with Formata
            </Button>
            <p className="text-sm text-muted-foreground">No credit card required.</p>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
