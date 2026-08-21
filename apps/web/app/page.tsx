import { redirect } from "next/navigation";

export default function Home() {
  // The control plane opens on the fleet Overview; there is no marketing page.
  redirect("/overview");
}
