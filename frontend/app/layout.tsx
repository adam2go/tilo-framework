import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tilo ROAM Workspace",
  description: "ROAM-based AI-native SaaS agent framework"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
