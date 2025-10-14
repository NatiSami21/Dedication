# main.py
from contextlib import asynccontextmanager # NEW IMPORT
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
#from . import auth
#from .routes_upload import router as upload_router
#from .routes_analysis import router as analysis_router
# Absolute imports (works in Docker with WORKDIR=/app)
import auth
from routes_upload import router as upload_router
from routes_analysis import router as analysis_router

from startup_loader import load_sample_sources # auto load sample academic sources
import asyncio 

# -------------------------------------------------------------
# Lifespan Event Handler 
# -------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the application.
    The code before 'yield' runs on startup.
    """
    # STARTUP LOGIC 
    print("="*50)
    print("[APP STARTUP] Initializing FastAPI Lifespan Handler...")
     
    print("[APP STARTUP] Starting database sample data loader...")

    try:
        await asyncio.to_thread(load_sample_sources)
        print("[APP STARTUP] Database sample data loading finished.")
    except Exception as e:
        print(f"[APP STARTUP ERROR] Failed to run load_sample_sources: {e}")
    
    print("="*50)
    
    yield  # Control is handed over to FastAPI to run the app
    
    # SHUTDOWN LOGIC
    print("[APP SHUTDOWN] Backend server shutting down...")


# -------------------------------------------------------------
# Initializing FastAPI
# -------------------------------------------------------------
# Passing above lifespan handler to the FastAPI constructor
app = FastAPI(
    title="Academic Assignment Helper",
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan
)

# -------------------------------------------------------------
# CORS Middleware
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Including Routers
# -------------------------------------------------------------
app.include_router(auth.router)
app.include_router(upload_router)
app.include_router(analysis_router)

# -------------------------------------------------------------
# Root Endpoint
# -------------------------------------------------------------
@app.get("/")
def root():
    """
    Simple health-check endpoint to verify server is running.
    """
    return {"message": "Backend running —> Academic Assignment Helper"}