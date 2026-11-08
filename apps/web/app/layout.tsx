import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "RankForge AI — Search Intelligence. Engineered for Growth.",
  description:
    "Multi-tenant SEO intelligence and automation platform enabling businesses and agencies to analyze technical SEO, discover organic search opportunities, and safely deploy approved optimizations.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-rf-bg text-rf-text antialiased min-h-screen selection:bg-rf-crimson selection:text-white">
        {children}
      </body>
    </html>
  );
}
