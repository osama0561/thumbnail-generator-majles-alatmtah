"""
Thumbnail Generator - Flask API for Vercel
"""

from flask import Flask, request, jsonify, render_template, send_file
import os
import json
import base64
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types

app = Flask(__name__, template_folder='../templates', static_folder='../statics')

# =============================================================================
# CORE THUMBNAIL GENERATION LOGIC
# =============================================================================

CONCEPT_GENERATION_PROMPT = """You are a YouTube thumbnail expert specializing in EMOTIONAL thumbnails that make people CLICK.

Generate 10 thumbnail concepts for this video title: "{title}"

## YOUR APPROACH:
1. First, identify the CORE PROBLEM/PAIN the viewer has about this topic
2. Define the EMOTIONS that problem creates (fear, frustration, shame, anxiety, confusion, regret, etc.)
3. Create thumbnails that make people FEEL something - they click on feelings, not logic
4. Focus on NEGATIVE emotions - pain sells

## STRICT RULES:
1. **EVERYDAY LANGUAGE** - Use words people actually SAY, not formal/poetic Arabic
2. **SIMPLE SCENES** - Face + simple background + text ONLY
3. **NO COMPLEX METAPHORS** - No trains, doors, waves, chains, mazes, drowning
4. **REAL SETTINGS** - Desk, plain wall, color gradient, home office
5. **EXPRESSION IS KEY** - The facial expression carries 80% of the emotion
6. **CURRENT REFERENCES** - No outdated years or trends

## WHAT MAKES A GOOD CONCEPT:
- The viewer should see THEMSELVES in the thumbnail
- Text should be the viewer's INNER VOICE (what they're literally thinking)
- Emotion should be OBVIOUS and slightly EXAGGERATED
- Could be photographed in real life (not surreal)

Return ONLY a valid JSON array with 10 objects:
[
  {{
    "id": 1,
    "name_ar": "اسم المفهوم",
    "name_en": "Concept Name",
    "emotion": "core emotion in English",
    "viewer_pain": "what pain/problem does the viewer feel about this topic",
    "expression": "detailed facial expression description",
    "pose": "body pose/position (simple)",
    "scene": "simple scene description - face + background only",
    "background": "plain background description (gradient, solid color, simple desk)",
    "arabic_text": "النص العربي للثمبنيل",
    "text_position": "where text goes",
    "text_style": "text appearance",
    "why_it_works": "why this will make someone click"
  }}
]

Return ONLY the JSON array, no other text or markdown."""


def get_gemini_client(api_key):
    """Initialize Gemini client"""
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def generate_concepts(title: str, api_key: str) -> list:
    """Generate 10 emotional thumbnail concepts for a video title"""
    client = get_gemini_client(api_key)
    if not client:
        return []

    prompt = CONCEPT_GENERATION_PROMPT.format(title=title)

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[prompt]
        )

        text = response.text.strip()

        # Remove markdown code blocks if present
        if '```' in text:
            parts = text.split('```')
            for part in parts:
                if part.strip().startswith('json'):
                    text = part.strip()[4:].strip()
                    break
                elif part.strip().startswith('['):
                    text = part.strip()
                    break

        text = text.strip()
        if not text.startswith('['):
            start = text.find('[')
            end = text.rfind(']') + 1
            if start != -1 and end > start:
                text = text[start:end]

        concepts = json.loads(text)
        return concepts

    except Exception as e:
        print(f"Error generating concepts: {e}")
        return []


def generate_thumbnail(concept: dict, reference_images: list, api_key: str):
    """Generate a single thumbnail based on concept"""
    client = get_gemini_client(api_key)
    if not client:
        return None

    if reference_images:
        person_instruction = """**THE PERSON (from reference photos):**
- Must look EXACTLY like the person in the reference photos provided
- Use their face, features, and appearance
- Expression: {expression}
- Pose: {pose}"""
    else:
        person_instruction = """**THE PERSON:**
- Create a professional-looking Middle Eastern man in his 20s-30s
- Clean appearance, could be a YouTuber/content creator
- Expression: {expression}
- Pose: {pose}"""

    prompt = f"""Create a SIMPLE, AUTHENTIC YouTube thumbnail. Must look like a REAL photo, not AI-generated.

**CONCEPT:** {concept['name_ar']} ({concept['name_en']})
**EMOTION TO CONVEY:** {concept['emotion']}
**WHY IT WORKS:** {concept.get('why_it_works', 'Triggers emotional response')}

{person_instruction.format(expression=concept['expression'], pose=concept.get('pose', 'simple pose'))}

**SCENE:** {concept['scene']}

**BACKGROUND:** {concept['background']}
- Keep it SIMPLE - plain colors, gradients, or simple real settings
- NO complex scenes, NO floating objects, NO surreal elements

**ARABIC TEXT:** "{concept['arabic_text']}"
- Position: {concept['text_position']}
- Style: {concept['text_style']}
- MUST be readable, proper Arabic (RTL), correctly connected letters
- Make it LARGE and impactful

**CRITICAL REQUIREMENTS:**
1. Should look like a REAL photograph, not AI art
2. Simple background (solid color, gradient, or plain wall)
3. FACIAL EXPRESSION is the main focus
4. Clean, minimal design
5. Arabic text must be PERFECTLY readable

**OUTPUT:** 1920x1080 (16:9), professional YouTube thumbnail quality"""

    try:
        contents = [prompt]
        if reference_images:
            for img_data in reference_images:
                img_bytes = base64.b64decode(img_data)
                img = Image.open(BytesIO(img_bytes))
                contents.append(img)

        response = client.models.generate_content(
            model='gemini-3-pro-image-preview',
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio='16:9',
                    image_size='2K'
                ),
            )
        )

        if response.candidates and len(response.candidates) > 0:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    inline_data = part.inline_data
                    if hasattr(inline_data, 'data'):
                        img_bytes = inline_data.data
                        buffered = BytesIO()
                        pil_image = Image.open(BytesIO(img_bytes))
                        pil_image.save(buffered, format="JPEG", quality=90)
                        return base64.b64encode(buffered.getvalue()).decode()
                    else:
                        gemini_image = inline_data.as_image()
                        img_buffer = BytesIO()
                        gemini_image.save(img_buffer)
                        img_buffer.seek(0)
                        pil_image = Image.open(img_buffer)
                        buffered = BytesIO()
                        pil_image.save(buffered, format="JPEG", quality=90)
                        return base64.b64encode(buffered.getvalue()).decode()

        return None

    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return None


# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/generate-concepts', methods=['POST'])
def api_generate_concepts():
    data = request.json
    title = data.get('title', '')
    api_key = data.get('api_key', '')

    if not title or not api_key:
        return jsonify({'error': 'العنوان و API Key مطلوبين'}), 400

    concepts = generate_concepts(title, api_key)
    if concepts:
        return jsonify({'concepts': concepts})
    else:
        return jsonify({'error': 'فشل في توليد الأفكار'}), 500


@app.route('/api/generate-thumbnail', methods=['POST'])
def api_generate_thumbnail():
    data = request.json
    concept = data.get('concept', {})
    api_key = data.get('api_key', '')
    reference_images = data.get('reference_images', [])

    if not concept or not api_key:
        return jsonify({'error': 'البيانات ناقصة'}), 400

    thumbnail_b64 = generate_thumbnail(concept, reference_images, api_key)
    if thumbnail_b64:
        return jsonify({'thumbnail': thumbnail_b64})
    else:
        return jsonify({'error': 'فشل في توليد الثمبنيل'}), 500


# For local development
if __name__ == '__main__':
    app.run(debug=True, port=5000)
