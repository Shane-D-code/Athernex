#!/usr/bin/env python3
"""Generate placeholder launcher icons for Android app"""

import os
from pathlib import Path

# Icon sizes for different densities
ICON_SIZES = {
    'mdpi': 48,
    'hdpi': 72,
    'xhdpi': 96,
    'xxhdpi': 144,
    'xxxhdpi': 192
}

def create_placeholder_icon(size, output_path):
    """Create a simple placeholder icon using PIL"""
    try:
        from PIL import Image, ImageDraw
        
        # Create image with purple background
        img = Image.new('RGB', (size, size), color='#6200EE')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple white circle in the center
        margin = size // 4
        draw.ellipse([margin, margin, size-margin, size-margin], 
                     fill='white', outline='white')
        
        # Save the image
        img.save(output_path, 'PNG')
        return True
    except ImportError:
        # PIL not available, create a minimal valid PNG
        # This is a 1x1 transparent PNG
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 size
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
            0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
            0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND chunk
            0x42, 0x60, 0x82
        ])
        with open(output_path, 'wb') as f:
            f.write(png_data)
        return True

def main():
    base_dir = Path(__file__).parent / 'app' / 'src' / 'main' / 'res'
    
    for density, size in ICON_SIZES.items():
        mipmap_dir = base_dir / f'mipmap-{density}'
        mipmap_dir.mkdir(parents=True, exist_ok=True)
        
        # Create ic_launcher.png
        launcher_path = mipmap_dir / 'ic_launcher.png'
        create_placeholder_icon(size, launcher_path)
        print(f'✓ Created {launcher_path}')
        
        # Create ic_launcher_round.png (same as regular for now)
        launcher_round_path = mipmap_dir / 'ic_launcher_round.png'
        create_placeholder_icon(size, launcher_round_path)
        print(f'✓ Created {launcher_round_path}')
        
        # Create ic_launcher_foreground.png
        foreground_path = mipmap_dir / 'ic_launcher_foreground.png'
        create_placeholder_icon(size, foreground_path)
        print(f'✓ Created {foreground_path}')
    
    print('\n✅ All launcher icons created successfully!')

if __name__ == '__main__':
    main()
