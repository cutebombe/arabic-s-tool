# 🎬 Enhanced Arabic Video Subtitle Tool

A professional tool for adding Arabic subtitles to videos with advanced features including yellow word tracking, RTL text rendering, and modern UI.

## ✨ Features

- **🔤 Proper Arabic Text Rendering**: RTL support with arabic-reshaper and python-bidi
- **🎯 Word-by-Word Tracking**: Individual word highlighting with timing
- **🟡 Yellow Word Markup**: Track specific words with `[[y]]word[[/y]]` syntax
- **📊 Data Export**: CSV and JSON export of tracked words and timing
- **🎨 Customizable Styling**: Font size, colors, positioning, and effects
- **🤖 Auto-Transcription**: Whisper AI integration for automatic subtitle generation
- **💻 Modern UI**: Professional Gradio interface with tabs and previews
- **⚡ Batch Processing**: Handle multiple videos at once
- **🔧 Cross-Platform**: Windows, macOS, and Linux support

## 🚀 Quick Start

### One-Shot Installation

```bash
# Clone or download the project files
git clone <repository-url>
cd arabic-subtitle-tool

# Run the setup script (Linux/macOS)
chmod +x setup.sh
./setup.sh

# Or manual setup:
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Windows Setup

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## 📋 Requirements

- **Python 3.9+**
- **FFmpeg** (for video processing)
- **ImageMagick** (for text rendering)
- **System Arabic fonts** (auto-downloaded if missing)

## 🎯 Usage

### Web Interface

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Open your browser**: http://127.0.0.1:7860

3. **Upload your video** or enter text directly

4. **Configure settings**:
   - Font family and size
   - Max words per line (default: 3)
   - Yellow word tracking mode
   - Position and styling

5. **Process and download** your subtitled video

### CLI Usage

```bash
python app.py \
  --input video.mp4 \
  --text "هذا [[y]]الخبر[[/y]] مهم جدًا اليوم" \
  --font Cairo-Bold \
  --font-size 64 \
  --max-words-per-line 3 \
  --word-box-enabled True \
  --box-opacity 0.7 \
  --corner-radius 12 \
  --anchor bottom-center \
  --highlight track_highlight
```

## 🟡 Yellow Word Markup

Mark important words for tracking and highlighting:

**Supported formats**:
- `[[y]]الخبر[[/y]]` - Double brackets
- `<y>الخبر</y>` - XML-style tags  
- `{y}الخبر{/y}` - Curly braces

**Example**:
```arabic
هذا [[y]]الخبر[[/y]] مهم جدًا في [[y]]السوق[[/y]] اليوم
```

**Tracking modes**:
- **Track Only**: Log timing data without visual highlighting
- **Track + Highlight**: Show yellow text + export timing data

## 🎨 UI Tabs

### 🎯 Overlay Tab
- Upload videos/images
- Direct text input
- Quick settings
- Process and preview

### 🟡 Yellow Tracker Tab
- Configure tracking modes
- Test markup parsing
- Export settings

### 🎨 Fonts & Style Tab
- Font management
- Download Arabic fonts
- Text styling options
- Word box customization

### ⚙️ Advanced Tab
- Position controls
- Video quality settings
- Processing options

### 📋 Logs Tab
- Live processing logs
- Error tracking
- Debug information

## 📊 Output Files

### Video Processing
- **Subtitled video**: MP4 with embedded subtitles
- **CSV file**: Yellow word timing data
- **JSON file**: Complete processing metadata

### CSV Format
```csv
sequence,word,start_time,end_time,source_line_index
1,الخبر,2.450,3.120,0
2,السوق,8.750,9.340,1
```

### JSON Format
```json
{
  "yellow_words": [...],
  "summary": {
    "total_words": 5,
    "export_timestamp": "2024-01-15T10:30:00",
    "average_duration": 0.67
  },
  "export_settings": {...}
}
```

## 🔧 Configuration

### Font Management
The tool auto-downloads recommended Arabic fonts:
- **Cairo-Bold** (recommended)
- **Tajawal-Bold** 
- **Amiri-Bold**
- **Noto Sans Arabic**

Fonts are stored in `assets/fonts/` directory.

### Rendering Settings

**Text Styling**:
- Font size: 32-96px (default: 64px)
- Colors: Customizable text and stroke
- Stroke width: 0-5px (default: 2px)

**Word Boxes**:
- Opacity: 10-100% (default: 70%)
- Corner radius: 0-20px (default: 12px)
- Padding: Adjustable horizontal/vertical

**Layout**:
- Max words per line: 1-8 (default: 3)
- Position presets or custom coordinates
- RTL text flow support

## 🏗️ Architecture

### Core Modules

**`fonts.py`**: Font management and auto-download
- System font scanning
- Google Fonts integration
- Cross-platform font paths

**`text_render.py`**: Arabic text rendering
- RTL text shaping with arabic-reshaper
- Bidirectional algorithm support
- Word box drawing with rounded corners

**`yellow.py`**: Yellow word parsing and tracking
- Multiple markup format support
- Timing distribution algorithms
- CSV/JSON export functionality

**`process.py`**: Video processing pipeline
- Whisper integration for transcription
- MoviePy video compositing
- Frame-by-frame subtitle rendering

**`app.py`**: Main application and UI
- Gradio web interface
- CLI argument parsing
- Processing coordination

## 🔍 Troubleshooting

### Common Issues

**Font not displaying correctly**:
- Ensure Arabic fonts are installed
- Try different font families
- Check font file permissions

**Video processing slow**:
- Reduce video quality setting
- Increase thread count
- Use smaller font sizes

**Whisper transcription errors**:
- Check audio quality
- Ensure internet connection for model download
- Try different Whisper model sizes

**ImageMagick errors**:
- Update ImageMagick policy for video processing
- Install latest version
- Check PATH configuration

### Debug Mode
```bash
python app.py --verbose
# Check logs in app.log file
```

## 🧪 Testing

Test the tool with sample data:

```python
# Test yellow word parsing
from yellow import YellowWordParser
parser = YellowWordParser()
result = parser.parse_text("هذا [[y]]الخبر[[/y]] مهم")
print(result)

# Test font rendering
from fonts import FontManager
fm = FontManager()
fonts = fm.get_available_fonts()
print(f"Available fonts: {fonts}")
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality  
4. Update documentation
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **Whisper AI** for transcription
- **MoviePy** for video processing
- **Gradio** for the modern UI
- **arabic-reshaper** for RTL text support
- **Google Fonts** for Arabic typography
