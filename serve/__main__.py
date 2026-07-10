"""Allow `python3 -m serve` to start the API server."""
import uvicorn
from .app import app

uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
