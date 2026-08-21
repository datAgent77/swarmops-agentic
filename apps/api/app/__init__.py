"""SwarmOps API — Enterprise Agent Control Plane.

Layered backend:

    api             HTTP surface (thin FastAPI route handlers)
    application     use-cases / orchestration (added in later phases)
    domain          pure business models and rules (added in later phases)
    infrastructure  adapters: persistence, external services (added later)

P00 only ships the foundation: health/status endpoints and the layer skeleton.
"""

__version__ = "0.0.0"
