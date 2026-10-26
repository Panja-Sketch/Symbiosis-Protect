import type { Metadata, Viewport } from "next";
import { Fraunces, Inter } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/app-shell";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "optional" });
const display = Fraunces({ subsets: ["latin"], variable: "--font-display", display: "optional" });

export const metadata: Metadata = {
  title: "Symbiosis Protect — Arizona demo",
  description: "Loss-prevention guidance, coverage in plain language, and live Arizona weather alerts.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1 };

export const dynamic = "force-dynamic";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${display.variable}`}>
      <body className="font-sans antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
