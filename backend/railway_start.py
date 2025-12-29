#!/usr/bin/env python
"""Start script for Railway deployment."""
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Railway needs 0.0.0.0, not 127.0.0.1
        port=port,
        log_level="info",
    )

