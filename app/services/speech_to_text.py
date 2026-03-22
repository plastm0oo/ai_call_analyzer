import whisper

try:
    model = whisper.load_model("large")
except Exception as e:
    model = None
    print(f"Whisper model loading failed: {e}")

def transcribe_audio(file_path: str) -> str:
    if model is None:
        raise RuntimeError("Whisper model is not loaded")

    try:
        result = model.transcribe(file_path, language="ru")
        text = result.get("text", "").strip()

        if not text:
            raise ValueError("Empty transcription result")

        return text

    except Exception as e:
        raise RuntimeError(f"Speech-to-Text failed: {str(e)}")