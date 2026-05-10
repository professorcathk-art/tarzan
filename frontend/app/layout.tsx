import type { Metadata } from "next";
import "./globals.css";
import localFont from "next/font/local";
import { Providers } from "@/components/providers";
import { SiteNav } from "@/components/site-nav";
import { Toaster } from "@/components/ui/sonner";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Tarzan — Multi-strategy screener",
  description: "Waterfall and alternative-data screening",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning className={geistSans.variable}>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-background text-foreground`}
      >
        <Providers>
          <SiteNav />
          <main className="pb-16">{children}</main>
          <Toaster richColors position="top-center" />
        </Providers>
      </body>
    </html>
  );
}
