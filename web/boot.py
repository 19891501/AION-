"""Entrypoint Render : API AION + MCP."""
from web.app import app

try:
    from web.mcp import router as mcp_router
    app.include_router(mcp_router)
except Exception as exc:  # package partiel
    import sys
    print("mcp router skipped:", exc, file=sys.stderr)
