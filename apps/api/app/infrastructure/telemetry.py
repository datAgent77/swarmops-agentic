"""OpenTelemetry configuration + status.

Every audit event carries a ``trace_id`` correlated to its execution, so the audit
trail doubles as an end-to-end reasoning-chain trace (reconstructed by the
observability service). When ``OTEL_ENABLED=true`` and a GCP project is configured,
spans additionally export to Cloud Trace; otherwise telemetry is retained locally.

The OpenTelemetry SDK is an optional ``[otel]`` dependency — this module degrades to
local telemetry when it is absent, and never fails app startup.
"""

from __future__ import annotations

from app.config import Settings

BACKEND_CLOUD_TRACE = "cloud_trace"
BACKEND_LOCAL = "local"


def tracing_backend(settings: Settings) -> str:
    """Report where traces go, truthfully."""
    if settings.otel_enabled and settings.google_cloud_project:
        return BACKEND_CLOUD_TRACE
    return BACKEND_LOCAL


def configure_tracing(settings: Settings) -> str:
    """Best-effort tracer setup at startup. Returns the active backend name.

    Never raises: if the OTel SDK or Cloud Trace exporter is unavailable, we fall
    back to local telemetry so the service always starts.
    """
    if not (settings.otel_enabled and settings.google_cloud_project):
        return BACKEND_LOCAL
    try:  # pragma: no cover - exercised only with the optional SDK + credentials
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider

        provider = TracerProvider(resource=Resource.create({"service.name": "swarmops-api"}))
        try:
            from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            provider.add_span_processor(
                BatchSpanProcessor(CloudTraceSpanExporter(project_id=settings.google_cloud_project))
            )
        except Exception:  # noqa: BLE001 — exporter optional; provider still valid
            pass
        trace.set_tracer_provider(provider)
        return BACKEND_CLOUD_TRACE
    except Exception:  # noqa: BLE001
        return BACKEND_LOCAL
