from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI(title="My Instagram AI System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def home():
    return {
        "status": "running",
        "message": "Instagram AI System is ready"
    }

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"


class PostRequest(BaseModel):
    topic: str
    content_type: str = "Instagram caption"


@app.get("/health")
def health():
    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=10
        )
        response.raise_for_status()

        return {
            "backend": "running",
            "ollama": "connected"
        }

    except requests.RequestException:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not responding"
        )


@app.post("/generate")
def generate_post(data: PostRequest):

    prompt = f"""
    Act as a professional Instagram content creator.

    Topic: {data.topic}
    Content type: {data.content_type}

    Generate:
    1. Attractive hook
    2. Engaging caption
    3. Five relevant hashtags
    4. Call to action

    Keep the content natural and interesting.
    """

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )

        response.raise_for_status()

        return {
            "success": True,
            "topic": data.topic,
            "generated_content": response.json()["response"]
        }

    except requests.RequestException as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )