"""Infrastructure layer — adapters for persistence and external services.

Concrete repository implementations, event buses, Google Cloud clients, and the
Gemini/ADK integration live here in later phases. The domain never imports from
this package directly; it depends on interfaces.
"""
