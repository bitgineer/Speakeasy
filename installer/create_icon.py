#!/usr/bin/env python3
"""
Create app icon for faster-whisper-hotkey.

Generates a multi-resolution ICO file with a modern microphone/waveform design.
The icon includes sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path


def draw_icon_base(size: int, bg_color: tuple) -> Image.Image:
    """Draw the base icon with background color."""
    img = Image.new('RGBA', (size, size), bg_color + (255,))
    draw = ImageDraw.Draw(img)
    return img, draw


def draw_microphone_icon(size: int, bg_color: tuple, fg_color: tuple) -> Image.Image:
    """Draw a modern microphone icon with sound waves."""
    img, draw = draw_icon_base(size, bg_color)

    # Scale factors
    scale = size / 256
    center = size // 2

    # Draw microphone body (rounded rectangle)
    mic_width = int(64 * scale)
    mic_height = int(100 * scale)
    mic_x = (size - mic_width) // 2
    mic_y = (size - mic_height) // 2 - int(10 * scale)

    # Microphone body
    corner_radius = int(32 * scale)
    draw.rounded_rectangle(
        [mic_x, mic_y, mic_x + mic_width, mic_y + mic_height],
        radius=corner_radius,
        fill=fg_color
    )

    # Microphone stand
    stand_width = int(8 * scale)
    stand_height = int(30 * scale)
    stand_x = center - stand_width // 2
    stand_y = mic_y + mic_height + int(5 * scale)
    draw.rectangle(
        [stand_x, stand_y, stand_x + stand_width, stand_y + stand_height],
        fill=fg_color
    )

    # Base
    base_width = int(80 * scale)
    base_height = int(12 * scale)
    base_x = (size - base_width) // 2
    base_y = stand_y + stand_height
    draw.rounded_rectangle(
        [base_x, base_y, base_x + base_width, base_y + base_height],
        radius=int(6 * scale),
        fill=fg_color
    )

    # Draw sound waves
    wave_count = 3
    wave_spacing = int(20 * scale)
    wave_width = int(4 * scale)
    wave_start_x = mic_x + mic_width + int(15 * scale)

    for i in range(wave_count):
        wave_x = wave_start_x + i * wave_spacing
        wave_height = int((30 + i * 15) * scale)
        wave_y = center - wave_height // 2
        draw.rounded_rectangle(
            [wave_x, wave_y, wave_x + wave_width, wave_y + wave_height],
            radius=int(2 * scale),
            fill=fg_color
        )

    return img


def draw_gradient_background(size: int, color_start: tuple, color_end: tuple) -> Image.Image:
    """Draw a gradient background."""
    img = Image.new('RGBA', (size, size))
    draw = ImageDraw.Draw(img)

    for y in range(size):
        ratio = y / size
        r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
        g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
        b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
        draw.rectangle([(0, y), (size, y + 1)], fill=(r, g, b, 255))

    return img


def create_icon() -> Image.Image:
    """Create the multi-resolution icon.

    Using a modern blue gradient background with white microphone.
    Color scheme: Blue gradient (#2563EB to #1D4ED8) with white icon.
    """
    # Modern blue gradient colors (Tailwind blue-600 to blue-700)
    bg_color_start = (37, 99, 235)   # #2563EB
    bg_color_end = (29, 78, 216)     # #1D4ED8
    fg_color = (255, 255, 255)       # White

    # Create different sizes
    sizes = [16, 32, 48, 64, 128, 256]

    icons = []
    for size in sizes:
        # For very small sizes, use solid background
        if size <= 32:
            img = draw_microphone_icon(size, bg_color_start, fg_color)
        else:
            # For larger sizes, add gradient
            bg_img = draw_gradient_background(size, bg_color_start, bg_color_end)
            fg_img = draw_microphone_icon(size, (0, 0, 0), fg_color)

            # Composite: background with icon
            img = Image.alpha_composite(
                bg_img.convert('RGBA'),
                fg_img.convert('RGBA')
            )

        icons.append(img)

    return icons


def save_ico(icons: list, output_path: Path):
    """Save icons as ICO file with all sizes."""
    # ICO format requires specific handling for sizes > 256
    # PIL handles this automatically when we pass a list
    icons[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in icons],
        bitmap_format='png'
    )
    print(f"Icon saved to: {output_path}")


def save_png(icons: list, output_dir: Path):
    """Save individual PNG files for reference."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for icon in icons:
        size = icon.width
        png_path = output_dir / f"app_icon_{size}x{size}.png"
        icon.save(png_path, format='PNG')
        print(f"PNG saved to: {png_path}")


def main():
    """Main entry point."""
    # Get the script directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / 'icons'
    ico_path = script_dir / 'app_icon.ico'

    print("Creating app icon...")
    print("Design: Modern microphone with sound waves")
    print("Colors: Blue gradient background, white foreground")
    print()

    # Create icons
    icons = create_icon()

    # Save as ICO (Windows icon format)
    save_ico(icons, ico_path)

    # Save individual PNGs
    save_png(icons, output_dir)

    print()
    print(f"Icon sizes created: {[f'{img.width}x{img.height}' for img in icons]}")
    print()
    print("Icon files ready for PyInstaller!")


if __name__ == '__main__':
    main()
