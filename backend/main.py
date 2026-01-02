from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os
import uuid

# Import config early to trigger environment variable loading and logging
import config

from routes import router
from websocket_manager import manager
from database import init_db

# Configure logging to show in console - FORCE IT
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

# Log immediately to verify logging works
logger.info("="*70)
logger.info("🚀 BACKEND STARTING - Logging configured")
logger.info("="*70)

app = FastAPI()

logger.info("✅ FastAPI app created")

# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    
    # Try EVERY possible way to force output
    msg = f"\n{'='*70}\n🔵 INCOMING REQUEST: {request.method} {request.url.path}\n   Full URL: {request.url}\n   Client: {request.client}\n"
    
    # Write directly to file descriptors
    try:
        os.write(1, msg.encode('utf-8'))
        os.write(2, msg.encode('utf-8'))
    except:
        pass
    
    sys.stdout.write(msg)
    sys.stdout.flush()
    sys.stderr.write(msg)
    sys.stderr.flush()
    
    logger.info(f"\n{'='*70}")
    logger.info(f"🔵 INCOMING REQUEST: {request.method} {request.url.path}")
    logger.info(f"   Full URL: {request.url}")
    logger.info(f"   Client: {request.client}")
    
    if request.url.path == "/process":
        logger.info(f"   ⚠️ This is a /process request - should trigger processing")
    
    try:
        response = await call_next(request)
        elapsed = time.time() - start_time
        msg2 = f"✅ REQUEST COMPLETED: {request.method} {request.url.path} - Status: {response.status_code} - Time: {elapsed:.2f}s\n{'='*70}\n\n"
        
        try:
            os.write(1, msg2.encode('utf-8'))
            os.write(2, msg2.encode('utf-8'))
        except:
            pass
        
        sys.stdout.write(msg2)
        sys.stdout.flush()
        sys.stderr.write(msg2)
        sys.stderr.flush()
        
        logger.info(f"✅ REQUEST COMPLETED: {request.method} {request.url.path} - Status: {response.status_code} - Time: {elapsed:.2f}s")
        logger.info(f"{'='*70}\n")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        msg3 = f"❌ ERROR in request after {elapsed:.2f}s: {str(e)}\n{'='*70}\n\n"
        
        try:
            os.write(1, msg3.encode('utf-8'))
            os.write(2, msg3.encode('utf-8'))
        except:
            pass
        
        sys.stdout.write(msg3)
        sys.stdout.flush()
        sys.stderr.write(msg3)
        sys.stderr.flush()
        
        logger.error(f"❌ ERROR in request after {elapsed:.2f}s: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error(f"{'='*70}\n")
        raise

logger.info("✅ Middleware registered")

# Allow CORS for frontend (local and deployed)
allowed_origins = [
    "http://localhost:4000",
    "http://localhost:3000",
    "http://127.0.0.1:4000",
    "http://127.0.0.1:3000",
]

# Add Vercel domain if provided via environment variable
vercel_url = os.getenv("VERCEL_URL")
if vercel_url:
    allowed_origins.append(f"https://{vercel_url}")
    allowed_origins.append(f"http://{vercel_url}")

# Allow all origins in development, specific origins in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Development: allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include router without prefix
app.include_router(router, tags=["api"])
logger.info("✅ Router included")

# Verify router is actually included
logger.info(f"Router routes count: {len(router.routes)}")
for route in router.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        logger.info(f"  Router route: {list(route.methods)} {route.path}")

# Log all registered routes
logger.info("Registered routes:")
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        logger.info(f"  {list(route.methods)} {route.path}")

logger.info("✅ CORS middleware registered")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    await init_db()
    logger.info("✅ Database initialized")

@app.get("/")
def read_root():
    # Try EVERY possible way to force output
    msg = "="*70 + "\nDEBUG: Root endpoint / called\n" + "="*70 + "\n"
    
    try:
        os.write(1, msg.encode('utf-8'))
        os.write(2, msg.encode('utf-8'))
    except:
        pass
    
    sys.stdout.write(msg)
    sys.stdout.flush()
    sys.stderr.write(msg)
    sys.stderr.flush()
    
    logger.info("="*70)
    logger.info("DEBUG: Root endpoint / called")
    logger.info("="*70)
    
    print("="*70, file=sys.stderr, flush=True)
    print("DEBUG: Root endpoint / called (print stderr)", file=sys.stderr, flush=True)
    print("="*70, file=sys.stderr, flush=True)
    
    return {"message": "AI Sheet Automation Backend is running"}

@app.get("/health")
def health_check():
    logger.info("DEBUG: Health check endpoint called")
    return {"status": "ok", "message": "Backend is healthy"}

@app.post("/test")
def test_endpoint(request: Request):
    logger.info("DEBUG: /test endpoint called")
    return {"status": "ok", "message": "Test endpoint works"}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await manager.send_personal_message({"type": "pong", "data": data}, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
