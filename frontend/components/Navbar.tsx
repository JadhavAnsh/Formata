"use client"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { motion } from "framer-motion"
import { Menu, Moon, Sun, User, LogOut } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"
import { useAuth } from "@/context/AuthContext"

type Theme = "light" | "dark"

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light"

  const stored = localStorage.getItem("theme")
  if (stored === "light" || stored === "dark") return stored

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

export function Navbar() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme)
  const { user, loading, logout } = useAuth()

  useEffect(() => {
    localStorage.setItem("theme", theme)
    document.documentElement.classList.toggle("dark", theme === "dark")
  }, [theme])

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark"
    setTheme(next)
  }

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 bg-background/80 backdrop-blur-md border-b border-white/5"
    >
      <div className="flex items-center gap-4 sm:gap-8">
        <Link href="/" className="text-xl font-bold tracking-tighter flex items-center gap-2">
          <div className="w-6 h-6 bg-primary rounded-sm italic rotate-45" />
          FORMATA
        </Link>
        
      </div>
      <div className="flex items-center gap-2 sm:gap-4">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="rounded-full"
          aria-label="Toggle theme"
          onClick={toggleTheme}
        >
          {theme === "dark" ? <Sun /> : <Moon />}
        </Button>
        <div className="hidden sm:flex items-center gap-3">
          {loading ? (
            <div className="w-20 h-8 bg-muted animate-pulse rounded-lg" />
          ) : user ? (
            <>
              <div className="flex items-center gap-2 text-sm text-muted-foreground mr-2">
                <User size={16} />
                <span>{user.name}</span>
              </div>
              <Button size="sm" variant="ghost" className="rounded-lg px-4" onClick={logout}>
                <LogOut size={16} className="mr-2" />
                Logout
              </Button>
              <Button size="sm" variant="ghost" className="rounded-lg px-4" asChild>
                <Link href="/dashboard">Dashboard</Link>
              </Button>
              <Button size="sm" className="rounded-lg px-4" asChild>
                <Link href="/ingest">Ingest</Link>
              </Button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Log in
              </Link>
              <Button size="sm" className="rounded-lg px-4" asChild>
                <Link href="/register">Register</Link>
              </Button>
            </>
          )}
          <Button size="sm" variant="outline" className="rounded-lg px-4" asChild>
            <Link href="/convert">Convert</Link>
          </Button>
        </div>

        <div className="sm:hidden">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button type="button" variant="ghost" size="icon" className="rounded-full" aria-label="Open menu">
                <Menu />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-44">
              {user ? (
                <>
                  <DropdownMenuItem className="flex items-center gap-2 font-medium">
                    <User size={16} />
                    <span>{user.name}</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href="/dashboard">Dashboard</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/ingest">Ingest Data</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/convert">Convert Files</Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={logout} className="text-destructive">
                    <LogOut size={16} className="mr-2" />
                    Logout
                  </DropdownMenuItem>
                </>
              ) : (
                <>
                  <DropdownMenuItem asChild>
                    <Link href="/login">Login</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/register">Register</Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href="/convert">Convert Files</Link>
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </motion.header>
  )
}
