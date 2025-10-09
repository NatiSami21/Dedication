# routes_analysis.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import re
import database, models  
from auth import get_current_user 
#from . import database, models
#from .auth import get_current_user

router = APIRouter(prefix="/analysis", tags=["Analysis Results"])

def sanitize_text(text: str) -> str:
    # Remove NULLs and any other non-printable control characters
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text or "").strip()

@router.get("/{assignment_id}")
def get_analysis(assignment_id: int,
                 db: Session = Depends(database.get_db),
                 current_user: models.Student = Depends(get_current_user)):

    assignment = db.query(models.Assignment).filter_by(
        id=assignment_id, student_id=current_user.id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    result = db.query(models.AnalysisResult).filter_by(
        assignment_id=assignment_id
    ).first()

    if not result:
        return {"status": "processing", "message": "Analysis not completed yet."}

    return {
        "status": "done",
        "assignment": assignment.filename,
        "plagiarism_score": result.plagiarism_score,
        "suggested_sources": result.suggested_sources,
        "research_suggestions": result.research_suggestions,
        "citation_recommendations": result.citation_recommendations,
    }

@router.post("/ack")
async def receive_text_ack(request: Request, db: Session = Depends(database.get_db)):
    """
    Receives extracted text data from n8n and updates the assignment record.
    Also creates an initial AnalysisResult entry to mark processing completion.
    """
    data = await request.json()
    assignment_id = data.get("assignment_id")
    extracted_text = data.get("text", "")
    student_email = data.get("student_email")

    if not assignment_id or not extracted_text:
        raise HTTPException(status_code=400, detail="Invalid payload from n8n")

    # ✅ Clean the text
    cleaned_text = sanitize_text(extracted_text)

    # ✅ Find the assignment
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # ✅ Update assignment text
    assignment.original_text = cleaned_text
    db.commit()
    db.refresh(assignment)

    # ✅ Create or update an analysis result placeholder
    analysis = db.query(models.AnalysisResult).filter(models.AnalysisResult.assignment_id == assignment_id).first()
    if not analysis:
        analysis = models.AnalysisResult(
            assignment_id=assignment_id,
            plagiarism_score=0.0,
            suggested_sources={},
            flagged_sections=[],
            research_suggestions="Initial extraction complete. Awaiting AI analysis.",
            citation_recommendations="Pending.",
            confidence_score=0.0,
        )
        db.add(analysis)
    else:
        analysis.research_suggestions = "Updated after text extraction."
    db.commit()

    return {
        "message": "Text extraction received and analysis record created",
        "assignment_id": assignment_id,
    }
