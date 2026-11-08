"""Compatibility ASGI entry point; use app.factory for imports without an instance."""
from app.factory import create_app

app = create_app()
