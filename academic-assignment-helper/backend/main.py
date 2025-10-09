# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
#from . import auth
#from .routes_upload import router as upload_router
#from .routes_analysis import router as analysis_router
# Absolute imports (works in Docker with WORKDIR=/app)
import auth
from routes_upload import router as upload_router
from routes_analysis import router as analysis_router

app = FastAPI(
    title="Academic Assignment Helper",
    swagger_ui_parameters={"persistAuthorization": True}
)

# for frontend or n8n access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(upload_router)
app.include_router(analysis_router)

@app.get("/")
def root():
    return {"message": "Backend running 🚀"}
