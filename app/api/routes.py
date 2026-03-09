import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.speech_to_text import transcribe_audio
from app.services.pipeline import run_analysis_pipeline
from app.services.report_service import save_report_to_file

router = APIRouter()

UPLOAD_DIR = "uploads"
REPORT_DIR = "reports"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


@router.post("/calls/upload")
async def upload_call(file: UploadFile = File(...)):
    allowed_extensions = (".wav", ".mp3")

    if not file.filename.endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Only .wav and .mp3 files are allowed")

    call_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{call_id}_{file.filename}")

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        transcript = transcribe_audio(file_path)
        analysis_result = run_analysis_pipeline(transcript)
        report_path = save_report_to_file(call_id, analysis_result)

        return {
            "call_id": call_id,
            "filename": file.filename,
            "transcript": transcript,
            "report": analysis_result,
            "report_path": report_path,
            "status": "processed"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")