import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Script from "next/script";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MovieBox Pro Unofficial Dashboard",
  description: "A premium dashboard for browsing and streaming MovieBox content.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <Script src="https://cdn.jsdelivr.net/npm/hls.js@latest" strategy="beforeInteractive" />
        <Script src="https://cdn.jsdelivr.net/npm/dashjs@latest/dist/dash.all.min.js" strategy="beforeInteractive" />
      </head>
      <body className={`${inter.className} antialiased selection:bg-yellow-500/30 selection:text-white`}>
        {children}
      </body>
    </html>
  );
}
