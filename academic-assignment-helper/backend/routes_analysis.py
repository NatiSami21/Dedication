# backend/routes_analysis.py
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import re, json, time
import database, models
from auth import get_current_user
from ai_utils import analyze_assignment_text  # Friendli.ai or Hugging Face integration
from database import SessionLocal, get_db
from vector_utils import embed_academic_sources
import vector_utils
from plagiarism_utils import detect_plagiarism

import requests, os
N8N_NOTIFY_URL = os.getenv("N8N_NOTIFY_URL")

router = APIRouter(prefix="/analysis", tags=["Analysis Results"])



# ------------------------------------------------------------
# service of sanitizing text input
# ------------------------------------------------------------
def sanitize_text(text: str) -> str:
    """Remove NULL and invisible characters from text."""
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text or "").strip()


# ------------------------------------------------------------
# GET /analysis/{assignment_id}
# ------------------------------------------------------------
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

    # Safe JSON decoding helper
    def try_json_load(value):
        if not value:
            return None
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except Exception:
            return value  # fallback

    suggested_sources = try_json_load(result.suggested_sources)
    citation_recommendations = try_json_load(result.citation_recommendations)
    flagged_sections = try_json_load(result.flagged_sections)

    return {
        "status": "done",
        "assignment": assignment.filename,
        "plagiarism_score": result.plagiarism_score,
        "flagged_sections": flagged_sections,
        "suggested_sources": suggested_sources,
        "research_suggestions": result.research_suggestions,
        "citation_recommendations": citation_recommendations,
    }


# ------------------------------------------------------------
# POST /analysis/ack  → obviously triggered by n8n webhook
# ------------------------------------------------------------
@router.post("/ack")
async def receive_text_ack(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
):
    """
    Receives extracted text from n8n and triggers RAG + plagiarism analysis.
    """
    data = await request.json()
    assignment_id = data.get("assignment_id")
    extracted_text = data.get("text", "")
    student_id = data.get("student_id")
    student_email = data.get("student_email")

    if not assignment_id or not extracted_text:
        raise HTTPException(status_code=400, detail="Invalid payload from n8n")

    cleaned_text = sanitize_text(extracted_text)

    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id and models.Assignment.student_id == student_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.original_text = cleaned_text
    db.commit()
    db.refresh(assignment)

    # Non-blocking background RAG analysis
    background_tasks.add_task(run_ai_analysis_rag, assignment_id, cleaned_text)

    return {"message": "Text received; analysis started.", "assignment_id": assignment_id}


# ------------------------------------------------------------
# Background RAG + Plagiarism Analysis
# ------------------------------------------------------------
def run_ai_analysis_rag(assignment_id: int, text: str):
    db = SessionLocal()
    try:
        print(f"[AI] Starting RAG + plagiarism analysis for assignment_id={assignment_id}")

        # First detecting plagiarism
        plagiarism_result = detect_plagiarism(db, text, top_k=3, similarity_threshold=0.6)
        plagiarism_score = plagiarism_result["plagiarism_score"]
        flagged_sections = plagiarism_result["flagged_sections"]

        # Keza collecting top source titles for RAG
        top_sources = [fs["source_title"] for fs in flagged_sections[:3]] if flagged_sections else []

        # Ketlo building RAG prompt 
        rag_prompt = f"""
        You are an AI academic assistant. Analyze the following student assignment.

        Assignment:
        {text[:2000]}

        Top Related Academic Sources:
        {top_sources}

        Plagiarism Score: {plagiarism_score}%

        Provide a structured JSON with:
        {{
            "summary": "...",
            "key_insights": ["..."],
            "improvement_suggestions": ["..."],
            "citations_to_add": ["Title 1", "Title 2"]
        }}
        """

        # Letiko runing AI summarization (Friendli wey Hugging Face)
        ai_output = analyze_assignment_text(rag_prompt)
        if not ai_output or "error" in ai_output:
            print(f"[AI] Error in RAG summarization: {ai_output}")
            return

        # Bestemecheresha -> result
        def safe_json(value):
            try:
                return json.dumps(value) if value is not None else None
            except Exception:
                return json.dumps(str(value))

        existing_result = db.query(models.AnalysisResult).filter_by(assignment_id=assignment_id).first()
        if existing_result:
            print(f"[AI] Updating existing record for assignment_id={assignment_id}")
            existing_result.plagiarism_score = plagiarism_score
            existing_result.flagged_sections = safe_json(flagged_sections)
            existing_result.suggested_sources = safe_json(top_sources)
            existing_result.research_suggestions = safe_json(ai_output.get("key_insights"))
            existing_result.citation_recommendations = safe_json(ai_output.get("citations_to_add"))
            existing_result.confidence_score = 0.9
        else:
            print(f"[AI] Creating new record for assignment_id={assignment_id}")
            new_result = models.AnalysisResult(
                assignment_id=assignment_id,
                plagiarism_score=plagiarism_score,
                flagged_sections=safe_json(flagged_sections),
                suggested_sources=safe_json(top_sources),
                research_suggestions=safe_json(ai_output.get("key_insights")),
                citation_recommendations=safe_json(ai_output.get("citations_to_add")),
                confidence_score=0.9,
            )
            db.add(new_result)

        db.commit()
        print(f"[AI] Stored full RAG + plagiarism analysis for assignment_id={assignment_id}")

        # Notify n8n that the analysis is completed
        notify_n8n_analysis_done(db, assignment_id)

    except Exception as e:
        print(f"[AI] Exception during RAG analysis: {e}")
    finally:
        db.close()


# ------------------------------------------------------------
# Manual test triggering
# ------------------------------------------------------------
@router.post("/run/{assignment_id}")
def run_analysis_manual(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Student = Depends(get_current_user),
):
    """Allow manual RAG analysis trigger."""
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

    run_ai_analysis_rag(assignment_id, text)
    return {"message": f"Manual RAG analysis triggered for assignment {assignment_id}"}


# ------------------------------------------------------------
# Helper endpoints
# ------------------------------------------------------------
@router.post("/embed-sources")
def embed_sources_endpoint(db: Session = Depends(database.get_db)):
    """Manually regenerate embeddings for academic sources."""
    embed_academic_sources(db)
    return {"message": "Embedding process completed."}


@router.post("/index-sources")
def create_vector_index(db: Session = Depends(get_db)):
    """Create pgvector index for academic sources."""
    vector_utils.index_academic_sources(db)
    return {"message": "Vector index created or already exists."}


@router.get("/search-similar")
def search_similar(query: str = Query(..., description="Text to find similar sources for"),
                   top_k: int = 5,
                   db: Session = Depends(get_db), 
                   current_user = Depends(get_current_user)):
    """Search semantically similar academic sources."""
    results = vector_utils.search_similar_sources(db, query, top_k)
    return {"results": results}

@router.post("/notify-n8n/{assignment_id}")
def run_notify_n8n_analysis_done_manual(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Student = Depends(get_current_user),
):
    """Manual trigger to notify n8n that analysis is done. By calling notify_n8n_analysis_done """
    notify_n8n_analysis_done(db, assignment_id)
    return {"message": f"n8n notified for assignment {assignment_id}"}



def notify_n8n_analysis_done(db: Session, assignment_id: int):
    
    """Notify n8n that the analysis is completed and ready."""
    
    N8N_NOTIFY_URL = os.getenv("N8N_NOTIFY_URL")

    try:
        # Fetch student + analysis data
        assignment = db.query(models.Assignment).filter_by(id=assignment_id).first()
        student = db.query(models.Student).filter_by(id=assignment.student_id).first()
        result = db.query(models.AnalysisResult).filter_by(assignment_id=assignment_id).first()

        if not assignment or not student or not result:
            print(f"[AI] Skipping n8n notify — missing data for assignment_id={assignment_id}")
            return

        payload = {
            "assignment_id": assignment_id,
            "filename": assignment.filename,
            "student_id": student.id,
            "student_id_self": student.student_id,
            "student_email": student.email,
            "full_name": student.full_name,
            "plagiarism_score": result.plagiarism_score,
            "flagged_sections": json.loads(result.flagged_sections or "[]"),
            "suggested_sources": json.loads(result.suggested_sources or "[]"),
            "research_suggestions": json.loads(result.research_suggestions or "[]"),
            "citation_recommendations": json.loads(result.citation_recommendations or "[]"),
            "status": "done"
        }

        res = requests.post(N8N_NOTIFY_URL, json=payload, timeout=10)
        res.raise_for_status()
        print(f"[AI] Notified n8n for assignment_id={assignment_id}")

    except Exception as e:
        print(f"[AI] Failed to notify n8n: {e}")