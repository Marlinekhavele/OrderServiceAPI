"""API package.

Keep this module lightweight to avoid package-level imports that can
trigger circular import errors. Endpoint modules are imported directly
by `app.api.api` (they expose `router` objects) so we avoid importing
them here.
"""

__all__ = []
