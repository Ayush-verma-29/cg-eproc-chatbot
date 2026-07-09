# backend/app/main.py
import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import json
import time
import uuid
import io
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from fastapi.concurrency import run_in_threadpool

from app.core.rag_engine import get_rag_engine
from app.core.config import settings
from app.core.session import session_manager
from app.services.analytics_service import analytics_service

app = FastAPI(
    title="CG e-Procurement Chatbot API",
    description="AI-powered RAG chatbot with separated vendor/government knowledge bases",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve PDF source documents statically ─────────────────────────────────────
# Both govt_rules and vendor_manuals directories are mounted under /docs.
# PDFs can then be linked as: /docs/govt/<filename>#page=N
app.mount("/docs/govt", StaticFiles(directory=str(settings.GOVT_PDF_DIR)), name="govt_docs")
app.mount("/docs/vendor", StaticFiles(directory=str(settings.VENDOR_PDF_DIR)), name="vendor_docs")
app.mount("/static", StaticFiles(directory=str(settings.BASE_DIR / "frontend")), name="static")

# Request/Response Models
class RoleRequest(BaseModel):
    role: str = "unified"  # "vendor", "government_officer", or "unified" (default)
    session_id: Optional[str] = None

class RoleResponse(BaseModel):
    session_id: str
    role: str
    message: str

class ChatRequest(BaseModel):
    question: str
    session_id: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    source_refs: Optional[List[Dict[str, Any]]] = None  # [{file, pages:[int], url, category}]
    rule_citations: Optional[List[str]] = None
    detected_language: str
    role_used: str
    timestamp: str

class FeedbackRequest(BaseModel):
    log_id: str
    feedback: str

# ==================== API Endpoints ====================

@app.get("/")
async def root():
    return {
        "message": "CG e-Procurement Chatbot API v2",
        "endpoints": {
            "start_session": "POST /api/v1/start (body: {'role': 'vendor' or 'government_officer'})",
            "chat": "POST /api/v1/chat (body: {'question': '...', 'session_id': '...'})",
            "health": "GET /health",
            "stats": "GET /api/v1/stats"
        }
    }



@app.post("/api/v1/start", response_model=RoleResponse)
async def start_session(request: RoleRequest):
    """Start a new session with specified role (unified, vendor, or government_officer)"""
    valid_roles = ["vendor", "government_officer", "unified"]
    if request.role not in valid_roles:
        request.role = "unified"  # default fallback
    
    session_id = session_manager.create_session(request.role)
    
    role_message = {
        "vendor": "You are now chatting as a VENDOR. I'll help you with portal usage, bid submission, registration, and troubleshooting.",
        "government_officer": "You are now chatting as a GOVERNMENT OFFICER. I'll help you with procurement rules, GFR guidelines, and compliance.",
        "unified": "Welcome to the CG e-Procurement Assistant. Ask me anything about procurement rules, vendor registration, tenders, or GFR guidelines."
    }
    
    return RoleResponse(
        session_id=session_id,
        role=request.role,
        message=role_message.get(request.role, "Session started")
    )

def safe_next(generator):
    try:
        return next(generator)
    except StopIteration:
        return None

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """Send a question to the chatbot and receive a stream of tokens"""
    # Get session
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please start a new session with /start")
    
    role = session.get("role")
    if not role:
        raise HTTPException(status_code=400, detail="No role assigned to session")
    
    async def event_generator():
        try:
            start_time = time.time()
            log_id = str(uuid.uuid4())
            
            rag_engine = get_rag_engine()

            # Fetch last 3 conversation turns from session for context
            conversation_history = session.get("history", [])[-3:]

            gen = rag_engine.ask_stream(
                question=request.question,
                role=role,
                session_id=request.session_id,
                conversation_history=conversation_history
            )
            
            accumulated_answer = ""
            
            while True:
                event = await run_in_threadpool(safe_next, gen)
                if event is None:
                    break
                if event["type"] == "start":
                    event["log_id"] = log_id  # Inject log_id for frontend to send feedback later
                elif event["type"] == "token":
                    accumulated_answer += event["text"]
                yield f"data: {json.dumps(event)}\n\n"
            
            if accumulated_answer:
                session_manager.add_to_history(request.session_id, request.question, accumulated_answer)
                # Log the query and calculate elapsed time
                elapsed_time = time.time() - start_time
                await run_in_threadpool(analytics_service.log_query, request.question, role, elapsed_time, log_id, request.session_id, accumulated_answer)
                
        except Exception as e:
            print(f"Error in event_generator: {e}")
            yield f"data: {json.dumps({'type': 'token', 'text': f'Error during generation: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
 
@app.post("/api/v1/chat/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit user satisfaction feedback for a query response"""
    success = await run_in_threadpool(
        analytics_service.submit_feedback, 
        request.log_id, 
        request.feedback
    )
    if not success:
        raise HTTPException(status_code=404, detail="Query log entry not found or invalid feedback value")

    # Dynamic Learning: Ingest satisfied (liked) query-answer pair into ChromaDB vector database
    if request.feedback == "satisfied":
        try:
            logs = await run_in_threadpool(analytics_service._read_logs)
            entry = next((e for e in logs if e.get("id") == request.log_id), None)
            if entry and entry.get("query") and entry.get("response"):
                from langchain.schema import Document
                doc = Document(
                    page_content=f"Question: {entry['query']}\nAnswer: {entry['response']}",
                    metadata={"source": "Learned satisfied Q&As", "topics": "learned,faq"}
                )
                rag_engine = get_rag_engine()
                if entry.get("role") == "government_officer":
                    govt_store = rag_engine.vector_store_manager.get_govt_store()
                    # Use log_id as the document ID to prevent duplicate chunks on multiple clicks
                    await run_in_threadpool(govt_store.add_documents, [doc], ids=[request.log_id])
                    if hasattr(govt_store, "persist"):
                        await run_in_threadpool(govt_store.persist)
                else:
                    vendor_store = rag_engine.vector_store_manager.get_vendor_store()
                    await run_in_threadpool(vendor_store.add_documents, [doc], ids=[request.log_id])
                    if hasattr(vendor_store, "persist"):
                        await run_in_threadpool(vendor_store.persist)
                print(f"💡 eProcurement Chatbot learned thumbs-up query: '{entry['query']}' successfully.")
        except Exception as e:
            print(f"Failed to ingest thumbs-up query into ChromaDB: {e}")

    return {"message": "Feedback recorded successfully"}

@app.get("/api/v1/admin/analytics")
async def get_analytics():
    """Retrieve system usage and satisfaction metrics for the admin dashboard"""
    metrics = await run_in_threadpool(analytics_service.get_metrics)
    return metrics

@app.get("/health")
async def health_check():
    """Check system health"""
    import requests
    
    rag_engine = get_rag_engine()
    status = await run_in_threadpool(rag_engine.get_status)
    
    # Check Ollama in thread pool to prevent event loop blocking
    def check_ollama():
        try:
            response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                return "healthy"
        except:
            pass
        return "unhealthy"
        
    ollama_status = await run_in_threadpool(check_ollama)
    
    return {
        "status": "healthy" if ollama_status == "healthy" else "degraded",
        "ollama": ollama_status,
        "vector_store": status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/stats")
async def get_stats():
    """Get system statistics"""
    rag_engine = get_rag_engine()
    status = await run_in_threadpool(rag_engine.get_status)
    
    def count_pdfs():
        return (
            len(list(settings.VENDOR_PDF_DIR.glob("*.pdf"))),
            len(list(settings.GOVT_PDF_DIR.glob("*.pdf")))
        )
    vendor_count, govt_count = await run_in_threadpool(count_pdfs)
    
    return {
        "rag_engine": status,
        "vendor_pdfs": vendor_count,
        "govt_pdfs": govt_count,
        "available_roles": ["vendor", "government_officer"]
    }

@app.get("/api/v1/admin/config")
async def get_admin_config():
    from app.services.admin_config_service import admin_config_service
    return admin_config_service.get_config()

@app.post("/api/v1/admin/config")
async def save_admin_config(config_data: dict):
    from app.services.admin_config_service import admin_config_service
    success = admin_config_service.save_config(config_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save admin configuration")
    return {"message": "Admin configuration updated successfully"}

@app.get("/api/v1/admin/sessions")
async def get_active_sessions():
    sessions_list = []
    for s_id, s_data in session_manager.sessions.items():
        created_at_iso = s_data["created_at"].isoformat() if hasattr(s_data["created_at"], "isoformat") else str(s_data["created_at"])
        last_activity_iso = s_data["last_activity"].isoformat() if hasattr(s_data["last_activity"], "isoformat") else str(s_data["last_activity"])
        sessions_list.append({
            "session_id": s_id,
            "created_at": created_at_iso,
            "last_activity": last_activity_iso,
            "role": s_data.get("role"),
            "history": s_data.get("history", [])
        })
    return sessions_list

@app.delete("/api/v1/admin/sessions/{session_id}")
async def kill_session(session_id: str):
    if session_id in session_manager.sessions:
        session_manager.clear_session(session_id)
        return {"message": f"Session {session_id} terminated successfully"}
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/api/v1/admin/documents")
async def get_documents():
    rag_engine = get_rag_engine()
    known_sources = getattr(rag_engine, "known_sources", [])
    physical_docs = set()
    for file in settings.VENDOR_PDF_DIR.glob("*.pdf"):
        physical_docs.add(file.name)
    for file in settings.GOVT_PDF_DIR.glob("*.pdf"):
        physical_docs.add(file.name)
    
    unique_sources = sorted(list(set(known_sources).union(physical_docs)))
    return unique_sources

@app.get("/api/v1/admin/export_pdf")
async def export_pdf():
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    
    metrics = await run_in_threadpool(analytics_service.get_metrics)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        alignment=0,
        spaceAfter=15
    )
    section_style = ParagraphStyle(
        'DocSection',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6
    )
    normal_style = ParagraphStyle(
        'DocNormal',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    story.append(Paragraph("CG e-Procurement Chatbot Analytics Audit Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 15))
    
    kpi_data = [
        [
            Paragraph("<b>Total Queries</b>", normal_style),
            Paragraph("<b>Avg Latency</b>", normal_style),
            Paragraph("<b>Satisfaction Rate</b>", normal_style),
            Paragraph("<b>Rated Queries</b>", normal_style)
        ],
        [
            Paragraph(str(metrics.get("total_queries", 0)), normal_style),
            Paragraph(f"{metrics.get('avg_response_time', 0.0):.2f}s", normal_style),
            Paragraph(f"{metrics.get('satisfaction_rate', 100.0):.1f}%", normal_style),
            Paragraph(str(metrics.get("rated_count", 0)), normal_style)
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[120]*4)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Top Asked Terms / Key Topics", section_style))
    topics_list = ", ".join(metrics.get("most_asked_topics", [])) or "None logged yet"
    story.append(Paragraph(topics_list, normal_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Recent Query Logs (Last 50 Queries)", section_style))
    
    log_data = [[
        Paragraph("Timestamp", header_style),
        Paragraph("Role", header_style),
        Paragraph("Query Text", header_style),
        Paragraph("Speed", header_style),
        Paragraph("Feedback", header_style)
    ]]
    
    for q in metrics.get("queries", []):
        try:
            ts = datetime.fromisoformat(q.get("timestamp")).strftime('%m-%d %H:%M')
        except:
            ts = q.get("timestamp", "")
            
        role = "Officer" if q.get("role") == "government_officer" else "Vendor"
        query_txt = q.get("query", "")
        speed = f"{q.get('response_time_seconds', 0.0):.1f}s"
        fb = q.get("feedback", "neutral").upper()
        
        log_data.append([
            Paragraph(ts, normal_style),
            Paragraph(role, normal_style),
            Paragraph(query_txt[:80] + ("..." if len(query_txt) > 80 else ""), normal_style),
            Paragraph(speed, normal_style),
            Paragraph(fb, normal_style)
        ])
        
    log_table = Table(log_data, colWidths=[70, 60, 260, 50, 70])
    log_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a8a3a')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(log_table)
    
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=cg_chatbot_analytics_report.pdf"}
    )

# ──────────────────────────────────────────────────
# TEXT-TO-SPEECH  (Google TTS via gTTS library)
# ──────────────────────────────────────────────────

@app.get("/api/v1/tts")
async def text_to_speech(
    text: str = Query(..., description="Plain text to convert to speech"),
    lang: str = Query("en", description="BCP-47 language code: 'hi' for Hindi, 'en' for English")
):
    """
    Convert text to speech audio using Google TTS (gTTS).
    Returns an audio/mpeg stream that the browser can play directly.
    Handles both Hindi (hi) and English (en).
    """
    try:
        from gtts import gTTS
    except ImportError:
        raise HTTPException(status_code=503, detail="gTTS not installed. Run: pip install gtts")

    # Map lang codes — accept 'hi', 'hi-IN', 'en', 'en-IN' etc.
    lang_code = lang.split('-')[0].lower()  # 'hi-IN' -> 'hi'
    if lang_code not in ('hi', 'en'):
        lang_code = 'en'

    # Truncate text to avoid very long TTS requests (Google has a ~5000 char limit)
    max_chars = 4000
    clean_text = text[:max_chars] if len(text) > max_chars else text
    if not clean_text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")

    def _synthesize():
        """Run gTTS synthesis synchronously (blocking I/O) in thread pool."""
        buf = io.BytesIO()
        tts = gTTS(text=clean_text, lang=lang_code, slow=False)
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()

    try:
        audio_bytes = await run_in_threadpool(_synthesize)
    except Exception as e:
        print(f"[TTS] gTTS error: {e}")
        raise HTTPException(status_code=502, detail=f"TTS synthesis failed: {str(e)}")

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={
            "Content-Length": str(len(audio_bytes)),
            "Cache-Control": "no-cache",
            "Accept-Ranges": "bytes",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)