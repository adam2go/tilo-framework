import type { Metadata } from "next";
import "./canvas.css";

export const metadata: Metadata = { title: "Tilo Canvas — 3D Agent Workspace" };

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
