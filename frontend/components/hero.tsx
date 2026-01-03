"use client"

import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { ArrowRight, Play } from "lucide-react"

const previewBarWidths = ["82%", "71%", "93%", "64%"] as const

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.3,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] as const },
  },
}

export function Hero() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center pt-32 pb-20 px-6 overflow-hidden">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff10_1px,transparent_1px),linear-gradient(to_bottom,#ffffff10_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)]" />
      </div>

      {/* Animated Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-primary/10 blur-[120px] rounded-full opacity-30 pointer-events-none" />

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 text-center max-w-4xl"
      >
        <motion.div
          variants={itemVariants}
          className="mb-6 inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 text-[10px] uppercase tracking-widest text-muted-foreground"
        >
          <span className="w-1 h-1 bg-primary rounded-full animate-pulse" />
          The Future of Data Structure
        </motion.div>

        <motion.h1
          variants={itemVariants}
          className="text-5xl md:text-8xl font-bold tracking-tight mb-8 text-balance bg-gradient-to-b from-foreground to-foreground/70 bg-clip-text text-transparent"
        >
          Turn Messy Data into AI‑Ready Intelligence
        </motion.h1>

        <motion.p
          variants={itemVariants}
          className="text-lg md:text-xl text-muted-foreground mb-12 max-w-2xl mx-auto leading-relaxed"
        >
          Formata automatically cleans, normalizes, validates, and structures scattered data—so your AI models start
          with reliable inputs, not chaos.
        </motion.p>

        <motion.div variants={itemVariants} className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button size="lg" className="rounded-full h-14 px-8 text-base group">
            Start Structuring Data
            <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Button>
          <Button
            size="lg"
            variant="outline"
            className="rounded-full h-14 px-8 text-base bg-white/5 hover:bg-white/10 border-white/10"
          >
            <Play className="mr-2 w-4 h-4 fill-current" />
            View Demo
          </Button>
        </motion.div>
      </motion.div>

      {/* Visual Component Preview */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 1, ease: [0.16, 1, 0.3, 1] as const }}
        className="mt-24 relative w-full max-w-5xl mx-auto aspect-[16/9] rounded-2xl border border-white/10 bg-card overflow-hidden shadow-2xl"
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(255,255,255,0.05)_0%,transparent_50%)]" />
        <div className="flex h-full">
          <aside className="w-1/4 border-r border-white/5 p-6 hidden md:block">
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="h-2 w-full bg-white/5 rounded-full"
                  style={{ width: previewBarWidths[i - 1] }}
                />
              ))}
            </div>
          </aside>
          <main className="flex-1 p-8">
            <div className="flex items-center justify-between mb-12">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-primary/20" />
                <div className="h-4 w-32 bg-white/10 rounded" />
              </div>
              <div className="h-8 w-8 rounded-full border border-white/10" />
            </div>
            <div className="grid grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="aspect-square rounded-xl bg-white/[0.02] border border-white/5 p-4 flex flex-col justify-end"
                >
                  <div className="h-2 w-full bg-white/10 rounded mb-2" />
                  <div className="h-2 w-2/3 bg-white/5 rounded" />
                </div>
              ))}
            </div>
          </main>
        </div>
      </motion.div>
    </section>
  )
}
