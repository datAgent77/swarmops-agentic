"""Agent discovery port.

A discovery provider surfaces agents present in the environment that the control
plane should onboard and govern. The demo provider (infrastructure) returns the
rogue CustomerRefundAgent v2; a real provider would query the Agent Registry (P13).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class DiscoveredAgent:
    agent_id: str
    name: str
    note: str = ""


class AgentDiscoveryProvider(ABC):
    @abstractmethod
    async def discover_agents(self) -> list[DiscoveredAgent]: ...
