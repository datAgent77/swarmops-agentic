"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

/** Minimal dependency-free tabs. `tabs` is the ordered list of labels; the render
 *  function receives the active label. */
export function Tabs({
  tabs,
  initial,
  children,
}: {
  tabs: string[];
  initial?: string;
  children: (active: string) => React.ReactNode;
}) {
  const [active, setActive] = React.useState(initial ?? tabs[0]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-1 border-b">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActive(tab)}
            className={cn(
              "-mb-px border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              active === tab
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {tab}
          </button>
        ))}
      </div>
      <div>{children(active)}</div>
    </div>
  );
}
