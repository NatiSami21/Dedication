from fastapi import FastAPI
from . import auth

app = FastAPI(title="Academic Assignment Helper")

app.include_router(auth.router)


@app.get("/")
def root():
    return {"message": "Backend running 🚀"}
