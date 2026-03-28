import os
import uuid
import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.report import UploadCallResponse
from app.services.speech_to_text import transcribe_audio
from app.services.pipeline import run_analysis_pipeline
from app.services.report_service import save_report_to_file
#from app.db.session import get_db
from fastapi.responses import FileResponse
from app.services.coaching_report_service import CoachingReportService

router = APIRouter()

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
UPLOAD_DIR = "uploads"
REPORT_DIR = "reports"
PDF_DIR = os.path.join(REPORT_DIR, "pdf")

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

@router.post("/calls/upload")
async def upload_call(file: UploadFile = File(...)):
    allowed_extensions = (".wav", ".mp3")

    if not file.filename.endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Only .wav and .mp3 files are allowed")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File is too large. Maximum allowed size is 100 MB."
        )
    
    call_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{call_id}_{file.filename}")

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        transcript = transcribe_audio(file_path)
        analysis_result = run_analysis_pipeline(call_id, transcript)
        display_transcript = analysis_result.get("role_transcript") or analysis_result["transcript"]
        report_path = save_report_to_file(call_id, analysis_result)

        return {
            "call_id": call_id,
            "filename": file.filename,
            "transcript": display_transcript,
            "role_transcript": analysis_result.get("role_transcript"),
            "report": analysis_result["final_report"],
            "report_path": report_path,
            "status": "processed"
        }

    except Exception as e:

        print("\n\n BACKEND ERROR ")

        traceback.print_exc()

        print("ERROR MESSAGE:", str(e), "\n\n")

        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
pdf_service = CoachingReportService(reports_dir=REPORT_DIR)

@router.get("/calls/{call_id}/download/pdf")
async def download_call_pdf(call_id: str):
    try:
        pdf_path = pdf_service.get_or_create_pdf(call_id)

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"coaching_report_{call_id}.pdf",
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Report JSON for call_id={call_id} not found"
        )

    except Exception as e:
        print("\n\n PDF DOWNLOAD ERROR ")
        traceback.print_exc()
        print("ERROR MESSAGE:", str(e), "\n\n")

        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )