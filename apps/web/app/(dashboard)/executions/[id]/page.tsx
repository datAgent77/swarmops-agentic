import { ExecutionDetail } from "@/components/executions/execution-detail";

export default function ExecutionDetailPage({ params }: { params: { id: string } }) {
  return <ExecutionDetail id={params.id} />;
}
