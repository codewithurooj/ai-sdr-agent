import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Toaster } from "sonner";
import { Sidebar } from "@/components/ui/Sidebar";

const geist = Geist({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI SDR Agent",
  description: "Automated outreach powered by AI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${geist.className} bg-slate-100 min-h-screen`}>
        <Providers>
          <Sidebar />
          <div className="md:pl-56 min-h-screen">
            <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
          </div>
        </Providers>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
