import io
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import textwrap

MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def get_font(size, bold=False):
    windows_fonts = Path("C:/Windows/Fonts")
    font_name = "arialbd.ttf" if bold else "arial.ttf"
    font_path = windows_fonts / font_name

    try:
        return ImageFont.truetype(str(font_path), size)
    except OSError:
        return ImageFont.load_default()


def create_instagram_image(topic, title, subtitle):
    width, height = 1080, 1080

    image = Image.new("RGB", (width, height), "#17152F")
    draw = ImageDraw.Draw(image)

    # Colorful background
    draw.rectangle((0, 0, width, height), fill="#211044")
    draw.ellipse((720, -150, 1200, 330), fill="#9333EA")
    draw.ellipse((-180, 750, 300, 1230), fill="#EC4899")
    draw.ellipse((650, 650, 1150, 1150), fill="#2563EB")

    # Main card
    draw.rounded_rectangle(
        (55, 55, 1025, 1025),
        radius=45,
        fill="#17152F",
        outline="#C084FC",
        width=5
    )

    # Branding
    draw.text(
        (100, 115),
        "InstaAI",
        fill="#F9A8D4",
        font=get_font(42, True)
    )

    # Title
    title_font = get_font(76, True)
    title_lines = textwrap.wrap(title, width=19)
    y = 330

    for line in title_lines[:4]:
        draw.text(
            (100, y),
            line,
            fill="#FFFFFF",
            font=title_font
        )
        y += 100

    # Subtitle
    subtitle_font = get_font(36)
    subtitle_lines = textwrap.wrap(subtitle, width=42)
    y += 35

    for line in subtitle_lines[:5]:
        draw.text(
            (105, y),
            line,
            fill="#E9D5FF",
            font=subtitle_font
        )
        y += 55

    # Footer
    draw.text(
        (100, 920),
        "LEARN • CREATE • GROW",
        fill="#F9A8D4",
        font=get_font(27, True)
    )

    # Safe filename
    safe_topic = "".join(
        char if char.isalnum() else "_"
        for char in topic
    )[:35]

    if not safe_topic:
        safe_topic = "instagram"
    output_path = MEDIA_DIR / f"{safe_topic}_post.png"

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    png_data = buffer.getvalue()

    output_path.write_bytes(png_data)

    print("Image saved successfully!")
    print("File size:", len(png_data), "bytes")

    return str(output_path)

def create_carousel_images(topic, slides):
    """
    Create multiple matching Instagram carousel slides.
    Each slide must contain a title and subtitle.
    """
    width, height = 1080, 1080
    safe_topic = "".join(
        char if char.isalnum() else "_"
        for char in topic
    )[:30] or "instagram"

    generated_files = []

    for index, slide in enumerate(slides, start=1):
        title = str(slide.get("title", ""))
        subtitle = str(slide.get("subtitle", ""))

        image = Image.new("RGB", (width, height), "#17152F")
        draw = ImageDraw.Draw(image)

        # Colorful background matching InstaAI
        draw.rectangle((0, 0, width, height), fill="#211044")
        draw.ellipse((720, -150, 1200, 330), fill="#9333EA")
        draw.ellipse((-180, 750, 300, 1230), fill="#EC4899")
        draw.ellipse((650, 650, 1150, 1150), fill="#2563EB")

        # Main card
        draw.rounded_rectangle(
            (55, 55, 1025, 1025),
            radius=45,
            fill="#17152F",
            outline="#C084FC",
            width=5
        )

        # Branding
        draw.text(
            (100, 115),
            "InstaAI",
            fill="#F9A8D4",
            font=get_font(42, True)
        )

        # Slide number
        draw.text(
            (820, 120),
            f"{index}/{len(slides)}",
            fill="#E9D5FF",
            font=get_font(32, True)
        )

        # Slide title
        title_font = get_font(68, True)
        title_lines = textwrap.wrap(title, width=20)

        y = 330
        for line in title_lines[:4]:
            draw.text(
                (100, y),
                line,
                fill="#FFFFFF",
                font=title_font
            )
            y += 90

        # Slide description
        subtitle_font = get_font(34)
        subtitle_lines = textwrap.wrap(subtitle, width=45)

        y += 35
        for line in subtitle_lines[:6]:
            draw.text(
                (105, y),
                line,
                fill="#E9D5FF",
                font=subtitle_font
            )
            y += 52

        # Footer
        draw.text(
            (100, 920),
            "LEARN • CREATE • GROW",
            fill="#F9A8D4",
            font=get_font(27, True)
        )

        # Save slide
        filename = f"{safe_topic}_slide_{index}.png"
        output_path = MEDIA_DIR / filename

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        output_path.write_bytes(buffer.getvalue())

        generated_files.append(str(output_path))

    return generated_files
