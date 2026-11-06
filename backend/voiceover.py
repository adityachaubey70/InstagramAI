
import pyttsx3
from pathlib import Path
import uuid

MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def generate_voiceover(text, voice="female", rate=165):
    if not text or not text.strip():
        raise ValueError("Voiceover text cannot be empty")

    engine = pyttsx3.init(driverName="sapi5")

    voices = engine.getProperty("voices")

    preferred_voice = "ZIRA" if voice.lower() == "female" else "DAVID"

    selected_voice = next(
        (
            v for v in voices
            if preferred_voice in (v.name + " " + v.id).upper()
        ),
        voices[0]
    )

    engine.setProperty("voice", selected_voice.id)
    engine.setProperty("rate", max(120, min(200, rate)))

    filename = f"voiceover_{uuid.uuid4().hex[:8]}.wav"
    output_path = MEDIA_DIR / filename

    try:
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
    finally:
        engine.stop()

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Voiceover audio file could not be created")

    return output_path
