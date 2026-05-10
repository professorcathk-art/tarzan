"use client";

import Link from "next/link";

import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";


const links = [

  { href: "/", label: "Home" },

  { href: "/screener", label: "Screener" },

  { href: "/templates", label: "Templates" },

  { href: "/settings", label: "Settings" },

  { href: "/auth/login", label: "Sign in" },


];

export function SiteNav() {

  const pathname = usePathname();

  return (

    <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">

      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">

        <Link href="/" className="text-lg font-semibold tracking-tight">

          Tarzan

        </Link>

        <nav className="flex flex-wrap gap-3 text-sm text-muted-foreground">

          {links.map(({ href, label }) => (

            <Link

              key={href}

              href={href}



              className={cn(
                "hover:text-foreground transition-colors",
                pathname === href && "text-foreground font-medium",
              )}
            >
              {label}

            </Link>

          ))}
        </nav>

      </div>

    </header>

  );

}

