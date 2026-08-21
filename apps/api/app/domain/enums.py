"""Domain enumerations. All are string-valued so they serialize cleanly over JSON
and read the same in the database, the API, and the UI."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    SECURITY_OFFICER = "SECURITY_OFFICER"
    BUSINESS_APPROVER = "BUSINESS_APPROVER"
    FINANCE_APPROVER = "FINANCE_APPROVER"
    DEVELOPER = "DEVELOPER"


class AgentStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    QUARANTINED = "QUARANTINED"
    RETIRED = "RETIRED"


class AutonomyLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ToolType(str, Enum):
    API = "API"
    MCP = "MCP"
    DATABASE = "DATABASE"
    AGENT = "AGENT"
    SAAS = "SAAS"
    INTERNAL_SERVICE = "INTERNAL_SERVICE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DependencyTargetType(str, Enum):
    TOOL = "TOOL"
    AGENT = "AGENT"
    DATABASE = "DATABASE"
    EXTERNAL_API = "EXTERNAL_API"
    MODEL = "MODEL"
    MCP = "MCP"


class Relationship(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    CALL = "CALL"
    DELEGATE = "DELEGATE"


class RecommendedAction(str, Enum):
    ALLOW = "ALLOW"
    MONITOR = "MONITOR"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    SUSPEND = "SUSPEND"
    QUARANTINE = "QUARANTINE"


class PolicyAction(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    QUARANTINE = "QUARANTINE"
    REDACT = "REDACT"
    LOG_ONLY = "LOG_ONLY"


class ExecutionStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class AuditActorType(str, Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    AGENT = "AGENT"


class SecurityCategory(str, Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    PII_LEAKAGE = "PII_LEAKAGE"
    EXTERNAL_TRANSMISSION = "EXTERNAL_TRANSMISSION"
    TOOL_POISONING = "TOOL_POISONING"


class ProposalDecision(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class IntegrationStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DEMO_MODE = "DEMO_MODE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    ERROR = "ERROR"
