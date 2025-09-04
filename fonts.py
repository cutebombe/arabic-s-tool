# fonts.py
import os
import platform
import requests
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import zipfile
import tempfile

logger = logging.getLogger(__name__)

class FontManager:
    """Manages Arabic fonts for the subtitle tool"""
    
    def __init__(self, font_dir: str = "assets/fonts"):
        self.font_dir = Path(font_dir)
        self.font_dir.mkdir(parents=True, exist_ok=True)
        
        # Recommended Arabic fonts with download URLs
        self.recommended_fonts = {
            "Cairo-Bold": {
                "url": "https://fonts.google.com/download?family=Cairo",
                "filename": "Cairo-Bold.ttf",
                "weight": "bold"
            },
            "Tajawal-Bold": {
                "url": "https://fonts.google.com/download?family=Tajawal",
                "filename": "Tajawal-Bold.ttf",
                "weight": "bold"
            },
            "Amiri-Bold": {
                "url": "https://fonts.google.com/download?family=Amiri",
                "filename": "Amiri-Bold.ttf",
                "weight": "bold"
            },
            "Noto Sans Arabic": {
                "url": "https://fonts.google.com/download?family=Noto+Sans+Arabic",
                "filename": "NotoSansArabic-Bold.ttf",
                "weight": "bold"
            }
        }
        
        self.system_font_paths = self._get_system_font_paths()
        self.available_fonts = {}
        
    def _get_system_font_paths(self) -> List[Path]:
        """Get system font directories based on OS"""
        system = platform.system().lower()
        paths = []
        
        if system == "windows":
            paths = [
                Path("C:/Windows/Fonts"),
                Path(os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts"))
            ]
        elif system == "darwin":  # macOS
            paths = [
                Path("/System/Library/Fonts"),
                Path("/Library/Fonts"),
                Path(os.path.expanduser("~/Library/Fonts"))
            ]
        else:  # Linux
            paths = [
                Path("/usr/share/fonts"),
                Path("/usr/local/share/fonts"),
                Path(os.path.expanduser("~/.fonts")),
                Path(os.path.expanduser("~/.local/share/fonts"))
            ]
        
        return [p for p in paths if p.exists()]
    
    def scan_fonts(self) -> Dict[str, str]:
        """Scan for available Arabic fonts"""
        self.available_fonts = {}
        
        # Scan custom font directory
        for font_file in self.font_dir.glob("*.ttf"):
            font_name = font_file.stem
            self.available_fonts[font_name] = str(font_file)
            logger.info(f"Found custom font: {font_name}")
        
        # Scan system fonts
        arabic_keywords = ["arabic", "noto", "cairo", "tajawal", "amiri", "droid", "kufi"]
        
        for font_path in self.system_font_paths:
            try:
                for font_file in font_path.rglob("*.ttf"):
                    font_name = font_file.stem.lower()
                    if any(keyword in font_name for keyword in arabic_keywords):
                        display_name = font_file.stem
                        if display_name not in self.available_fonts:
                            self.available_fonts[display_name] = str(font_file)
                            logger.info(f"Found system font: {display_name}")
            except (PermissionError, OSError):
                continue
        
        # Add fallback fonts if nothing found
        if not self.available_fonts:
            self.available_fonts["Default"] = None
            logger.warning("No Arabic fonts found, using system default")
        
        return self.available_fonts
    
    def get_available_fonts(self) -> List[str]:
        """Get list of available font names"""
        if not self.available_fonts:
            self.scan_fonts()
        return list(self.available_fonts.keys())
    
    def get_font_path(self, font_name: str) -> Optional[str]:
        """Get the path to a specific font"""
        if not self.available_fonts:
            self.scan_fonts()
        return self.available_fonts.get(font_name)
    
    def download_font(self, font_name: str) -> bool:
        """Download a specific font"""
        if font_name not in self.recommended_fonts:
            logger.error(f"Font {font_name} not in recommended list")
            return False
        
        font_info = self.recommended_fonts[font_name]
        target_path = self.font_dir / font_info["filename"]
        
        if target_path.exists():
            logger.info(f"Font {font_name} already exists")
            return True
        
        try:
            logger.info(f"Downloading font: {font_name}")
            response = requests.get(font_info["url"], timeout=30)
            response.raise_for_status()
            
            # Handle zip files (Google Fonts typically return zip)
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / "font.zip"
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                
                # Extract and find the bold variant
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                    
                    # Look for bold variant
                    extracted_files = list(Path(temp_dir).glob("*.ttf"))
                    bold_font = None
                    
                    for font_file in extracted_files:
                        if "bold" in font_file.name.lower():
                            bold_font = font_file
                            break
                    
                    if not bold_font and extracted_files:
                        bold_font = extracted_files[0]  # Fallback to first font
                    
                    if bold_font:
                        bold_font.rename(target_path)
                        logger.info(f"Successfully downloaded: {font_name}")
                        return True
            
        except Exception as e:
            logger.error(f"Failed to download font {font_name}: {e}")
            return False
        
        return False
    
    def setup_fonts(self) -> None:
        """Setup fonts on first run"""
        self.scan_fonts()
        
        # Download recommended fonts if not available
        if len(self.available_fonts) < 2:  # Only default font available
            logger.info("Downloading recommended Arabic fonts...")
            for font_name in ["Cairo-Bold", "Tajawal-Bold"]:
                self.download_font(font_name)
            
            # Rescan after download
            self.scan_fonts()
    
    def get_font_info(self, font_name: str) -> Dict:
        """Get detailed information about a font"""
        font_path = self.get_font_path(font_name)
        
        info = {
            "name": font_name,
            "path": font_path,
            "available": font_path is not None,
            "type": "system" if font_path and str(self.font_dir) not in font_path else "custom"
        }
        
        if font_name in self.recommended_fonts:
            info.update(self.recommended_fonts[font_name])
            info["recommended"] = True
        else:
            info["recommended"] = False
        
        return info
