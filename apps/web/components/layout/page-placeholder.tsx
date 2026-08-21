import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

/** Stub surface used by nav pages that later phases will populate. Keeps the
 *  operational shell navigable in P00 without faking business features. */
export function PagePlaceholder({
  title,
  description,
  phase,
}: {
  title: string;
  description: string;
  phase: string;
}) {
  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{title}</CardTitle>
          <Badge variant="outline">{phase}</Badge>
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">
        This surface is part of the SwarmOps control plane shell. Functionality lands in a later
        build phase; the navigation, layout, and contracts are in place now.
      </CardContent>
    </Card>
  );
}
