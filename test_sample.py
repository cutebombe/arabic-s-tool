# test_sample.py
"""
Sample test data and usage examples for the Arabic Subtitle Tool
"""

# Sample Arabic text with yellow word markup
SAMPLE_TEXTS = [
    # News headline format
    "هذا [[y]]الخبر[[/y]] مهم جدًا في [[y]]السوق[[/y]] اليوم",
    
    # Educational content
    "تعلم <y>البرمجة</y> أمر ضروري في <y>العصر</y> الحديث",
    
    # Mixed markup styles
    "السفر إلى {y}دبي{/y} كان [[y]]رائعًا[[/y]] والطقس <y>جميل</y>",
    
    # Long text with multiple yellow words
    """
    في هذا [[y]]اليوم[[/y]] المميز نحتفل بإنجاز <y>عظيم</y> حققه فريق 
    العمل من خلال {y}التعاون{/y} والجهد [[y]]المستمر[[/y]] لتحقيق 
    أهدافنا المشتركة في <y>التطوير</y> والنمو
    """,
]

def test_yellow_parsing():
    """Test yellow word parsing functionality"""
    from yellow import YellowWordParser
    
    parser = YellowWordParser()
    
    print("🧪 Testing Yellow Word Parsing\n")
    
    for i, text in enumerate(SAMPLE_TEXTS, 1):
        print(f"Test {i}: {text[:50]}...")
        
        # Parse yellow words
        yellow_words = parser.parse_text(text)
        clean_text = parser.remove_markup(text)
        
        print(f"  Original: {text}")
        print(f"  Clean: {clean_text}")
        print(f"  Yellow words: {[w.word for w in yellow_words]}")
        print(f"  Count: {len(yellow_words)}")
        print("-" * 50)

def test_font_detection():
    """Test font detection and loading"""
    from fonts import FontManager
    
    print("🔤 Testing Font Detection\n")
    
    fm = FontManager()
    fonts = fm.get_available_fonts()
    
    print(f"Available fonts: {len(fonts)}")
    for font in fonts[:10]:  # Show first 10
        info = fm.get_font_info(font)
        status = "✅" if info['available'] else "❌"
        print(f"  {status} {font} ({info['type']})")
    
    if len(fonts) > 10:
        print(f"  ... and {len(fonts) - 10} more")

def test_text_rendering():
    """Test Arabic text rendering"""
    from fonts import FontManager
    from text_render import TextRenderer
    
    print("🎨 Testing Text Rendering\n")
    
    fm = FontManager()
    renderer = TextRenderer(fm)
    
    test_text = "مرحبا بك في أداة الترجمة العربية"
    
    # Test text reshaping
    shaped = renderer.reshape_arabic_text(test_text)
    print(f"Original: {test_text}")
    print(f"Shaped: {shaped}")
    
    # Test font loading
    available_fonts = fm.get_available_fonts()
    if available_fonts:
        font_name = available_fonts[0]
        font = renderer.get_font(font_name, 48)
        print(f"Loaded font: {font_name}")
        
        # Test text dimensions
        lines, width, height = renderer.calculate_text_dimensions(
            test_text, font, max_words_per_line=3
        )
        print(f"Text lines: {lines}")
        print(f"Dimensions: {width}x{height}")

def create_sample_srt():
    """Create a sample SRT file for testing"""
    srt_content = """1
00:00:00,000 --> 00:00:03,000
هذا [[y]]الخبر[[/y]] مهم جدًا

2
00:00:03,500 --> 00:00:06,500
في [[y]]السوق[[/y]] اليوم

3
00:00:07,000 --> 00:00:10,000
نشاهد تطورات <y>مثيرة</y>

4
00:00:10,500 --> 00:00:13,500
في عالم {y}التكنولوجيا{/y}
"""
    
    with open("sample_subtitles.srt", "w", encoding="utf-8") as f:
        f.write(srt_content)
    
    print("📝 Created sample_subtitles.srt")
    return "sample_subtitles.srt"

def run_full_test():
    """Run comprehensive test suite"""
    print("🚀 Running Full Test Suite\n")
    print("=" * 60)
    
    try:
        test_yellow_parsing()
        print("\n")
        
        test_font_detection()
        print("\n")
        
        test_text_rendering()
        print("\n")
        
        srt_file = create_sample_srt()
        print(f"\nSample files created:")
        print(f"  - {srt_file}")
        
        print("\n✅ All tests completed successfully!")
        print("\nTo test the full application:")
        print("  1. python app.py")
        print("  2. Upload a video or use direct text input")
        print("  3. Try the sample text with yellow words")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_full_test()
