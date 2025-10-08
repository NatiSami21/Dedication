from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Academic Assignment Helper backend running 🚀"}
