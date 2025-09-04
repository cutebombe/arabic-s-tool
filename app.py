# app.py
import gradio as gr
import argparse
import sys
from pathlib import Path
import logging
from typing import Optional, Dict, Any, List, Tuple
import json
import csv
from datetime import datetime

# Import our modules
from fonts import FontManager
from text_render import TextRenderer
from yellow import YellowWordParser, YellowWordTracker
from process import VideoProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ArabicSubtitleApp:
    def __init__(self):
        self.font_manager = FontManager()
        self.text_renderer = TextRenderer(self.font_manager)
        self.yellow_parser = YellowWordParser()
        self.yellow_tracker = YellowWordTracker()
        self.video_processor = VideoProcessor(self.text_renderer, self.yellow_tracker)
        
        # Initialize fonts
        self.font_manager.setup_fonts()
        
    def create_gradio_interface(self):
        """Create the main Gradio interface"""
        
        with gr.Blocks(
            title="Arabic Video Subtitle Tool",
            theme=gr.themes.Soft(),
            css="""
            .main-header {
                text-align: center;
                color: #2c3e50;
                margin-bottom: 30px;
            }
            .tab-content {
                padding: 20px;
            }
            .preview-container {
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
            }
            """
        ) as interface:
            
            gr.HTML("<h1 class='main-header'>🎬 Arabic Video Subtitle Tool</h1>")
            
            with gr.Tabs():
                # Main Processing Tab
                with gr.Tab("🎯 Overlay", elem_classes="tab-content"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            # Input section
                            gr.HTML("<h3>📁 Input Files</h3>")
                            input_video = gr.File(
                                label="Upload Video/Image",
                                file_types=['.mp4', '.mov', '.avi', '.mkv', '.jpg', '.png'],
                                type="filepath"
                            )
                            input_captions = gr.File(
                                label="Captions File (Optional)",
                                file_types=['.srt', '.vtt', '.txt'],
                                type="filepath"
                            )
                            input_text = gr.Textbox(
                                label="Direct Text Input",
                                placeholder="Enter Arabic text with yellow word markup: [[y]]الخبر[[/y]]",
                                lines=5,
                                rtl=True
                            )
                            
                            # Quick settings
                            gr.HTML("<h3>⚡ Quick Settings</h3>")
                            font_family = gr.Dropdown(
                                label="Font Family",
                                choices=self.font_manager.get_available_fonts(),
                                value="Cairo-Bold",
                                interactive=True
                            )
                            font_size = gr.Slider(
                                label="Font Size",
                                minimum=32,
                                maximum=96,
                                value=64,
                                step=2
                            )
                            max_words_per_line = gr.Slider(
                                label="Max Words per Line",
                                minimum=1,
                                maximum=8,
                                value=3,
                                step=1
                            )
                            
                            process_btn = gr.Button(
                                "🚀 Process Video",
                                variant="primary",
                                size="lg"
                            )
                        
                        with gr.Column(scale=1):
                            # Preview section
                            gr.HTML("<h3>👁️ Preview</h3>")
                            preview_output = gr.Video(
                                label="Output Preview",
                                elem_classes="preview-container"
                            )
                            
                            # Download section
                            gr.HTML("<h3>📥 Downloads</h3>")
                            download_video = gr.File(label="Download Video")
                            download_csv = gr.File(label="Download CSV (Yellow Words)")
                            download_json = gr.File(label="Download JSON (Settings)")
                            
                            # Summary
                            summary_output = gr.JSON(label="Process Summary")
                
                # Yellow Word Tracking Tab
                with gr.Tab("🟡 Yellow Tracker", elem_classes="tab-content"):
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("<h3>Yellow Word Settings</h3>")
                            yellow_mode = gr.Radio(
                                label="Tracking Mode",
                                choices=[
                                    ("Track Only (Log timing)", "track_only"),
                                    ("Track + Highlight (Yellow + Log)", "track_highlight")
                                ],
                                value="track_highlight"
                            )
                            
                            yellow_markup_preview = gr.Textbox(
                                label="Markup Preview",
                                placeholder="[[y]]word[[/y]] or <y>word</y> or {y}word{/y}",
                                lines=3
                            )
                            
                            test_yellow_btn = gr.Button("Test Yellow Parsing")
                            yellow_test_output = gr.JSON(label="Parsed Yellow Words")
                        
                        with gr.Column():
                            gr.HTML("<h3>Export Settings</h3>")
                            csv_columns = gr.CheckboxGroup(
                                label="CSV Columns",
                                choices=[
                                    "sequence", "word", "start_time", 
                                    "end_time", "source_line_index", "confidence"
                                ],
                                value=["sequence", "word", "start_time", "end_time"]
                            )
                
                # Fonts & Style Tab
                with gr.Tab("🎨 Fonts & Style", elem_classes="tab-content"):
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("<h3>Font Management</h3>")
                            refresh_fonts_btn = gr.Button("🔄 Refresh Font List")
                            available_fonts = gr.Dropdown(
                                label="Available Fonts",
                                choices=self.font_manager.get_available_fonts(),
                                value="Cairo-Bold"
                            )
                            download_font_btn = gr.Button("📥 Download Missing Fonts")
                            font_status = gr.Textbox(label="Font Status", interactive=False)
                            
                            gr.HTML("<h3>Text Styling</h3>")
                            text_color = gr.ColorPicker(label="Text Color", value="#FFFFFF")
                            stroke_width = gr.Slider(
                                label="Stroke Width",
                                minimum=0,
                                maximum=5,
                                value=2,
                                step=1
                            )
                            stroke_color = gr.ColorPicker(label="Stroke Color", value="#000000")
                        
                        with gr.Column():
                            gr.HTML("<h3>Word Box Settings</h3>")
                            word_box_enabled = gr.Checkbox(
                                label="Enable Per-Word Background Tracking",
                                value=True
                            )
                            box_opacity = gr.Slider(
                                label="Box Opacity",
                                minimum=0.1,
                                maximum=1.0,
                                value=0.7,
                                step=0.1
                            )
                            corner_radius = gr.Slider(
                                label="Corner Radius",
                                minimum=0,
                                maximum=20,
                                value=12,
                                step=1
                            )
                            padding_x = gr.Slider(
                                label="Horizontal Padding",
                                minimum=0,
                                maximum=20,
                                value=8,
                                step=1
                            )
                            padding_y = gr.Slider(
                                label="Vertical Padding",
                                minimum=0,
                                maximum=20,
                                value=4,
                                step=1
                            )
                
                # Advanced Tab
                with gr.Tab("⚙️ Advanced", elem_classes="tab-content"):
                    with gr.Row():
                        with gr.Column():
                            gr.HTML("<h3>Position & Layout</h3>")
                            position_preset = gr.Dropdown(
                                label="Position Preset",
                                choices=[
                                    "bottom-center", "bottom-left", "bottom-right",
                                    "center", "top-center", "custom"
                                ],
                                value="bottom-center"
                            )
                            custom_x = gr.Slider(
                                label="Custom X Position (%)",
                                minimum=0,
                                maximum=100,
                                value=50,
                                visible=False
                            )
                            custom_y = gr.Slider(
                                label="Custom Y Position (%)",
                                minimum=0,
                                maximum=100,
                                value=85,
                                visible=False
                            )
                            
                            def toggle_custom_position(preset):
                                return [
                                    gr.update(visible=preset == "custom"),
                                    gr.update(visible=preset == "custom")
                                ]
                            
                            position_preset.change(
                                toggle_custom_position,
                                inputs=[position_preset],
                                outputs=[custom_x, custom_y]
                            )
                        
                        with gr.Column():
                            gr.HTML("<h3>Processing Options</h3>")
                            video_quality = gr.Dropdown(
                                label="Video Quality",
                                choices=["ultrafast", "fast", "medium", "slow"],
                                value="fast"
                            )
                            fps_override = gr.Number(
                                label="FPS Override (0 = auto)",
                                value=0,
                                minimum=0,
                                maximum=60
                            )
                            threads = gr.Slider(
                                label="Processing Threads",
                                minimum=1,
                                maximum=8,
                                value=4,
                                step=1
                            )
                
                # Logs Tab
                with gr.Tab("📋 Logs", elem_classes="tab-content"):
                    log_output = gr.Textbox(
                        label="Live Logs",
                        lines=20,
                        max_lines=30,
                        interactive=False,
                        show_copy_button=True
                    )
                    clear_logs_btn = gr.Button("🗑️ Clear Logs")
                    refresh_logs_btn = gr.Button("🔄 Refresh Logs")
            
            # Event handlers
            def process_video_handler(*args):
                return self._process_video_gradio(*args)
            
            def test_yellow_parsing(text):
                if not text:
                    return {"error": "No text provided"}
                try:
                    parsed = self.yellow_parser.parse_text(text)
                    return {
                        "original": text,
                        "parsed_words": [w.dict() for w in parsed],
                        "markup_patterns": self.yellow_parser.get_supported_patterns()
                    }
                except Exception as e:
                    return {"error": str(e)}
            
            def refresh_fonts():
                self.font_manager.scan_fonts()
                return gr.update(choices=self.font_manager.get_available_fonts())
            
            def get_logs():
                try:
                    with open('app.log', 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        return ''.join(lines[-200:])  # Last 200 lines
                except:
                    return "No logs available"
            
            # Connect event handlers
            process_btn.click(
                fn=process_video_handler,
                inputs=[
                    input_video, input_captions, input_text,
                    font_family, font_size, max_words_per_line,
                    yellow_mode, word_box_enabled, box_opacity,
                    corner_radius, padding_x, padding_y,
                    text_color, stroke_width, stroke_color,
                    position_preset, custom_x, custom_y,
                    video_quality, threads
                ],
                outputs=[
                    preview_output, download_video, download_csv,
                    download_json, summary_output
                ]
            )
            
            test_yellow_btn.click(
                fn=test_yellow_parsing,
                inputs=[yellow_markup_preview],
                outputs=[yellow_test_output]
            )
            
            refresh_fonts_btn.click(
                fn=refresh_fonts,
                outputs=[available_fonts]
            )
            
            refresh_logs_btn.click(
                fn=get_logs,
                outputs=[log_output]
            )
            
            clear_logs_btn.click(
                fn=lambda: "",
                outputs=[log_output]
            )
        
        return interface
    
    def _process_video_gradio(self, *args) -> Tuple:
        """Process video with Gradio inputs"""
        try:
            # Parse arguments
            (input_video, input_captions, input_text,
             font_family, font_size, max_words_per_line,
             yellow_mode, word_box_enabled, box_opacity,
             corner_radius, padding_x, padding_y,
             text_color, stroke_width, stroke_color,
             position_preset, custom_x, custom_y,
             video_quality, threads) = args
            
            if not input_video and not input_text:
                return None, None, None, None, {"error": "Please provide input video or text"}
            
            # Setup processing parameters
            params = {
                'font_family': font_family,
                'font_size': int(font_size),
                'max_words_per_line': int(max_words_per_line),
                'yellow_mode': yellow_mode,
                'word_box_enabled': word_box_enabled,
                'box_opacity': float(box_opacity),
                'corner_radius': int(corner_radius),
                'padding_x': int(padding_x),
                'padding_y': int(padding_y),
                'text_color': text_color,
                'stroke_width': int(stroke_width),
                'stroke_color': stroke_color,
                'position_preset': position_preset,
                'custom_x': float(custom_x) if position_preset == 'custom' else None,
                'custom_y': float(custom_y) if position_preset == 'custom' else None,
                'video_quality': video_quality,
                'threads': int(threads)
            }
            
            # Process the video
            result = self.video_processor.process(
                input_video=input_video,
                input_captions=input_captions,
                input_text=input_text,
                **params
            )
            
            return (
                result.get('output_video'),
                result.get('output_video'),  # Download link
                result.get('csv_file'),
                result.get('json_file'),
                result.get('summary', {})
            )
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return None, None, None, None, {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Arabic Video Subtitle Tool")
    parser.add_argument('--input', help='Input video/image path')
    parser.add_argument('--captions', help='Captions file path')
    parser.add_argument('--text', help='Direct text input')
    parser.add_argument('--font', default='Cairo-Bold', help='Font family')
    parser.add_argument('--font-size', type=int, default=64, help='Font size')
    parser.add_argument('--max-words-per-line', type=int, default=3, help='Max words per line')
    parser.add_argument('--word-box-enabled', type=bool, default=True, help='Enable word boxes')
    parser.add_argument('--box-opacity', type=float, default=0.7, help='Box opacity')
    parser.add_argument('--corner-radius', type=int, default=12, help='Corner radius')
    parser.add_argument('--padding-x', type=int, default=8, help='Horizontal padding')
    parser.add_argument('--padding-y', type=int, default=4, help='Vertical padding')
    parser.add_argument('--anchor', default='bottom-center', help='Text anchor position')
    parser.add_argument('--highlight', default='track_highlight', help='Yellow word mode')
    parser.add_argument('--outdir', default='output', help='Output directory')
    parser.add_argument('--port', type=int, default=7860, help='Server port')
    parser.add_argument('--host', default='127.0.0.1', help='Server host')
    
    args = parser.parse_args()
    
    # Initialize the app
    app = ArabicSubtitleApp()
    
    # CLI mode
    if args.input:
        logger.info("Running in CLI mode")
        # TODO: Implement CLI processing
        print("CLI mode not yet implemented. Use the web interface.")
        return
    
    # Web interface mode
    logger.info(f"Starting web interface on {args.host}:{args.port}")
    interface = app.create_gradio_interface()
    interface.launch(
        server_name=args.host,
        server_port=args.port,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()
