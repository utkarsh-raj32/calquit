import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import ActionQueue from "@/components/ActionQueue";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ParcelPilot AI",
  description: "AI Support System for ParcelPilot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-white text-black min-h-screen`}>
        {children}
        <ActionQueue />
      </body>
    </html>
  );
}
