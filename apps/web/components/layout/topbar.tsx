"use client";

import { usePathname } from "next/navigation";

import { NAV_ITEMS } from "@/lib/nav";
import { Badge } from "@/components/ui/badge";

function titleForPath(pathname: string): string {
  const match = NAV_ITEMS.find(
    (item) => pathname === item.href || pathname.startsWith(`${item.href}/`),
  );
  return match?.label ?? "SwarmOps";
}

export function Topbar() {
  const pathname = usePathname();

  return (
    <header className="flex h-16 items-center justify-between border-b bg-background/80 px-6 backdrop-blur">
      <h1 className="text-lg font-semibold tracking-tight">{titleForPath(pathname)}</h1>
      <div className="flex items-center gap-3">
        <Badge variant="secondary">SaitALCorp</Badge>
        <Badge variant="low">Demo Mode</Badge>
      </div>
    </header>
  );
}
