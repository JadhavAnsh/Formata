"use client"

import { motion } from "framer-motion"

const steps = [
  {
    title: "Upload",
    description: "Provide your raw dataset from any supported format.",
    number: "01",
  },
  {
    title: "Process",
    description: "Formata cleans, filters, and validates data in real time.",
    number: "02",
  },
  {
    title: "Deploy",
    description: "Download structured output ready for analytics or AI models.",
    number: "03",
  },
]

export function HowItWorks() {
  return (
    <section className="py-24 px-6 border-y border-white/5 bg-white/[0.01]">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row gap-12 items-start">
          <div className="md:w-1/3">
            <motion.h2
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-bold sticky top-32"
            >
              From Raw Data to Clean Structure
            </motion.h2>
          </div>
          <div className="md:w-2/3 space-y-12">
            {steps.map((step, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.2 }}
                className="group relative pl-12 border-l border-white/10 pb-12 last:pb-0"
              >
                <div className="absolute left-0 top-0 -translate-x-1/2 w-8 h-8 rounded-full bg-background border border-white/10 flex items-center justify-center text-[10px] font-mono group-hover:border-primary transition-colors">
                  {step.number}
                </div>
                <h3 className="text-2xl font-bold mb-4">{step.title}</h3>
                <p className="text-muted-foreground text-lg max-w-lg leading-relaxed">{step.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
