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
        corner_radius: int = 12,
        padding_x: int = 8,
        padding_y: int = 4
    ) -> Tuple[int, int, int, int]:
        """Draw a rounded rectangle box behind text"""
        
        # Reshape text for proper measurement
        shaped_text = self.reshape_arabic_text(text)
        
        # Get text dimensions
        bbox = draw.textbbox(position, shaped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate box coordinates with padding
        x, y = position
        box_left = x - padding_x
        box_top = y - padding_y
        box_right = x + text_width + padding_x
        box_bottom = y + text_height + padding_y
        
        # Draw rounded rectangle
        self._draw_rounded_rectangle(
            draw, 
            (box_left, box_top, box_right, box_bottom),
            corner_radius,
            fill=box_color
        )
        
        return (box_left, box_top, box_right, box_bottom)
    
    def _draw_rounded_rectangle(
        self,
        draw: ImageDraw.Draw,
        coords: Tuple[int, int, int, int],
        radius: int,
        fill: Tuple[int, int, int, int]
    ) -> None:
        """Draw a rounded rectangle"""
        x1, y1, x2, y2 = coords
        
        # Draw the main rectangle
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
        
        # Draw the corners
        draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill)
        draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill)
        draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill)
        draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill)
    
    def draw_text_with_stroke(
        self,
        draw: ImageDraw.Draw,
        position: Tuple[int, int],
        text: str,
        font: ImageFont.FreeTypeFont,
        fill_color: Tuple[int, int, int] = (255, 255, 255),
        stroke_color: Tuple[int, int, int] = (0, 0, 0),
        stroke_width: int = 2
    ) -> None:
        """Draw text with stroke outline"""
        
        shaped_text = self.reshape_arabic_text(text)
        x, y = position
        
        # Draw stroke
        if stroke_width > 0:
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x + dx, y + dy), shaped_text, font=font, fill=stroke_color)
        
        # Draw main text
        draw.text((x, y), shaped_text, font=font, fill=fill_color)
    
    def create_subtitle_frame(
        self,
        video_width: int,
        video_height: int,
        lines: List[str],
        current_word_indices: List[int],
        font: ImageFont.FreeTypeFont,
        position_preset: str = "bottom-center",
        custom_position: Optional[Tuple[float, float]] = None,
        text_color: Tuple[int, int, int] = (255, 255, 255),
        stroke_color: Tuple[int, int, int] = (0, 0, 0),
        stroke_width: int = 2,
        word_box_enabled: bool = True,
        box_color: Tuple[int, int, int, int] = (0, 0, 0, 179),
        corner_radius: int = 12,
        padding_x: int = 8,
        padding_y: int = 4,
        yellow_word_indices: Optional[List[int]] = None,
        yellow_color: Tuple[int, int, int] = (255, 255, 0)
    ) -> np.ndarray:
        """Create a subtitle frame overlay"""
        
        # Create transparent image
        img = Image.new('RGBA', (video_width, video_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if not lines:
            return np.array(img)
        
        # Calculate text dimensions
        line_height = font.size + 10  # Add some spacing
        total_text_height = len(lines) * line_height
        
        # Determine position
        if custom_position:
            text_x = int(video_width * custom_position[0] / 100)
            text_y = int(video_height * custom_position[1] / 100)
        else:
            # Use preset positions
            if position_preset == "bottom-center":
                text_x = video_width // 2
                text_y = video_height - total_text_height - 50
            elif position_preset == "bottom-left":
                text_x = 50
                text_y = video_height - total_text_height - 50
            elif position_preset == "bottom-right":
                text_x = video_width - 50
                text_y = video_height - total_text_height - 50
            elif position_preset == "center":
                text_x = video_width // 2
                text_y = (video_height - total_text_height) // 2
            elif position_preset == "top-center":
                text_x = video_width // 2
                text_y = 50
            else:
                text_x = video_width // 2
                text_y = video_height - total_text_height - 50
        
        # Draw each line
        current_y = text_y
        global_word_index = 0
        
        for line_idx, line in enumerate(lines):
            words = line.split()
            
            # Calculate line width for centering
            shaped_line = self.reshape_arabic_text(line)
            bbox = draw.textbbox((0, 0), shaped_line, font=font)
            line_width = bbox[2] - bbox[0]
            
            # Adjust x position for centering (RTL)
            if "center" in position_preset:
                line_x = text_x - line_width // 2
            elif "right" in position_preset:
                line_x = text_x - line_width
            else:
                line_x = text_x
            
            # Draw word boxes and text for each word in the line
            current_x = line_x + line_width  # Start from right for RTL
            
            for word_idx, word in enumerate(reversed(words)):  # Reverse for RTL
                shaped_word = self.reshape_arabic_text(word)
                word_bbox = draw.textbbox((0, 0), shaped_word, font=font)
                word_width = word_bbox[2] - word_bbox[0]
                
                # Position for this word
                word_x = current_x - word_width
                word_pos = (word_x, current_y)
                
                # Determine word color
                is_current_word = global_word_index in current_word_indices
                is_yellow_word = yellow_word_indices and global_word_index in yellow_word_indices
                
                # Draw word box if enabled and word is currently being spoken
                if word_box_enabled and is_current_word:
                    self.draw_word_box(
                        draw, word, word_pos, font,
                        box_color, corner_radius, padding_x, padding_y
                    )
                
                # Determine text color
                word_color = text_color
                if is_yellow_word:
                    word_color = yellow_color
                
                # Draw the word
                self.draw_text_with_stroke(
                    draw, word_pos, word,
                    font, word_color, stroke_color, stroke_width
                )
                
                # Update position for next word (moving left)
                current_x = word_x - 10  # Add word spacing
                global_word_index += 1
            
            current_y += line_height
        
        return np.array(img)
    
    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def create_preview_image(
        self,
        text: str,
        font_name: str,
        font_size: int,
        max_words_per_line: int = 3,
        width: int = 800,
        height: int = 200
    ) -> Image.Image:
        """Create a preview image of the text rendering"""
        
        font = self.get_font(font_name, font_size)
        lines, text_width, text_height = self.calculate_text_dimensions(
            text, font, max_width=width-40, max_words_per_line=max_words_per_line
        )
        
        # Create preview image
        img = Image.new('RGBA', (width, height), (50, 50, 50, 255))
        draw = ImageDraw.Draw(img)
        
        # Center the text
        start_y = (height - text_height) // 2
        current_y = start_y
        line_height = font_size + 10
        
        for line in lines:
            shaped_line = self.reshape_arabic_text(line)
            bbox = draw.textbbox((0, 0), shaped_line, font=font)
            line_width = bbox[2] - bbox[0]
            line_x = (width - line_width) // 2
            
            # Draw with stroke
            self.draw_text_with_stroke(
                draw, (line_x, current_y), line, font,
                (255, 255, 255), (0, 0, 0), 2
            )
            
            current_y += line_height
        
        return img
