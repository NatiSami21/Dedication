# routes_upload.py
 
import os, shutil, requests
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import database, models
from auth import get_current_user
from dotenv import load_dotenv
#from . import database, models
#from .auth import get_current_user

load_dotenv()

router = APIRouter(prefix="/upload", tags=["Assignment Upload"])
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post("/", status_code=201)
def upload_assignment(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.Student = Depends(get_current_user),
):
    # Check file extension
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed."
        )


    # መጀመሪያ ሌትስ Save the file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ከዛ ሌትስ Record metadata in DB  
    new_assignment = models.Assignment(
        student_id=current_user.id,
        filename=file.filename,
        original_text=None,
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    # ለጥቆ ሌትስ Trigger n8n workflow (webhook) 
    try:
        payload = {
            "assignment_id": new_assignment.id,
            "student_email": current_user.email,
            "student_id": current_user.id,
             "filename": file.filename,
        }
        res = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        res.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger n8n: {e}")

    return {
        "message": "Assignment uploaded successfully and processing started.",
        "assignment_id": new_assignment.id,
        "file_path": os.path.abspath(file_path),
    }
