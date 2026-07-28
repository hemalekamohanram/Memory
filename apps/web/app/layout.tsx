import type { Metadata } from "next";
import Link from "next/link";
import { Activity, Archive, Blocks, Bot, BrainCircuit, Database, GitBranch, LayoutDashboard } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Engram — Persistent Memory OS",
  description: "Governed engineering memory for AI agents",
};

const nav = [
  ["/", "Overview", LayoutDashboard],
  ["/workspace", "Agent workspace", Bot],
  ["/memories", "Memory explorer", BrainCircuit],
  ["/timeline", "Timeline", GitBranch],
  ["/consolidation", "Consolidation", Blocks],
  ["/architecture", "Architecture", Database],
  ["/mcp", "MCP Inspector", Activity],
] as const;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <aside className="sidebar">
            <div className="brand"><span className="brandMark"><Archive size={18} /></span><span>Engram</span></div>
            <p className="eyebrow">MEMORY OPERATING SYSTEM</p>
            <nav aria-label="Primary navigation">
              {nav.map(([href, label, Icon]) => <Link href={href} key={href}><Icon size={17} /><span>{label}</span></Link>)}
            </nav>
            <div className="modeCard"><span className="statusDot" /><div><strong>Mock mode</strong><small>Deterministic & offline</small></div></div>
          </aside>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
