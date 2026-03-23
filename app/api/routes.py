import os
import uuid
import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.report import UploadCallResponse
from app.services.speech_to_text import transcribe_audio
from app.services.pipeline import run_analysis_pipeline
from app.services.report_service import save_report_to_file

router = APIRouter()

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
UPLOAD_DIR = "uploads"
REPORT_DIR = "reports"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

@router.post("/calls/upload", response_model=UploadCallResponse)
async def upload_call(file: UploadFile = File(...)):
    allowed_extensions = (".wav", ".mp3")

    if not file.filename.endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Only .wav and .mp3 files are allowed")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File is too large. Maximum allowed size is 150 MB."
        )
    
    call_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{call_id}_{file.filename}")

    with open(file_path, "wb") as f:
        #content = await file.read()
        f.write(content)

    try:
        transcript = transcribe_audio(file_path)
        analysis_result = run_analysis_pipeline(call_id, transcript)
        report_path = save_report_to_file(call_id, analysis_result["final_report"])

        return {
            "call_id": call_id,
            "filename": file.filename,
            "transcript": analysis_result["transcript"],
            "report": analysis_result["final_report"],
            "report_path": report_path,
            "status": "processed"
        }

    except Exception as e:

        print("\n\n BACKEND ERROR ")

        traceback.print_exc()

        print("ERROR MESSAGE:", str(e), "\n\n")

        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")