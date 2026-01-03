"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { Database, Zap, ShieldAlert, Cpu } from "lucide-react"

const features = [
  {
    title: "Multi‑Source Ingestion",
    description: "Upload CSV, JSON, Excel, or Markdown files—Formata handles the rest.",
    icon: Database,
  },
  {
    title: "Smart Normalization",
    description: "Automatic type conversion, date parsing, and value standardization.",
    icon: Zap,
  },
  {
    title: "Real‑Time Error Visibility",
    description: "See validation issues instantly without stopping the pipeline.",
    icon: ShieldAlert,
  },
  {
    title: "AI‑Ready Outputs",
    description: "Export clean datasets or vector embeddings, ready for ML workflows.",
    icon: Cpu,
  },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const },
  },
}

export function Features() {
  return (
    <section id="product" className="py-24 px-6 relative">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-5xl font-bold mb-4">Everything Your Data Needs—Automated</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Our platform provides the essential tools to transform raw, unstructured data into high-quality assets for
            your AI models.
          </p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {features.map((feature, idx) => (
            <motion.div key={idx} variants={itemVariants}>
              <Card className="p-8 h-full bg-card hover:bg-white/[0.04] border-white/5 transition-all duration-300 group hover:-translate-y-1 hover:shadow-2xl hover:shadow-primary/5">
                <div className="mb-6 inline-flex items-center justify-center w-12 h-12 rounded-lg bg-white/5 text-primary group-hover:scale-110 transition-transform">
                  <feature.icon className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{feature.description}</p>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
