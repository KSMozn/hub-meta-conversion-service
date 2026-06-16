"""Service-layer exceptions. Routers translate these into HTTP responses."""

from __future__ import annotations


class ServiceError(Exception):
    """Base for service-layer errors."""


class NotFoundError(ServiceError):
    pass


class ConflictError(ServiceError):
    pass


class UpstreamError(ServiceError):
    """The dependency (Meta) failed in a way we can't paper over."""
