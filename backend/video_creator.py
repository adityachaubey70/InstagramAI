
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
    vfx
)
import textwrap
import uuid
import math
import numpy as np
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / "media"
VIDEO_DIR = MEDIA_DIR / "videos"

VIDEO_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 720
HEIGHT = 1280
FPS = 24


def get_font(size, bold=False):
    font_path = (
        "C:/Windows/Fonts/arialbd.ttf"
        if bold else
        "C:/Windows/Fonts/arial.ttf"
    )

    try:
        return ImageFont.truetype(font_path, size)
    except OSError:
        return ImageFont.load_default()


def create_slide(text, title, number, total):
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    # Purple gradient background
    for y in range(HEIGHT):
        ratio = y / HEIGHT

        r = int(25 + ratio * 35)
        g = int(15 + ratio * 5)
        b = int(65 + ratio * 75)

        draw.line((0, y, WIDTH, y), fill=(r, g, b))

    # Decorative circles
    draw.ellipse((-100, -100, 250, 250), fill=(95, 35, 150))
    draw.ellipse((530, 950, 850, 1270), fill=(120, 30, 125))

    # Branding
    draw.text(
        (45, 55),
        "InstaAI",
        font=get_font(36, True),
        fill=(255, 100, 180)
    )

    draw.text(
        (45, 120),
        f"SCENE {number}/{total}",
        font=get_font(22),
        fill=(200, 190, 255)
    )

    # Title
    title_lines = textwrap.wrap(title, width=24)

    y = 300

    for line in title_lines:
        draw.text(
            (55, y),
            line,
            font=get_font(48, True),
            fill="white"
        )
        y += 65

    # Main text
    text_lines = textwrap.wrap(text, width=28)

    y = 570

    for line in text_lines:
        draw.text(
            (55, y),
            line,
            font=get_font(34),
            fill=(235, 230, 255)
        )
        y += 55

    # Progress indicator
    bar_width = 620
    progress = int(bar_width * number / total)

    draw.rounded_rectangle(
        (50, 1150, 50 + bar_width, 1165),
        radius=7,
        fill=(90, 75, 130)
    )

    draw.rounded_rectangle(
        (50, 1150, 50 + progress, 1165),
        radius=7,
        fill=(255, 90, 180)
    )

    draw.text(
        (45, 1190),
        "LEARN • CREATE • GROW",
        font=get_font(22, True),
        fill="white"
    )

    return image


def split_into_scenes(narration, max_words=12):
    words = narration.split()
    scenes = []

    for i in range(0, len(words), max_words):
        scenes.append(" ".join(words[i:i + max_words]))

    return scenes or ["Welcome to InstaAI!"]


def create_subtitle_frame(words, active_index):
    """Create a subtitle image with the active word highlighted."""

    image = Image.new(
        "RGBA",
        (660, 110),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (5, 5, 655, 105),
        radius=20,
        fill=(10, 10, 20, 220)
    )

    font_size = 32
    font = get_font(font_size, True)

    # Reduce font size if the caption is too wide
    while font_size > 20:
        font = get_font(font_size, True)

        widths = [
            draw.textbbox((0, 0), word, font=font)[2]
            for word in words
        ]

        total_width = sum(widths) + (len(words) - 1) * 12

        if total_width <= 600:
            break

        font_size -= 2

    widths = [
        draw.textbbox((0, 0), word, font=font)[2]
        for word in words
    ]

    total_width = sum(widths) + (len(words) - 1) * 12

    x = (660 - total_width) // 2

    for index, word in enumerate(words):

        color = (
            (255, 100, 190)
            if index == active_index
            else (255, 255, 255)
        )

        draw.text(
            (x, 32),
            word,
            font=font,
            fill=color
        )

        x += widths[index] + 12

    return image


def create_subtitle_clips(narration, audio_duration):
    """Create approximate word-synchronized subtitle animations."""

    words = narration.split()

    if not words:
        return []

    weights = [max(1, len(word)) for word in words]
    total_weight = sum(weights)

    clips = []
    current_time = 0

    for index, word in enumerate(words):

        duration = audio_duration * weights[index] / total_weight

        # Display a group of four words
        start = (index // 4) * 4
        group = words[start:start + 4]
        active_index = index - start

        frame = create_subtitle_frame(
            group,
            active_index
        )

        subtitle_clip = (
            ImageClip(
                np.array(frame),
                transparent=True
            )
            .with_duration(duration)
            .with_start(current_time)
            .with_position(("center", 920))
        )

        clips.append(subtitle_clip)

        current_time += duration

    return clips



def create_reel_video(topic, narration, audio_path):
    if not Path(audio_path).exists():
        raise FileNotFoundError("Voiceover audio file not found")

    audio = AudioFileClip(str(audio_path))

    scenes = split_into_scenes(narration)
    total = len(scenes)

    # Limit scene count for lightweight video rendering
    if total > 12:
        audio.close()
        raise ValueError(
            "Narration is too long. Please use a shorter script."
        )

    total_words = sum(len(scene.split()) for scene in scenes)

    clips = []
    image_paths = []

    try:
        for index, scene in enumerate(scenes, start=1):
            scene_words = len(scene.split())

            duration = (
                audio.duration * scene_words / total_words
            )

            # Keep every scene at least 1.5 seconds
            duration = max(1.5, duration)

            image = create_slide(
                scene,
                topic,
                index,
                total
            )

            image_path = (
                VIDEO_DIR /
                f"scene_{uuid.uuid4().hex[:8]}.png"
            )

            image.save(image_path)
            image_paths.append(image_path)

            clip = (
                ImageClip(str(image_path))
                .with_duration(duration)
                .with_effects([
                 vfx.FadeIn(0.35),
                 vfx.FadeOut(0.35)
                ])
            )

            clips.append(clip)

        video = concatenate_videoclips(
            clips,
            method="compose"
        )

        # Match video length to voiceover length
        video = video.with_duration(audio.duration)
        # Generate animated synchronized subtitles
        subtitle_clips = create_subtitle_clips(
            narration,
            audio.duration
        )
        # Combine video and subtitles
        video = CompositeVideoClip(
            [video] + subtitle_clips,
            size=(WIDTH, HEIGHT)
        )
        video = video.with_duration(audio.duration)
        video = video.with_audio(audio)

        filename = f"InstaAI_Reel_{uuid.uuid4().hex[:8]}.mp4"
        output_path = VIDEO_DIR / filename

        video.write_videofile(
            str(output_path),
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=2,
            logger=None
        )

        video.close()

        for subtitle_clip in subtitle_clips:
            subtitle_clip.close()

        return output_path

    finally:
        audio.close()
        for clip in clips:
            clip.close()
