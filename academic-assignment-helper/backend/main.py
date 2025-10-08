from fastapi import FastAPI
from . import auth
from .routes_upload import router as upload_router
from .routes_analysis import router as analysis_router

app = FastAPI(title="Academic Assignment Helper", swagger_ui_parameters={"persistAuthorization": True})

app.include_router(auth.router)
app.include_router(upload_router)
app.include_router(analysis_router)


@app.get("/")
def root():
    return {"message": "Backend running 🚀"}
