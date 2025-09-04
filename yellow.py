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
