"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, CircleAlert, Loader2 } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type Status = {
  service: string;
  version: string;
  environment: string;
  demo_mode: boolean;
  category: string;
  tagline: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";

/** Live connectivity check against the backend /api/v1/status endpoint.
 *  Proves the shell talks to the FastAPI service; degrades gracefully. */
export function SystemStatus() {
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [data, setData] = useState<Status | null>(null);

  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/api/v1/status`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((json: Status) => {
        if (!active) return;
        setData(json);
        setState("ok");
      })
      .catch(() => active && setState("error"));
    return () => {
      active = false;
    };
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          {state === "loading" && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
          {state === "ok" && <CheckCircle2 className="h-4 w-4 text-severity-low" />}
          {state === "error" && <CircleAlert className="h-4 w-4 text-severity-critical" />}
          Backend Connectivity
        </CardTitle>
        <CardDescription>
          {state === "ok" && data
            ? `Connected — ${data.service} v${data.version} (${data.environment})`
            : state === "error"
              ? `No response from ${API_URL}. Start the API with "make dev".`
              : "Checking backend status…"}
        </CardDescription>
      </CardHeader>
      {state === "ok" && data && (
        <CardContent className="text-sm text-muted-foreground">
          {data.category} · {data.tagline}
        </CardContent>
      )}
    </Card>
  );
}
