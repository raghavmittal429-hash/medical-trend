"""
Backend package marker for medical-trend.

This file makes the `backend` directory a Python package so
`uvicorn backend.main:app` can import the module correctly on hosts
that require a package marker (e.g. some WSGI/ASGI deploy platforms).
"""

__all__ = []
