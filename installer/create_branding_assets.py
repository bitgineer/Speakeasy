#!/usr/bin/env python3
"""
Create comprehensive branding assets for faster-whisper-hotkey.

Generates:
- High-resolution logo (PNG/SVG)
- GitHub banner/header
- Social media images (Twitter/X, Reddit, etc.)
- App store screenshots
- Marketing materials with consistent branding
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
from typing import Tuple, List


# Brand Colors
BRAND = {
    'primary': (37, 99, 235),      # #2563EB - Blue 600
    'primary_dark': (29, 78, 216), # #1D4ED8 - Blue 700
    'secondary': (139, 92, 246),   # #8B5CF6 - Purple 500
    'accent': (59, 130, 246),      # #3B82F6 - Blue 500
    'dark': (15, 23, 42),          # #0F172A - Slate 900
    'light': (248, 250, 252),      # #F8FAFC - Slate 50
    'white': (255, 255, 255),
    'gradient_start': (37, 99, 235),
    'gradient_end': (139, 92, 246),
}


def draw_gradient(draw: ImageDraw.ImageDraw, width: int, height: int,
                  color_start: Tuple, color_end: Tuple, direction: str = 'vertical') -> None:
    """Draw a gradient on the image."""
    if direction == 'vertical':
        for y in range(height):
            ratio = y / height
            r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
            g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
            b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
            draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b, 255))
    else:
        for x in range(width):
            ratio = x / width
            r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
            g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
            b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
            draw.rectangle([(x, 0), (x + 1, height)], fill=(r, g, b, 255))


def create_gradient_image(width: int, height: int,
                          color_start: Tuple, color_end: Tuple,
                          direction: str = 'vertical') -> Image.Image:
    """Create an image with a gradient background."""
    img = Image.new('RGBA', (width, height))
    draw = ImageDraw.Draw(img)
    draw_gradient(draw, width, height, color_start, color_end, direction)
    return img


def draw_microphone_element(size: int, center_x: int, center_y: int,
                            scale: float, color: Tuple,
                            draw: ImageDraw.ImageDraw) -> None:
    """Draw a microphone element at the specified position."""
    # Microphone body
    mic_width = int(64 * scale)
    mic_height = int(100 * scale)
    mic_x = center_x - mic_width // 2
    mic_y = center_y - mic_height // 2 - int(10 * scale)

    corner_radius = int(32 * scale)
    draw.rounded_rectangle(
        [mic_x, mic_y, mic_x + mic_width, mic_y + mic_height],
        radius=corner_radius,
        fill=color
    )

    # Microphone stand
    stand_width = int(8 * scale)
    stand_height = int(30 * scale)
    stand_x = center_x - stand_width // 2
    stand_y = mic_y + mic_height + int(5 * scale)
    draw.rectangle(
        [stand_x, stand_y, stand_x + stand_width, stand_y + stand_height],
        fill=color
    )

    # Base
    base_width = int(80 * scale)
    base_height = int(12 * scale)
    base_x = center_x - base_width // 2
    base_y = stand_y + stand_height
    draw.rounded_rectangle(
        [base_x, base_y, base_x + base_width, base_y + base_height],
        radius=int(6 * scale),
        fill=color
    )


def draw_sound_waves(center_x: int, center_y: int, scale: float,
                     color: Tuple, draw: ImageDraw.ImageDraw,
                     side: str = 'right') -> None:
    """Draw sound wave elements."""
    wave_count = 3
    wave_spacing = int(20 * scale)
    wave_width = int(4 * scale)

    if side == 'right':
        wave_start_x = center_x + int(40 * scale)
    else:
        wave_start_x = center_x - int(40 * scale) - wave_width - (wave_count - 1) * wave_spacing

    for i in range(wave_count):
        if side == 'right':
            wave_x = wave_start_x + i * wave_spacing
        else:
            wave_x = wave_start_x + (wave_count - 1 - i) * wave_spacing

        wave_height = int((30 + i * 15) * scale)
        wave_y = center_y - wave_height // 2
        draw.rounded_rectangle(
            [wave_x, wave_y, wave_x + wave_width, wave_y + wave_height],
            radius=int(2 * scale),
            fill=color
        )


def create_logo(size: int = 512, with_text: bool = False,
                text: str = "faster-whisper") -> Image.Image:
    """Create a high-resolution logo."""
    # Create gradient background (rounded square for modern app icon look)
    img = create_gradient_image(
        size, size,
        BRAND['gradient_start'], BRAND['gradient_end'],
        'diagonal'
    )

    # Make it a rounded rectangle (squircle shape)
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    corner_radius = size // 5
    mask_draw.rounded_rectangle(
        [(0, 0), (size, size)],
        radius=corner_radius,
        fill=255
    )
    img.putalpha(mask)

    draw = ImageDraw.Draw(img)
    center = size // 2

    # Draw microphone icon
    scale = size / 256
    draw_microphone_element(size, center - int(30 * scale), center - int(20 * scale), scale, BRAND['white'], draw)

    # Draw sound waves
    draw_sound_waves(center, center - int(20 * scale), scale, BRAND['white'], draw, 'right')

    # Add text below icon if requested
    if with_text:
        try:
            # Try to use a nice font, fall back to default
            font_size = size // 12
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = center - text_width // 2
        text_y = size - int(size * 0.15)

        draw.text((text_x, text_y), text, fill=BRAND['white'], font=font)

    return img


def create_diagonal_gradient(width: int, height: int,
                             color_start: Tuple, color_end: Tuple) -> Image.Image:
    """Create an image with a diagonal gradient."""
    img = Image.new('RGBA', (width, height))
    draw = ImageDraw.Draw(img)

    # Diagonal gradient
    for y in range(height):
        for x in range(width):
            ratio = (x + y) / (width + height)
            r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
            g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
            b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
            img.putpixel((x, y), (r, g, b, 255))

    return img


def create_github_banner(width: int = 1280, height: int = 320) -> Image.Image:
    """Create a banner for GitHub repository/social media."""
    # Create gradient background
    img = create_gradient_image(width, height, BRAND['dark'], BRAND['primary_dark'], 'diagonal')

    draw = ImageDraw.Draw(img)

    # Add subtle pattern (dots)
    dot_spacing = 20
    dot_color = (255, 255, 255, 10)  # Very transparent white
    for y in range(0, height, dot_spacing):
        for x in range(0, width, dot_spacing):
            draw.ellipse([(x, y), (x + 2, y + 2)], fill=dot_color)

    # Draw logo on the left
    logo_size = int(height * 0.6)
    logo = create_logo(logo_size)
    logo_x = int(width * 0.08)
    logo_y = (height - logo_size) // 2
    img.paste(logo, (logo_x, logo_y), logo)

    # Add text
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        subtitle_font = ImageFont.truetype("arial.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    text_x = logo_x + logo_size + int(width * 0.08)

    # Title
    draw.text((text_x, height // 2 - 40), "faster-whisper-hotkey",
              fill=BRAND['white'], font=title_font)

    # Subtitle
    draw.text((text_x, height // 2 + 20), "Instant voice transcription with a single hotkey",
              fill=(200, 200, 200), font=subtitle_font)

    # Badge (small pill-shaped tag)
    badge_x = width - int(width * 0.15)
    badge_y = height // 2 - 20
    badge_width = 120
    badge_height = 40
    badge_color = BRAND['secondary']

    draw.rounded_rectangle(
        [(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)],
        radius=20,
        fill=badge_color
    )

    try:
        badge_font = ImageFont.truetype("arial.ttf", 16)
    except:
        badge_font = ImageFont.load_default()

    badge_text = "v1.0.0"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    badge_text_x = badge_x + (badge_width - (badge_bbox[2] - badge_bbox[0])) // 2
    badge_text_y = badge_y + (badge_height - (badge_bbox[3] - badge_bbox[1])) // 2
    draw.text((badge_text_x, badge_text_y - badge_bbox[1]), badge_text,
              fill=BRAND['white'], font=badge_font)

    return img


def create_social_media_banner(width: int = 1200, height: int = 630,
                               platform: str = "generic") -> Image.Image:
    """Create OpenGraph/social media banner."""
    # Dark gradient background
    img = create_gradient_image(width, height, BRAND['dark'], (30, 58, 138), 'vertical')

    draw = ImageDraw.Draw(img)

    # Large centered logo
    logo_size = min(width, height) // 3
    logo = create_logo(logo_size)
    logo_x = (width - logo_size) // 2
    logo_y = int(height * 0.15)
    img.paste(logo, (logo_x, logo_y), logo)

    # Text below logo
    try:
        title_font = ImageFont.truetype("arial.ttf", 52)
        tagline_font = ImageFont.truetype("arial.ttf", 28)
    except:
        title_font = ImageFont.load_default()
        tagline_font = ImageFont.load_default()

    # Title
    title = "faster-whisper-hotkey"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
    title_y = logo_y + logo_size + int(height * 0.08)
    draw.text((title_x, title_y), title, fill=BRAND['white'], font=title_font)

    # Tagline
    tagline = "Hold hotkey. Speak. Release. Transcribed."
    tagline_bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
    tagline_x = (width - (tagline_bbox[2] - tagline_bbox[0])) // 2
    tagline_y = title_y + int(height * 0.08)
    draw.text((tagline_x, tagline_y), tagline, fill=(180, 180, 200), font=tagline_font)

    # Feature pills at bottom
    features = [
        "25+ Languages",
        "GPU Acceleration",
        "No Python Required",
    ]

    pill_y = int(height * 0.75)
    pill_spacing = 20
    pill_height = 44
    total_pills_width = 0

    try:
        pill_font = ImageFont.truetype("arial.ttf", 20)
    except:
        pill_font = ImageFont.load_default()

    pill_widths = []
    for feature in features:
        bbox = draw.textbbox((0, 0), feature, font=pill_font)
        text_width = bbox[2] - bbox[0]
        pill_width = text_width + 40
        pill_widths.append(pill_width)
        total_pills_width += pill_width

    total_width_with_spacing = total_pills_width + pill_spacing * (len(features) - 1)
    current_x = (width - total_width_with_spacing) // 2

    for i, (feature, pill_width) in enumerate(zip(features, pill_widths)):
        pill_color = BRAND['accent'] if i % 2 == 0 else BRAND['secondary']
        draw.rounded_rectangle(
            [(current_x, pill_y), (current_x + pill_width, pill_y + pill_height)],
            radius=22,
            fill=pill_color
        )

        text_bbox = draw.textbbox((0, 0), feature, font=pill_font)
        text_x = current_x + (pill_width - (text_bbox[2] - text_bbox[0])) // 2
        text_y = pill_y + (pill_height - (text_bbox[3] - text_bbox[1])) // 2
        draw.text((text_x, text_y - text_bbox[1]), feature,
                  fill=BRAND['white'], font=pill_font)

        current_x += pill_width + pill_spacing

    return img


def create_screenshot_mockup(width: int = 1200, height: int = 800) -> Image.Image:
    """Create a mockup application screenshot."""
    # Create window background
    img = Image.new('RGB', (width, height), BRAND['light'])
    draw = ImageDraw.Draw(img)

    # Window title bar
    title_bar_height = 40
    title_bar = create_gradient_image(width, title_bar_height, BRAND['primary'], BRAND['primary_dark'], 'horizontal')
    img.paste(title_bar, (0, 0))

    # Window controls (red, yellow, green circles)
    controls_y = title_bar_height // 2
    for i, color in enumerate([(239, 68, 68), (234, 179, 8), (34, 197, 94)]):
        draw.ellipse(
            [(20 + i * 30, controls_y - 8), (20 + i * 30 + 16, controls_y + 8)],
            fill=color
        )

    # Title bar text
    try:
        title_font = ImageFont.truetype("arial.ttf", 14)
    except:
        title_font = ImageFont.load_default()
    draw.text((width // 2 - 80, 12), "faster-whisper-hotkey", fill=BRAND['white'], font=title_font)

    # Sidebar
    sidebar_width = 250
    sidebar = Image.new('RGB', (sidebar_width, height - title_bar_height), (248, 250, 252))
    img.paste(sidebar, (0, title_bar_height))

    # Sidebar items (mock)
    items = ["Dashboard", "Settings", "Models", "History", "About"]
    item_y = title_bar_height + 20
    for item in items:
        draw.rounded_rectangle(
            [(10, item_y), (sidebar_width - 10, item_y + 36)],
            radius=8,
            fill=(226, 232, 240) if item == "Dashboard" else (255, 255, 255)
        )
        draw.text((30, item_y + 10), item, fill=BRAND['dark'], font=title_font)
        item_y += 50

    # Main content area - status card
    content_x = sidebar_width + 40
    content_y = title_bar_height + 40

    # Status card
    card_width = width - sidebar_width - 80
    card_height = 200

    # Card shadow
    draw.rounded_rectangle(
        [(content_x + 4, content_y + 4), (content_x + card_width + 4, content_y + card_height + 4)],
        radius=16,
        fill=(200, 200, 200)
    )

    # Card background
    draw.rounded_rectangle(
        [(content_x, content_y), (content_x + card_width, content_y + card_height)],
        radius=16,
        fill=BRAND['white']
    )

    # Card header
    try:
        header_font = ImageFont.truetype("arial.ttf", 20)
        status_font = ImageFont.truetype("arial.ttf", 32)
    except:
        header_font = ImageFont.load_default()
        status_font = ImageFont.load_default()

    draw.text((content_x + 24, content_y + 24), "Status", fill=BRAND['dark'], font=header_font)

    # Status indicator
    status_y = content_y + 70
    draw.ellipse(
        [(content_x + 24, status_y), (content_x + 48, status_y + 24)],
        fill=BRAND['accent']
    )
    draw.text((content_x + 60, status_y), "Model Loaded", fill=BRAND['dark'], font=header_font)

    # Model name
    draw.text((content_x + 24, status_y + 50), "parakeet-tdt-0.6b-v3",
              fill=BRAND['primary'], font=status_font)

    # Stats row
    stats_y = content_y + card_height + 40
    stats = [
        ("Device", "CPU"),
        ("Language", "Auto"),
        ("Hotkey", "F4"),
    ]

    stat_box_width = (card_width - 40) // 3
    for i, (label, value) in enumerate(stats):
        stat_x = content_x + 20 + i * (stat_box_width + 10)

        draw.rounded_rectangle(
            [(stat_x, stats_y), (stat_x + stat_box_width, stats_y + 80)],
            radius=12,
            fill=BRAND['white']
        )

        draw.text((stat_x + 16, stats_y + 16), label, fill=(100, 100, 100), font=title_font)
        draw.text((stat_x + 16, stats_y + 44), value, fill=BRAND['dark'], font=header_font)

    # Transcription preview area
    preview_y = stats_y + 100
    preview_height = 200

    draw.rounded_rectangle(
        [(content_x, preview_y), (content_x + card_width, preview_y + preview_height)],
        radius=16,
        fill=BRAND['white']
    )

    draw.text((content_x + 24, preview_y + 24), "Recent Transcription",
              fill=BRAND['dark'], font=header_font)

    # Fake transcription text
    transcription = "Hold the hotkey, speak, release. And baamm in your text field!"
    draw.text((content_x + 24, preview_y + 70), transcription,
              fill=(100, 100, 100), font=title_font)

    return img


def save_assets(output_dir: Path) -> None:
    """Generate and save all branding assets."""
    output_dir.mkdir(parents=True, exist_ok=True)

    branding_dir = output_dir / 'branding'
    branding_dir.mkdir(exist_ok=True)

    print("Generating branding assets...")
    print()

    # 1. High-resolution logos
    print("Creating high-resolution logos...")
    for size in [256, 512, 1024]:
        logo = create_logo(size, with_text=False)
        logo_path = branding_dir / f'logo_{size}x{size}.png'
        logo.save(logo_path, format='PNG', optimize=True)
        print(f"  Saved: {logo_path}")

    # Logo with text
    logo_text = create_logo(512, with_text=True)
    logo_text_path = branding_dir / 'logo_512x512_with_text.png'
    logo_text.save(logo_text_path, format='PNG', optimize=True)
    print(f"  Saved: {logo_text_path}")

    # 2. GitHub banner
    print("\nCreating GitHub banner...")
    github_banner = create_github_banner()
    banner_path = branding_dir / 'github_banner.png'
    github_banner.save(banner_path, format='PNG', optimize=True, quality=95)
    print(f"  Saved: {banner_path}")

    # Smaller version for README
    github_banner_small = create_github_banner(880, 220)
    banner_small_path = branding_dir / 'github_banner_small.png'
    github_banner_small.save(banner_small_path, format='PNG', optimize=True, quality=90)
    print(f"  Saved: {banner_small_path}")

    # 3. Social media / OpenGraph banners
    print("\nCreating social media banners...")
    for platform, width, height in [("generic", 1200, 630), ("twitter", 1600, 900)]:
        banner = create_social_media_banner(width, height, platform)
        banner_path = branding_dir / f'og_image_{width}x{height}.png'
        banner.save(banner_path, format='PNG', optimize=True, quality=95)
        print(f"  Saved: {banner_path}")

    # 4. Screenshot mockups
    print("\nCreating screenshot mockups...")
    screenshot = create_screenshot_mockup()
    screenshot_path = branding_dir / 'screenshot_main.png'
    screenshot.save(screenshot_path, format='PNG', optimize=True, quality=95)
    print(f"  Saved: {screenshot_path}")

    # Create a version showing the hotkey feature
    print("\nCreating feature highlight mockups...")
    # Could add more specific mockups here

    # 5. Favicon / smaller icons
    print("\nCreating favicons...")
    for size in [32, 64, 128]:
        logo = create_logo(size, with_text=False)
        logo_path = branding_dir / f'favicon_{size}x{size}.png'
        logo.save(logo_path, format='PNG', optimize=True)
        print(f"  Saved: {logo_path}")

    print()
    print(f"All branding assets saved to: {branding_dir}")
    print()
    print("Generated files:")
    for file in sorted(branding_dir.glob('*')):
        print(f"  - {file.name}")


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    output_dir = script_dir

    save_assets(output_dir)
    print()
    print("Brand assets ready for distribution!")


if __name__ == '__main__':
    main()
