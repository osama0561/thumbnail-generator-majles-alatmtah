"""
Generate 4 thumbnails for: بنيت تطبيق بالكامل بالذكاء الأصطناعي !!
Selected concepts: 1, 2, 5, 6
"""

import os
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from pathlib import Path

# API Key
os.environ['GEMINI_API_KEY'] = 'AIzaSyBMLcdHIaB3fJxrHH0sUFx01atm4FXstdc'

client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])

# Output folder
output_dir = Path("E:/YouTube_Workflow_Clean/thumbnail_saas/generated_thumbnails")
output_dir.mkdir(exist_ok=True)

# Selected concepts
concepts = [
    {
        "id": 1,
        "name": "The Chill Builder",
        "arabic_text": "AI بنى لي تطبيق",
        "prompt": """Create a YouTube thumbnail with these EXACT specifications:

**PERSON:**
- Middle Eastern man in his 20s-30s, professional content creator look
- RELAXED pose: leaning back with hands behind head OR arms crossed casually
- CALM/STILL facial expression - not excited, just confident and chill
- Looking at camera

**SCENE COMPOSITION:**
- Person on the LEFT side (40% of frame)
- LAPTOP on the right showing a GREEN APP interface with Arabic letter "أ" logo
- ChatGPT icon (green/white circular logo) floating near top
- VS Code icon (blue icon) floating near the laptop
- Icons should be clean and recognizable

**BACKGROUND:** Dark blue/purple gradient, professional tech vibe

**ARABIC TEXT:** "AI بنى لي تطبيق"
- Large, bold white text
- Position: TOP of thumbnail
- Clean Arabic font, RIGHT-TO-LEFT, perfectly readable

**STYLE:** Realistic photo, NOT cartoon. Clean, modern, tech YouTube thumbnail.
**OUTPUT:** 1920x1080, 16:9 aspect ratio"""
    },
    {
        "id": 2,
        "name": "Tools Working",
        "arabic_text": "خليت AI يشتغل",
        "prompt": """Create a YouTube thumbnail with these EXACT specifications:

**PERSON:**
- Middle Eastern man in his 20s-30s, professional look
- STILL/NEUTRAL facial expression - calm, direct eye contact with camera
- Standing or sitting straight, confident posture

**SCENE COMPOSITION:**
- Person in CENTER
- ChatGPT logo/icon on the LEFT side (large, recognizable)
- VS Code icon on the RIGHT side (large, recognizable)
- LAPTOP at bottom center showing GREEN APP with Arabic "أ" logo
- The tools (ChatGPT, VS Code) appear to be "working" - maybe with subtle glow or connection lines to the laptop

**BACKGROUND:** Dark black or dark gray, minimal

**ARABIC TEXT:** "خليت AI يشتغل"
- Large, bold text (white or light green)
- Position: TOP of thumbnail
- Clean Arabic font, RIGHT-TO-LEFT, perfectly readable

**STYLE:** Realistic photo, professional tech thumbnail
**OUTPUT:** 1920x1080, 16:9 aspect ratio"""
    },
    {
        "id": 5,
        "name": "Done and Relaxed",
        "arabic_text": "خلاص جاهز",
        "prompt": """Create a YouTube thumbnail with these EXACT specifications:

**PERSON:**
- Middle Eastern man in his 20s-30s
- RELAXED pose: leaning back in office chair, satisfied but calm
- Slight subtle smile, peaceful expression - the look of "job done"
- Maybe one hand gesturing toward the laptop

**SCENE COMPOSITION:**
- Person on LEFT side, relaxed in chair
- LAPTOP prominently displayed showing the GREEN APP with Arabic "أ" logo
- The app should be clearly visible as the "finished product"
- Clean desk setup or simple background

**BACKGROUND:** Simple gradient or clean office/desk setting

**ARABIC TEXT:** "خلاص جاهز"
- Large, bold text (white or green)
- Position: TOP RIGHT area
- Clean Arabic font, RIGHT-TO-LEFT, perfectly readable

**STYLE:** Realistic photo, cozy but professional vibe
**OUTPUT:** 1920x1080, 16:9 aspect ratio"""
    },
    {
        "id": 6,
        "name": "My Tools",
        "arabic_text": "بس هذي اللي استخدمت",
        "prompt": """Create a YouTube thumbnail with these EXACT specifications:

**PERSON:**
- Middle Eastern man in his 20s-30s
- STILL/NEUTRAL expression with slight shrug gesture (like "that's all it took")
- Casual, unbothered vibe
- Looking at camera

**SCENE COMPOSITION:**
- Person on one side
- LARGE ChatGPT icon prominently displayed
- LARGE VS Code icon prominently displayed
- LAPTOP showing the GREEN APP with Arabic "أ" logo
- The icons should be BIG and clearly the focus along with the result

**BACKGROUND:** Pure black or very dark, making the icons pop

**ARABIC TEXT:** "بس هذي اللي استخدمت"
- Large, bold white text
- Position: TOP of thumbnail
- Clean Arabic font, RIGHT-TO-LEFT, perfectly readable

**STYLE:** Realistic photo, minimalist design with focus on the tools
**OUTPUT:** 1920x1080, 16:9 aspect ratio"""
    }
]


def generate_thumbnail(concept):
    """Generate a single thumbnail"""
    print(f"\n🎨 Generating: {concept['name']} - {concept['arabic_text']}")

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp-image-generation',
            contents=[concept['prompt']],
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
            )
        )

        if response.candidates and len(response.candidates) > 0:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    inline_data = part.inline_data

                    if hasattr(inline_data, 'data'):
                        img_bytes = inline_data.data
                        pil_image = Image.open(BytesIO(img_bytes))
                    else:
                        gemini_image = inline_data.as_image()
                        img_buffer = BytesIO()
                        gemini_image.save(img_buffer)
                        img_buffer.seek(0)
                        pil_image = Image.open(img_buffer)
                        pil_image.load()

                    # Save
                    filename = f"thumbnail_{concept['id']}_{concept['name'].replace(' ', '_')}.jpg"
                    filepath = output_dir / filename
                    pil_image.save(filepath, "JPEG", quality=95)
                    print(f"✅ Saved: {filepath}")
                    return True

        print(f"❌ No image generated for {concept['name']}")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("🎬 Generating Thumbnails")
    print("Title: بنيت تطبيق بالكامل بالذكاء الأصطناعي !!")
    print("=" * 50)

    import time

    for i, concept in enumerate(concepts):
        generate_thumbnail(concept)
        if i < len(concepts) - 1:
            print("⏳ Waiting 5 seconds...")
            time.sleep(5)

    print("\n" + "=" * 50)
    print(f"✅ Done! Check: {output_dir}")
    print("=" * 50)
