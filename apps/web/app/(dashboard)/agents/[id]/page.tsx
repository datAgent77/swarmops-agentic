import { AgentDetail } from "@/components/agents/agent-detail";

export default function AgentDetailPage({ params }: { params: { id: string } }) {
  return <AgentDetail id={params.id} />;
}
