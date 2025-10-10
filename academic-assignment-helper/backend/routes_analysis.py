# backend/routes_analysis.py
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
import re, json, time
import database, models
from auth import get_current_user
from ai_utils import analyze_assignment_text  #Friendli.ai integration
import json
from database import SessionLocal

from vector_utils import embed_academic_sources  #Hugging Face integration

router = APIRouter(prefix="/analysis", tags=["Analysis Results"])

 
def sanitize_text(text: str) -> str:
    """Remove NULL and invisible characters from text."""
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text or "").strip()


# GET analysis 
@router.get("/{assignment_id}")
def get_analysis(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Student = Depends(get_current_user),
):
    """Return latest analysis result or status."""
    assignment = (
        db.query(models.Assignment)
        .filter_by(id=assignment_id, student_id=current_user.id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    result = (
        db.query(models.AnalysisResult)
        .filter_by(assignment_id=assignment_id)
        .first()
    )

    if not result:
        return {"status": "processing", "message": "Analysis not completed yet."}

    # --- Safe JSON decoding helpers ---
    def try_json_load(value):
        if not value:
            return None
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except Exception:
            return value  # fallback to raw string if broken JSON

    suggested_sources = try_json_load(result.suggested_sources)
    citation_recommendations = try_json_load(result.citation_recommendations)

    return {
        "status": "done",
        "assignment": assignment.filename,
        "topic": suggested_sources.get("topic") if isinstance(suggested_sources, dict) else None,
        "plagiarism_score": result.plagiarism_score,
        "suggested_sources": suggested_sources,
        "research_suggestions": result.research_suggestions,
        "citation_recommendations": citation_recommendations,
    }


# POST /analysis/ack this is will be Triggerd by n8n webhook calls this after text extraction
@router.post("/ack")
async def receive_text_ack(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
):
    """
    Receives extracted text from n8n and triggers Friendli.ai analysis asynchronously.
    """
    data = await request.json()
    assignment_id = data.get("assignment_id")
    extracted_text = data.get("text", "")
    student_email = data.get("student_email")

    if not assignment_id or not extracted_text:
        raise HTTPException(status_code=400, detail="Invalid payload from n8n")

    cleaned_text = sanitize_text(extracted_text)

    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Storing raw text
    assignment.original_text = cleaned_text
    db.commit()
    db.refresh(assignment)

    #Triggering background AI analysis and this part will be non blocking
    background_tasks.add_task(run_ai_analysis, assignment_id, cleaned_text)

    return {"message": "Text received; analysis started.", "assignment_id": assignment_id}


# this is oviosly background AI analysis processing
def run_ai_analysis(assignment_id: int, text: str):
    db = SessionLocal()

    try:
        print(f"[AI] Starting analysis for assignment_id={assignment_id}")
        ai_result = analyze_assignment_text(text)

        if "error" in ai_result:
            print(f"[AI] Analysis failed for {assignment_id}: {ai_result['error']}")
            return

        # trying extracting fields safely
        topic = ai_result.get("topic")
        level = ai_result.get("academic_level")
        plagiarism = ai_result.get("plagiarism_summary")
        sources = ai_result.get("suggested_sources")
        citation = ai_result.get("citation_recommendations")
        insights = ai_result.get("key_insights")

        # Safe JSON serialization
        def safe_json(value):
            try:
                return json.dumps(value) if value is not None else None
            except Exception:
                return json.dumps(str(value))

        # Checking if analysis already exists
        existing_result = db.query(models.AnalysisResult).filter_by(assignment_id=assignment_id).first()

        if existing_result:
            print(f"[AI] Updating existing analysis for assignment_id={assignment_id}")
            existing_result.suggested_sources = safe_json(sources)
            existing_result.plagiarism_score = None
            existing_result.flagged_sections = safe_json(None)
            existing_result.research_suggestions = (
                "\n".join(insights) if isinstance(insights, list) else (insights or plagiarism)
            )
            existing_result.citation_recommendations = safe_json(citation)
            existing_result.confidence_score = 0.9
        else:
            print(f"[AI] Creating new analysis record for assignment_id={assignment_id}")
            new_result = models.AnalysisResult(
                assignment_id=assignment_id,
                suggested_sources=safe_json(sources),
                plagiarism_score=None,
                flagged_sections=safe_json(None),
                research_suggestions="\n".join(insights) if isinstance(insights, list) else (insights or plagiarism),
                citation_recommendations=safe_json(citation),
                confidence_score=0.9,
            )
            db.add(new_result)

        db.commit()
        print(f"[AI] Analysis stored successfully for assignment_id={assignment_id}")

    except Exception as e:
        print(f"[AI] Exception during analysis for assignment_id={assignment_id}: {e}")
    finally:
        db.close()

# I tried manual run
@router.post("/run/{assignment_id}")
def run_analysis_manual(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Student = Depends(get_current_user),
):
    """Allow manual trigger of analysis for testing."""
    assignment = (
        db.query(models.Assignment)
        .filter_by(id=assignment_id, student_id=current_user.id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    text = assignment.original_text or ""
    if not text:
        raise HTTPException(status_code=400, detail="No text found for this assignment")

    run_ai_analysis(assignment_id, text)
    return {"message": f"Manual AI analysis triggered for assignment {assignment_id}"}

@router.post("/embed-sources")
def embed_sources_endpoint(db: Session = Depends(database.get_db)):
    """Manual trigger to generate embeddings for academic sources."""
    embed_academic_sources(db)
    return {"message": "Embedding process completed"}