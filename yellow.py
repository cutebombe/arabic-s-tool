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
# yellow.py
import re
import csv
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class YellowWord:
    """Represents a yellow-marked word with its metadata"""
    word: str
    original_markup: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    sequence: Optional[int] = None
    source_line_index: Optional[int] = None
    confidence: Optional[float] = None
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

class YellowWordParser:
    """Parses yellow word markup from text"""
    
    def __init__(self):
        # Define supported markup patterns
        self.patterns = [
            (r'\[\[y\]\](.*?)\[\[/y\]\]', '[[y]]{}[[/y]]'),  # [[y]]word[[/y]]
            (r'<y>(.*?)</y>', '<y>{}</y>'),                    # <y>word</y>
            (r'\{y\}(.*?)\{/y\}', '{{y}}{{/y}}'),             # {y}word{/y}
        ]
    
    def get_supported_patterns(self) -> List[str]:
        """Get list of supported markup patterns"""
        return [pattern[1] for pattern in self.patterns]
    
    def parse_text(self, text: str) -> List[YellowWord]:
        """Parse text and extract yellow-marked words"""
        yellow_words = []
        processed_text = text
        
        for pattern_regex, pattern_format in self.patterns:
            matches = list(re.finditer(pattern_regex, processed_text, re.IGNORECASE))
            
            for match in matches:
                word = match.group(1).strip()
                if word:
                    yellow_word = YellowWord(
                        word=word,
                        original_markup=match.group(0)
                    )
                    yellow_words.append(yellow_word)
        
        # Add sequence numbers
        for i, yellow_word in enumerate(yellow_words):
            yellow_word.sequence = i + 1
        
        return yellow_words
    
    def remove_markup(self, text: str) -> str:
        """Remove yellow markup from text, keeping only the words"""
        clean_text = text
        
        for pattern_regex, _ in self.patterns:
            clean_text = re.sub(pattern_regex, r'\1', clean_text, flags=re.IGNORECASE)
        
        return clean_text
    
    def get_word_positions(self, text: str) -> List[Dict[str, Any]]:
        """Get positions of yellow words in the clean text"""
        clean_text = self.remove_markup(text)
        yellow_words = self.parse_text(text)
        word_positions = []
        
        clean_words = clean_text.split()
        
        for yellow_word in yellow_words:
            # Find the position of this word in the clean text
            for i, clean_word in enumerate(clean_words):
                if clean_word.strip() == yellow_word.word.strip():
                    word_positions.append({
                        'word': yellow_word.word,
                        'position': i,
                        'yellow_word': yellow_word
                    })
                    break
        
        return word_positions

class YellowWordTracker:
    """Tracks yellow words timing and exports data"""
    
    def __init__(self):
        self.tracked_words: List[YellowWord] = []
        self.export_settings = {
            'csv_columns': ['sequence', 'word', 'start_time', 'end_time', 'source_line_index'],
            'include_confidence': False,
            'timestamp_format': 'seconds'  # 'seconds' or 'timecode'
        }
    
    def add_word_timing(
        self,
        yellow_word: YellowWord,
        start_time: float,
        end_time: float,
        source_line_index: Optional[int] = None,
        confidence: Optional[float] = None
    ) -> None:
        """Add timing information to a yellow word"""
        yellow_word.start_time = start_time
        yellow_word.end_time = end_time
        yellow_word.source_line_index = source_line_index
        yellow_word.confidence = confidence
        
        if yellow_word not in self.tracked_words:
            self.tracked_words.append(yellow_word)
    
    def distribute_timing(
        self,
        words: List[str],
        yellow_positions: List[int],
        segment_start: float,
        segment_end: float,
        yellow_words: List[YellowWord]
    ) -> None:
        """Distribute timing across words in a segment"""
        if not words or not yellow_positions:
            return
        
        segment_duration = segment_end - segment_start
        word_duration = segment_duration / len(words)
        
        yellow_idx = 0
        for i, word in enumerate(words):
            if i in yellow_positions and yellow_idx < len(yellow_words):
                word_start = segment_start + (i * word_duration)
                word_end = word_start + word_duration
                
                self.add_word_timing(
                    yellow_words[yellow_idx],
                    word_start,
                    word_end,
                    confidence=0.8  # Default confidence for distributed timing
                )
                yellow_idx += 1
    
    def format_timestamp(self, seconds: float, format_type: str = 'seconds') -> str:
        """Format timestamp according to specified format"""
        if format_type == 'timecode':
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
        else:
            return f"{seconds:.3f}"
    
    def export_to_csv(
        self,
        output_path: str,
        columns: Optional[List[str]] = None
    ) -> bool:
        """Export tracked words to CSV"""
        try:
            if columns is None:
                columns = self.export_settings['csv_columns']
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(columns)
                
                # Write data
                for word in self.tracked_words:
                    row = []
                    for col in columns:
                        if col == 'start_time' and word.start_time is not None:
                            row.append(self.format_timestamp(
                                word.start_time, 
                                self.export_settings['timestamp_format']
                            ))
                        elif col == 'end_time' and word.end_time is not None:
                            row.append(self.format_timestamp(
                                word.end_time, 
                                self.export_settings['timestamp_format']
                            ))
                        else:
                            row.append(getattr(word, col, ''))
                    writer.writerow(row)
            
            logger.info(f"Exported {len(self.tracked_words)} yellow words to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return False
    
    def export_to_json(
        self,
        output_path: str,
        include_settings: bool = True
    ) -> bool:
        """Export tracked words and settings to JSON"""
        try:
            export_data = {
                'yellow_words': [word.dict() for word in self.tracked_words],
                'summary': {
                    'total_words': len(self.tracked_words),
                    'export_timestamp': datetime.now().isoformat(),
                    'average_duration': self._calculate_average_duration()
                }
            }
            
            if include_settings:
                export_data['export_settings'] = self.export_settings
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported yellow word data to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            return False
    
    def _calculate_average_duration(self) -> Optional[float]:
        """Calculate average duration of yellow words"""
        durations = []
        for word in self.tracked_words:
            if word.start_time is not None and word.end_time is not None:
                durations.append(word.end_time - word.start_time)
        
        return sum(durations) / len(durations) if durations else None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about tracked yellow words"""
        total_duration = 0
        words_with_timing = 0
        confidence_scores = []
        
        for word in self.tracked_words:
            if word.start_time is not None and word.end_time is not None:
                total_duration += word.end_time - word.start_time
                words_with_timing += 1
            
            if word.confidence is not None:
                confidence_scores.append(word.confidence)
        
        return {
            'total_words': len(self.tracked_words),
            'words_with_timing': words_with_timing,
            'total_duration': total_duration,
            'average_duration': total_duration / words_with_timing if words_with_timing > 0 else 0,
            'average_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else None,
            'min_confidence': min(confidence_scores) if confidence_scores else None,
            'max_confidence': max(confidence_scores) if confidence_scores else None
        }
    
    def clear(self) -> None:
        """Clear all tracked words"""
        self.tracked_words.clear()
    
    def set_export_settings(self, **kwargs) -> None:
        """Update export settings"""
        self.export_settings.update(kwargs)
        # process.py
import os
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import moviepy.editor as mpy
import whisper
import srt
from PIL import Image
from datetime import datetime, timedelta

from text_render import TextRenderer
from yellow import YellowWordParser, YellowWordTracker, YellowWord

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Main video processing pipeline"""
    
    def __init__(self, text_renderer: TextRenderer, yellow_tracker: YellowWordTracker):
        self.text_renderer = text_renderer
        self.yellow_tracker = yellow_tracker
        self.yellow_parser = YellowWordParser()
        
        # Initialize Whisper model
        self.whisper_model = None
        
    def load_whisper_model(self, model_size: str = "medium") -> None:
        """Load Whisper model for transcription"""
        try:
            logger.info(f"Loading Whisper model: {model_size}")
            self.whisper_model = whisper.load_model(model_size)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def process(
        self,
        input_video: Optional[str] = None,
        input_captions: Optional[str] = None,
        input_text: Optional[str] = None,
        **params
    ) -> Dict[str, Any]:
        """Main processing pipeline"""
        
        try:
            logger.info("Starting video processing pipeline")
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Step 1: Handle inputs
                video_clip = None
                if input_video:
                    video_clip = mpy.VideoFileClip(input_video)
                    logger.info(f"Loaded video: {video_clip.w}x{video_clip.h}, {video_clip.duration}s")
                
                # Step 2: Get or generate subtitles
                subtitle_segments = []
                if input_captions:
                    subtitle_segments = self._load_captions(input_captions)
                elif input_text:
                    # Use provided text directly
                    subtitle_segments = self._text_to_segments(input_text, video_clip.duration if video_clip else 10.0)
                elif video_clip:
                    # Extract audio and transcribe
                    subtitle_segments = self._transcribe_video(video_clip, temp_path)
                else:
                    raise ValueError("No input provided")
                
                logger.info(f"Generated {len(subtitle_segments)} subtitle segments")
                
                # Step 3: Process yellow words
                all_yellow_words = []
                processed_segments = []
                
                for i, segment in enumerate(subtitle_segments):
                    # Parse yellow words from this segment
                    yellow_words = self.yellow_parser.parse_text(segment['text'])
                    clean_text = self.yellow_parser.remove_markup(segment['text'])
                    
                    # Update segment with clean text
                    processed_segment = segment.copy()
                    processed_segment['text'] = clean_text
                    processed_segment['yellow_words'] = yellow_words
                    processed_segment['words'] = clean_text.split()
                    
                    # Distribute timing for yellow words
                    if yellow_words:
                        yellow_positions = self._find_yellow_positions(processed_segment['words'], yellow_words)
                        self.yellow_tracker.distribute_timing(
                            processed_segment['words'],
                            yellow_positions,
                            segment['start'],
                            segment['end'],
                            yellow_words
                        )
                        all_yellow_words.extend(yellow_words)
                    
                    processed_segments.append(processed_segment)
                
                # Step 4: Create output video/image
                output_files = {}
                
                if video_clip:
                    output_video = self._create_subtitled_video(
                        video_clip, processed_segments, temp_path, **params
                    )
                    output_files['output_video'] = output_video
                else:
                    # Create preview image
                    preview_image = self._create_preview_image(
                        processed_segments[0]['text'] if processed_segments else "Sample Text",
                        **params
                    )
                    output_files['preview_image'] = preview_image
                
                # Step 5: Export yellow word data
                if all_yellow_words:
                    csv_file = temp_path / "yellow_words.csv"
                    json_file = temp_path / "yellow_data.json"
                    
                    self.yellow_tracker.export_to_csv(str(csv_file))
                    self.yellow_tracker.export_to_json(str(json_file))
                    
                    output_files['csv_file'] = str(csv_file)
                    output_files['json_file'] = str(json_file)
                
                # Step 6: Generate summary
                summary = {
                    'processing_time': datetime.now().isoformat(),
                    'segments_processed': len(processed_segments),
                    'yellow_words_found': len(all_yellow_words),
                    'yellow_statistics': self.yellow_tracker.get_statistics(),
                    'settings_used': params,
                    'video_info': {
                        'width': video_clip.w if video_clip else None,
                        'height': video_clip.h if video_clip else None,
                        'duration': video_clip.duration if video_clip else None,
                        'fps': video_clip.fps if video_clip else None
                    }
                }
                
                output_files['summary'] = summary
                
                logger.info("Video processing completed successfully")
                return output_files
                
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise
    
    def _load_captions(self, captions_file: str) -> List[Dict[str, Any]]:
        """Load captions from SRT or other caption files"""
        segments = []
        
        try:
            with open(captions_file, 'r', encoding='utf-8') as f:
                if captions_file.endswith('.srt'):
                    subtitles = list(srt.parse(f.read()))
                    for sub in subtitles:
                        segments.append({
                            'start': sub.start.total_seconds(),
                            'end': sub.end.total_seconds(),
                            'text': sub.content.strip()
                        })
                else:
                    # Handle plain text files
                    content = f.read().strip()
                    segments.append({
                        'start': 0.0,
                        'end': 10.0,  # Default duration
                        'text': content
                    })
            
            logger.info(f"Loaded {len(segments)} caption segments from {captions_file}")
            return segments
            
        except Exception as e:
            logger.error(f"Failed to load captions: {e}")
            raise
    
    def _text_to_segments(self, text: str, duration: float) -> List[Dict[str, Any]]:
        """Convert text to subtitle segments"""
        # Split text into sentences or chunks
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if not sentences:
            sentences = [text.strip()]
        
        segments = []
        segment_duration = duration / len(sentences)
        
        for i, sentence in enumerate(sentences):
            start_time = i * segment_duration
            end_time = start_time + segment_duration
            
            segments.append({
                'start': start_time,
                'end': end_time,
                'text': sentence
            })
        
        return segments
    
    def _transcribe_video(self, video_clip: mpy.VideoFileClip, temp_path: Path) -> List[Dict[str, Any]]:
        """Transcribe video audio using Whisper"""
        
        if not self.whisper_model:
            self.load_whisper_model()
        
        # Extract audio
        audio_file = temp_path / "audio.wav"
        video_clip.audio.write_audiofile(str(audio_file), verbose=False, logger=None)
        
        # Transcribe with word timestamps
        logger.info("Transcribing audio...")
        result = self.whisper_model.transcribe(
            str(audio_file),
            language="ar",
            word_timestamps=True,
            fp16=False
        )
        
        segments = []
        for segment in result["segments"]:
            segments.append({
                'start': segment["start"],
                'end': segment["end"],
                'text': segment["text"].strip(),
                'words': segment.get("words", [])
            })
        
        logger.info(f"
