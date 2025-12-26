#!/usr/bin/env python
"""Simple script to run the FastAPI server with debug logging."""
import uvicorn

if __name__ == "__main__":
    # Use import string for reload to work
    # Try binding to localhost explicitly instead of 0.0.0.0
    uvicorn.run(
        "main:app",
        host="127.0.0.1",  # Changed from 0.0.0.0 to 127.0.0.1
        port=9000,
        log_level="info",
        reload=True
    )

