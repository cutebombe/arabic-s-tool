# text_render.py
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Dict, Optional, Any
import arabic_reshaper
from bidi.algorithm import get_display
import logging
from pathlib import Path
import math

logger = logging.getLogger(__name__)

class TextRenderer:
    """Handles Arabic text rendering with proper RTL support"""
    
    def __init__(self, font_manager):
        self.font_manager = font_manager
        
        # Arabic reshaper configuration
        self.reshaper_config = {
            'delete_harakat': False,
            'support_zwj': True,
            'shift_harakat_position': True
        }
    
    def reshape_arabic_text(self, text: str) -> str:
        """Reshape Arabic text for proper display"""
        try:
            # Reshape Arabic characters
            reshaped_text = arabic_reshaper.reshape(text, **self.reshaper_config)
            # Apply bidirectional algorithm
            display_text = get_display(reshaped_text)
            return display_text
        except Exception as e:
            logger.warning(f"Failed to reshape Arabic text: {e}")
            return text
    
    def get_font(self, font_name: str, font_size: int) -> ImageFont.FreeTypeFont:
        """Get font object with fallback handling"""
        font_path = self.font_manager.get_font_path(font_name)
        
        try:
            if font_path and Path(font_path).exists():
                return ImageFont.truetype(font_path, font_size)
            else:
                logger.warning(f"Font {font_name} not found, using default")
                return ImageFont.load_default()
        except Exception as e:
            logger.error(f"Error loading font {font_name}: {e}")
            return ImageFont.load_default()
    
    def calculate_text_dimensions(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: Optional[int] = None,
        max_words_per_line: int = 3
    ) -> Tuple[List[str], int, int]:
        """Calculate text dimensions with word wrapping"""
        
        # Create temporary image for measurement
        temp_img = Image.new('RGBA', (1, 1))
        draw = ImageDraw.Draw(temp_img)
        
        # Split text into words
        words = text.strip().split()
        lines = []
        current_line = []
        
        for word in words:
            # Check if adding this word would exceed max words per line
            if len(current_line) >= max_words_per_line:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            else:
                current_line.append(word)
                
                # Also check width if max_width is specified
                if max_width:
                    line_text = self.reshape_arabic_text(' '.join(current_line))
                    bbox = draw.textbbox((0, 0), line_text, font=font)
                    line_width = bbox[2] - bbox[0]
                    
                    if line_width > max_width and len(current_line) > 1:
                        # Remove last word and start new line
                        current_line.pop()
                        lines.append(' '.join(current_line))
                        current_line = [word]
        
        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate total dimensions
        max_line_width = 0
        total_height = 0
        line_spacing = font.size * 0.2  # 20% of font size for line spacing
        
        for line in lines:
            shaped_line = self.reshape_arabic_text(line)
            bbox = draw.textbbox((0, 0), shaped_line, font=font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            
            max_line_width = max(max_line_width, line_width)
            total_height += line_height + line_spacing
        
        total_height -= line_spacing  # Remove last line spacing
        
        return lines, int(max_line_width), int(total_height)
    
    def draw_word_box(
        self,
        draw: ImageDraw.Draw,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.FreeTypeFont,
        box_color: Tuple[int, int, int, int] = (0, 0, 0, 179),  # 70% opacity black
        corner_radius: int =
