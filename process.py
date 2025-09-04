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
            logger.info(f"Transcribed {len(segments)} segments")
        return segments
    
    def _find_yellow_positions(self, words: List[str], yellow_words: List[YellowWord]) -> List[int]:
        """Find positions of yellow words in the word list"""
        positions = []
        
        for yellow_word in yellow_words:
            for i, word in enumerate(words):
                if word.strip().lower() == yellow_word.word.strip().lower():
                    positions.append(i)
                    break
        
        return positions
    
    def _create_subtitled_video(
        self,
        video_clip: mpy.VideoFileClip,
        segments: List[Dict[str, Any]],
        temp_path: Path,
        **params
    ) -> str:
        """Create video with subtitles"""
        
        logger.info("Creating subtitled video...")
        
        # Get parameters
        font_name = params.get('font_family', 'Cairo-Bold')
        font_size = params.get('font_size', 64)
        max_words_per_line = params.get('max_words_per_line', 3)
        yellow_mode = params.get('yellow_mode', 'track_highlight')
        word_box_enabled = params.get('word_box_enabled', True)
        box_opacity = params.get('box_opacity', 0.7)
        corner_radius = params.get('corner_radius', 12)
        padding_x = params.get('padding_x', 8)
        padding_y = params.get('padding_y', 4)
        text_color = params.get('text_color', '#FFFFFF')
        stroke_width = params.get('stroke_width', 2)
        stroke_color = params.get('stroke_color', '#000000')
        position_preset = params.get('position_preset', 'bottom-center')
        custom_x = params.get('custom_x')
        custom_y = params.get('custom_y')
        video_quality = params.get('video_quality', 'fast')
        threads = params.get('threads', 4)
        
        # Convert colors
        text_rgb = self.text_renderer.hex_to_rgb(text_color)
        stroke_rgb = self.text_renderer.hex_to_rgb(stroke_color)
        box_rgba = (0, 0, 0, int(255 * box_opacity))
        
        # Get font
        font = self.text_renderer.get_font(font_name, font_size)
        
        # Create subtitle clips
        subtitle_clips = []
        
        for segment in segments:
            if not segment['text'].strip():
                continue
            
            # Split text into lines
            lines, _, _ = self.text_renderer.calculate_text_dimensions(
                segment['text'], font, 
                max_width=int(video_clip.w * 0.8),
                max_words_per_line=max_words_per_line
            )
            
            # Get yellow word indices for this segment
            yellow_word_indices = []
            if yellow_mode == 'track_highlight':
                for yellow_word in segment.get('yellow_words', []):
                    for i, word in enumerate(segment['words']):
                        if word.strip().lower() == yellow_word.word.strip().lower():
                            yellow_word_indices.append(i)
                            break
            
            # Create word-level clips for tracking
            words = segment['words']
            word_duration = (segment['end'] - segment['start']) / len(words) if words else 0
            
            for word_idx, word in enumerate(words):
                word_start = segment['start'] + (word_idx * word_duration)
                word_end = word_start + word_duration
                
                # Determine position
                custom_position = None
                if position_preset == 'custom' and custom_x is not None and custom_y is not None:
                    custom_position = (custom_x, custom_y)
                
                # Create frame for this word
                def make_frame(t):
                    # Determine which words are currently active
                    current_time = word_start + t
                    current_word_indices = []
                    
                    # Find all words that should be highlighted at this time
                    for i, w in enumerate(words):
                        w_start = segment['start'] + (i * word_duration)
                        w_end = w_start + word_duration
                        if w_start <= current_time <= w_end:
                            current_word_indices.append(i)
                    
                    # Create subtitle frame
                    frame = self.text_renderer.create_subtitle_frame(
                        video_clip.w, video_clip.h,
                        lines, current_word_indices, font,
                        position_preset, custom_position,
                        text_rgb, stroke_rgb, stroke_width,
                        word_box_enabled, box_rgba,
                        corner_radius, padding_x, padding_y,
                        yellow_word_indices, (255, 255, 0)
                    )
                    
                    return frame[:, :, :3]  # Remove alpha channel for MoviePy
                
                # Create clip for this word
                word_clip = mpy.VideoClip(make_frame, duration=word_duration)
                word_clip = word_clip.set_start(word_start)
                subtitle_clips.append(word_clip)
        
        # Composite video with subtitles
        logger.info("Compositing video with subtitles...")
        final_video = mpy.CompositeVideoClip([video_clip] + subtitle_clips)
        
        # Export video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = temp_path / f"subtitled_video_{timestamp}.mp4"
        
        logger.info("Exporting final video...")
        final_video.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            fps=video_clip.fps,
            threads=threads,
            preset=video_quality,
            verbose=False,
            logger=None
        )
        
        logger.info(f"Video exported to {output_path}")
        return str(output_path)
    
    def _create_preview_image(self, text: str, **params) -> str:
        """Create a preview image of the subtitle rendering"""
        
        font_name = params.get('font_family', 'Cairo-Bold')
        font_size = params.get('font_size', 64)
        max_words_per_line = params.get('max_words_per_line', 3)
        
        preview_img = self.text_renderer.create_preview_image(
            text, font_name, font_size, max_words_per_line
        )
        
        # Save preview image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"preview_{timestamp}.png"
        preview_img.save(output_path)
        
        return output_pathLoading Whisper model: {model_size}")
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
