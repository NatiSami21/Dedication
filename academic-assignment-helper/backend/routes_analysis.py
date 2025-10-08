from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import database, models
from .auth import get_current_user

router = APIRouter(prefix="/analysis", tags=["Analysis Results"])

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
