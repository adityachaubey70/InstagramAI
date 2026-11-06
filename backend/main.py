from fastapi import BackgroundTasks
from voiceover import generate_voiceover
from fastapi.staticfiles import StaticFiles
from image_creator import create_instagram_image, create_carousel_images
from video_creator import create_reel_video
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
class VoiceoverRequest(BaseModel):
    text: str
    voice: str = "female"
    rate: int = 165
class ReelVideoRequest(BaseModel):
    topic: str
    narration: str
    audio_filename: str
from typing import Literal
from pathlib import Path
import json
import requests
import sqlite3
import zipfile
import uuid
from fastapi.responses import FileResponse
from datetime import datetime

app = FastAPI(title="My Instagram AI System")
MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/media",
    StaticFiles(directory=str(MEDIA_DIR)),
    name="media"
)

# CORS configuration
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

# AI configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"

# Database location
DB_PATH = Path(__file__).resolve().parent / "instagram.db"


# Database connection
def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# Create database table
def init_db():
    with get_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                content_type TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        """)
        # Store daily Reel batches
        connection.execute("""
            CREATE TABLE IF NOT EXISTS reel_batches (
                id TEXT PRIMARY KEY,
                target_count INTEGER NOT NULL DEFAULT 6,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                approved_at TEXT
            )
        """)

        # Store individual Reels
        connection.execute("""
            CREATE TABLE IF NOT EXISTS reels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                narration TEXT NOT NULL,
                video_path TEXT,
                audio_path TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                approved_at TEXT,
                published_at TEXT,
                error TEXT,
                FOREIGN KEY (batch_id) REFERENCES reel_batches(id)
            )
        """)

init_db()
# Create a new Reel batch

class ReelBatchRequest(BaseModel):
    target_count: int = 6


@app.post("/reel-batches")
def create_reel_batch(data: ReelBatchRequest):
    try:
        if not 1 <= data.target_count <= 30:
            raise HTTPException(
                status_code=400,
                detail="Target count must be between 1 and 30."
            )

        batch_id = uuid.uuid4().hex[:12]

        with get_db() as connection:
            connection.execute(
                """
                INSERT INTO reel_batches
                (id, target_count, status, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    batch_id,
                    data.target_count,
                    "pending",
                    datetime.now().isoformat(timespec="seconds")
                )
            )

        return {
            "success": True,
            "message": "Reel batch created successfully",
            "batch_id": batch_id,
            "target_count": data.target_count,
            "status": "pending"
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# Request models
class PostRequest(BaseModel):
    topic: str
    content_type: str = "Instagram caption"


class ImageRequest(BaseModel):
    topic: str
    title: str
    subtitle: str

class CarouselRequest(BaseModel):
    topic: str
    slide_count: int = 5

# Request models
class PostRequest(BaseModel):
    topic: str
    content_type: str = "Instagram caption"


class SavePostRequest(BaseModel):
    topic: str
    content_type: str
    content: str


class StatusUpdate(BaseModel):
    status: Literal["pending", "approved", "rejected"]


class EditPostRequest(BaseModel):
    content: str



# Home endpoint
@app.get("/")
def home():
    return {
        "status": "running",
        "message": "Instagram AI System is ready"
    }


# Health endpoint
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
            "ollama": "connected",
            "database": "ready"
        }

    except requests.RequestException:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not responding"
        )
    
# new end piont    
@app.put("/posts/{post_id}")
def edit_post(post_id: int, data: EditPostRequest):

    with get_db() as connection:
        cursor = connection.execute(
            "UPDATE posts SET content = ? WHERE id = ?",
            (data.content, post_id)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Post not found"
            )

    return {
        "success": True,
        "message": "Post updated successfully"
    }

# Generate Instagram content
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


# Save a post permanently
@app.post("/posts")
def save_post(data: SavePostRequest):

    with get_db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO posts
            (topic, content_type, content, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data.topic,
                data.content_type,
                data.content,
                "pending",
                datetime.now().isoformat(timespec="seconds")
            )
        )

        post_id = cursor.lastrowid

    return {
        "success": True,
        "message": "Post saved for approval",
        "post_id": post_id,
        "status": "pending"
    }


# Get all saved posts
@app.get("/posts")
def get_posts():

    with get_db() as connection:
        rows = connection.execute(
            "SELECT * FROM posts ORDER BY id DESC"
        ).fetchall()

    return [dict(row) for row in rows]


# Approve or reject a post
@app.patch("/posts/{post_id}/status")
def update_post_status(post_id: int, data: StatusUpdate):

    with get_db() as connection:
        cursor = connection.execute(
            "UPDATE posts SET status = ? WHERE id = ?",
            (data.status, post_id)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Post not found"
            )

    return {
        "success": True,
        "post_id": post_id,
        "status": data.status
    }


# Delete a saved post
@app.delete("/posts/{post_id}")
def delete_post(post_id: int):

    with get_db() as connection:
        cursor = connection.execute(
            "DELETE FROM posts WHERE id = ?",
            (post_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Post not found"
            )

    return {
        "success": True,
        "message": "Post deleted"
    }
@app.post("/create-image")
def create_image(data: ImageRequest):
    try:
        image_path = create_instagram_image(
            data.topic,
            data.title,
            data.subtitle
        )

        filename = Path(image_path).name

        return {
            "success": True,
            "message": "Instagram image created successfully",
            "image_url": f"/media/{filename}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/create-carousel")
def create_carousel(data: CarouselRequest):

    if not 3 <= data.slide_count <= 7:
        raise HTTPException(
            status_code=400,
            detail="Slide count must be between 3 and 7."
        )

    prompt = f"""
    Create an educational Instagram carousel about: {data.topic}

    Create exactly {data.slide_count} slides.

    Return ONLY valid JSON in this format:
    {{
        "slides": [
            {{
                "title": "Slide title",
                "subtitle": "Short explanation"
            }}
        ]
    }}

    Make the first slide an attractive introduction.
    Make the middle slides informative.
    Make the last slide a call to action.
    Keep each subtitle short and easy to understand.
    Do not include markdown or text outside the JSON.
    """

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=240
        )

        response.raise_for_status()

        ai_result = json.loads(response.json()["response"])
        slides = ai_result["slides"]

        if len(slides) != data.slide_count:
            raise ValueError("AI generated an incorrect number of slides.")

        for slide in slides:
            if not slide.get("title") or not slide.get("subtitle"):
                raise ValueError("A slide is missing its title or subtitle.")

        image_paths = create_carousel_images(data.topic, slides)

        image_urls = [
            f"/media/{Path(path).name}"
            for path in image_paths
        ]

        return {
            "success": True,
            "topic": data.topic,
            "slides": slides,
            "images": image_urls,
            "message": "Instagram carousel created successfully!"
        }

    except requests.RequestException as error:
        raise HTTPException(status_code=503, detail=str(error))

    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=500, detail=str(error))

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

# ======================================
# InstaAI - Download Carousel as ZIP
# ======================================

class CarouselZipRequest(BaseModel):
    images: list[str]


@app.post("/download-carousel-zip")
def download_carousel_zip(data: CarouselZipRequest):
    try:
        zip_name = f"Instagram_Carousel_{uuid.uuid4().hex[:8]}.zip"
        zip_path = MEDIA_DIR / zip_name

        if not data.images:
            raise HTTPException(
                status_code=400,
                detail="No carousel images provided."
            )

        with zipfile.ZipFile(
            zip_path, "w", zipfile.ZIP_DEFLATED
        ) as zip_file:

            for index, image_url in enumerate(data.images, start=1):
                filename = Path(image_url).name
                image_path = (MEDIA_DIR / filename).resolve()

                if image_path.parent != MEDIA_DIR.resolve():
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid image path."
                    )

                if not image_path.is_file():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Image not found: {filename}"
                    )

                zip_file.write(
                    image_path,
                    arcname=f"Slide_{index}.png"
                )

        return FileResponse(
            path=str(zip_path),
            filename=zip_name,
            media_type="application/zip"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================================
# InstaAI - AI Reel Script Generator
# ======================================

class ReelRequest(BaseModel):
    topic: str
    duration: int = 30
    language: str = "English"


@app.post("/generate-reel-script")
def generate_reel_script(data: ReelRequest):
    try:
        if not data.topic.strip():
            raise HTTPException(
                status_code=400,
                detail="Please enter a Reel topic."
            )

        if data.duration not in [15, 30, 45, 60]:
            raise HTTPException(
                status_code=400,
                detail="Duration must be 15, 30, 45 or 60 seconds."
            )

        prompt = f"""
        Create an engaging Instagram Reel script.

        Topic: {data.topic}
        Duration: {data.duration} seconds
        Language: {data.language}

        Include:
        1. Attention-grabbing opening hook.
        2. Scene-by-scene visual directions.
        3. Voiceover narration.
        4. On-screen text for each scene.
        5. Closing call to action.
        6. Relevant hashtags.

        Keep the script suitable for Instagram Reels.
        Make it engaging, clear and practical.
        """

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
        result = response.json()

        return {
            "success": True,
            "topic": data.topic,
            "duration": data.duration,
            "language": data.language,
            "generated_script": result.get("response", "").strip()
        }

    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Local AI service error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/generate-voiceover")
def create_voiceover(data: VoiceoverRequest):
    try:
        audio_path = generate_voiceover(
            data.text,
            data.voice,
            data.rate
        )

        filename = Path(audio_path).name

        return {
            "success": True,
            "message": "English voiceover created successfully",
            "audio_url": f"/media/{filename}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/create-reel-video")
def create_reel_video_endpoint(data: ReelVideoRequest):
    try:
        if not data.topic.strip() or not data.narration.strip():
            raise HTTPException(
                status_code=400,
                detail="Topic and narration are required"
            )

        # Only accept audio files inside the media folder
        audio_name = Path(data.audio_filename).name

        if audio_name != data.audio_filename:
            raise HTTPException(
                status_code=400,
                detail="Invalid audio filename"
            )

        audio_path = MEDIA_DIR / audio_name

        if not audio_path.is_file() or audio_path.suffix.lower() != ".wav":
            raise HTTPException(
                status_code=404,
                detail="Voiceover audio file not found"
            )

        video_path = create_reel_video(
            data.topic,
            data.narration,
            audio_path
        )

        return {
            "success": True,
            "message": "Instagram Reel video created successfully",
            "video_url": f"/media/videos/{Path(video_path).name}"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ==========================================
# InstaAI - Daily Reel Batch Approval
# ==========================================

@app.get("/reel-batches")
def get_reel_batches():
    with get_db() as connection:
        rows = connection.execute(
            """
            SELECT
                b.id,
                b.target_count,
                b.status,
                b.created_at,
                b.approved_at,
                COUNT(r.id) AS reel_count
            FROM reel_batches b
            LEFT JOIN reels r ON r.batch_id = b.id
            GROUP BY b.id
            ORDER BY b.created_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


@app.get("/reel-batches/{batch_id}/reels")
def get_batch_reels(batch_id: str):
    with get_db() as connection:
        batch = connection.execute(
            "SELECT * FROM reel_batches WHERE id = ?",
            (batch_id,)
        ).fetchone()

        if batch is None:
            raise HTTPException(
                status_code=404,
                detail="Reel batch not found"
            )

        rows = connection.execute(
            """
            SELECT * FROM reels
            WHERE batch_id = ?
            ORDER BY id
            """,
            (batch_id,)
        ).fetchall()

    return {
        "batch": dict(batch),
        "reels": [dict(row) for row in rows]
    }


@app.post("/reel-batches/{batch_id}/approve-all")
def approve_all_reels(batch_id: str):
    approved_at = datetime.now().isoformat(timespec="seconds")

    with get_db() as connection:
        batch = connection.execute(
            "SELECT * FROM reel_batches WHERE id = ?",
            (batch_id,)
        ).fetchone()

        if batch is None:
            raise HTTPException(404, "Reel batch not found")

        counts = connection.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) AS ready
            FROM reels
            WHERE batch_id = ?
            """,
            (batch_id,)
        ).fetchone()

        if counts["total"] != batch["target_count"] or counts["ready"] != batch["target_count"]:
            raise HTTPException(
                status_code=400,
                detail="All Reels must finish generating successfully before approval."
            )

        connection.execute(
            """
            UPDATE reels
            SET status = 'approved', approved_at = ?
            WHERE batch_id = ? AND status = 'ready'
            """,
            (approved_at, batch_id)
        )

        connection.execute(
            """
            UPDATE reel_batches
            SET status = 'approved', approved_at = ?
            WHERE id = ?
            """,
            (approved_at, batch_id)
        )

    return {
        "success": True,
        "batch_id": batch_id,
        "status": "approved",
        "message": "All Reels in this batch have been approved."
    }

@app.post("/reel-batches/{batch_id}/reject-all")
def reject_all_reels(batch_id: str):
    with get_db() as connection:
        batch = connection.execute(
            "SELECT * FROM reel_batches WHERE id = ?",
            (batch_id,)
        ).fetchone()

        if batch is None:
            raise HTTPException(
                status_code=404,
                detail="Reel batch not found"
            )

        connection.execute(
            """
            UPDATE reels
            SET status = 'rejected'
            WHERE batch_id = ? AND status = 'pending'
            """,
            (batch_id,)
        )

        connection.execute(
            """
            UPDATE reel_batches
            SET status = 'rejected'
            WHERE id = ?
            """,
            (batch_id,)
        )

    return {
        "success": True,
        "batch_id": batch_id,
        "status": "rejected",
        "message": "All pending Reels in this batch have been rejected."
    }
def generate_batch_background(batch_id: str):
    topics = [
        "AI Technology",
        "Python Programming",
        "Data Science",
        "Artificial Intelligence",
        "Python Programming",
        "Data Science"
    ]

    with get_db() as connection:
        batch = connection.execute(
            "SELECT * FROM reel_batches WHERE id = ?",
            (batch_id,)
        ).fetchone()

        if batch is None:
            return

        connection.execute(
            "UPDATE reel_batches SET status = 'generating' WHERE id = ?",
            (batch_id,)
        )

        topics_to_generate = (
            topics * ((batch["target_count"] + len(topics) - 1) // len(topics))
        )[:batch["target_count"]]

        for topic in topics_to_generate:
            connection.execute(
                """
                INSERT INTO reels
                (batch_id, topic, narration, status, created_at)
                VALUES (?, ?, ?, 'generating', ?)
                """,
                (
                    batch_id,
                    topic,
                    "",
                    datetime.now().isoformat(timespec="seconds")
                )
            )

        reel_rows = connection.execute(
            "SELECT id, topic FROM reels WHERE batch_id = ? ORDER BY id",
            (batch_id,)
        ).fetchall()

    failed = False

    for reel in reel_rows:
        reel_id = reel["id"]
        topic = reel["topic"]

        try:
            prompt = f"""
            Write an engaging 30-second Instagram Reel narration
            about {topic}.

            Requirements:
            - English only.
            - Around 50 to 65 words.
            - Start with a strong hook.
            - Use simple language.
            - End with a call to action.
            - Return narration only.
            - No headings, scene directions or hashtags.
            """

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:3b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=240
            )

            response.raise_for_status()
            narration = response.json()["response"].strip()

            audio_path = generate_voiceover(
                narration,
                "female",
                165
            )

            video_path = create_reel_video(
                topic,
                narration,
                audio_path
            )

            with get_db() as connection:
                connection.execute(
                    """
                    UPDATE reels
                    SET narration = ?, audio_path = ?,
                        video_path = ?, status = 'ready'
                    WHERE id = ?
                    """,
                    (
                        narration,
                        str(audio_path),
                        str(video_path),
                        reel_id
                    )
                )

        except Exception as error:
            failed = True

            with get_db() as connection:
                connection.execute(
                    """
                    UPDATE reels
                    SET status = 'failed', error = ?
                    WHERE id = ?
                    """,
                    (str(error), reel_id)
                )

    with get_db() as connection:
        final_status = "partial" if failed else "ready"

        connection.execute(
            "UPDATE reel_batches SET status = ? WHERE id = ?",
            (final_status, batch_id)
        )
class GenerateBatchRequest(BaseModel):
    batch_id: str


@app.post("/reel-batches/generate")
def start_batch_generation(
    data: GenerateBatchRequest,
    background_tasks: BackgroundTasks
):
    with get_db() as connection:
        batch = connection.execute(
            "SELECT * FROM reel_batches WHERE id = ?",
            (data.batch_id,)
        ).fetchone()

        if batch is None:
            raise HTTPException(
                status_code=404,
                detail="Batch not found"
            )

        if batch["status"] != "pending":
            raise HTTPException(
                status_code=400,
                detail="This batch is not available for generation."
            )

        existing = connection.execute(
            "SELECT COUNT(*) FROM reels WHERE batch_id = ?",
            (data.batch_id,)
        ).fetchone()[0]

        if existing > 0:
            raise HTTPException(
                status_code=400,
                detail="Reels already exist in this batch."
            )

    background_tasks.add_task(
        generate_batch_background,
        data.batch_id
    )

    return {
        "success": True,
        "message": "Six Reel generation started.",
        "batch_id": data.batch_id,
        "status": "generating"
    }