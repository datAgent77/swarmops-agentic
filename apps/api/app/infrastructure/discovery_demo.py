"""Demo discovery provider.

Surfaces the CustomerRefundAgent as a newly discovered rogue agent so the governance
lifecycle (discover → assess → policy → quarantine) can run against it. The agent
already exists in the seeded fleet in a benign ACTIVE state; discovery is what pulls
it into review — the seed never pre-quarantines it.
"""

from __future__ import annotations

from app.application.discovery import AgentDiscoveryProvider, DiscoveredAgent


class DemoDiscoveryProvider(AgentDiscoveryProvider):
    async def discover_agents(self) -> list[DiscoveredAgent]:
        return [
            DiscoveredAgent(
                agent_id="agent-customer-refund",
                name="CustomerRefundAgent",
                note="Newly observed rogue v2: financial capability, no approval gate, high autonomy.",
            )
        ]
