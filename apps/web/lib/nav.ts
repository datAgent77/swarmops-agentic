import {
  Activity,
  Boxes,
  FileCheck2,
  Fingerprint,
  GitBranch,
  LayoutDashboard,
  ListChecks,
  ScrollText,
  Settings,
  ShieldCheck,
  Workflow,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};

/** Primary control-plane navigation. Pages are placeholders in P00 and get
 *  populated across P01–P14. Order intentionally follows the operator journey:
 *  see the fleet → inspect agents → govern → observe → configure. */
export const NAV_ITEMS: NavItem[] = [
  { label: "Overview", href: "/overview", icon: LayoutDashboard },
  { label: "Agents", href: "/agents", icon: Boxes },
  { label: "Agent Graph", href: "/graph", icon: GitBranch },
  { label: "Executions", href: "/executions", icon: Workflow },
  { label: "Approvals", href: "/approvals", icon: FileCheck2 },
  { label: "Policies", href: "/policies", icon: ListChecks },
  { label: "Security", href: "/security", icon: ShieldCheck },
  { label: "Observability", href: "/observability", icon: Activity },
  { label: "Audit Log", href: "/audit", icon: ScrollText },
  { label: "Integrations", href: "/integrations", icon: Fingerprint },
  { label: "Settings", href: "/settings", icon: Settings },
];
