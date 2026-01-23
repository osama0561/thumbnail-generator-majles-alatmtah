"""
Thumbnail Generator SaaS - MVP
Simple Streamlit app for generating emotional YouTube thumbnails

Process:
1. User enters video title
2. AI generates 10 emotional thumbnail concepts
3. User selects which ones to generate
4. (Optional) User uploads reference photos for their face
5. Generate thumbnails
6. Download
"""

import streamlit as st
import os
import time
import json
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types
import base64
from io import BytesIO

# Page config
st.set_page_config(
    page_title="مولد الثمبنيل",
    page_icon="🎨",
    layout="wide"
)

# Custom CSS with RTL support
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
        direction: rtl;
    }
    .sub-header {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
        direction: rtl;
    }
    .concept-box {
        background-color: #1a1a2e;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-right: 4px solid #ff4b4b;
        direction: rtl;
    }
    .emotion-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 15px;
        font-size: 0.75rem;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    .arabic-text {
        font-size: 1.2rem;
        color: #ffd700;
        direction: rtl;
        text-align: right;
    }
    .step-header {
        background: linear-gradient(90deg, #ff4b4b, #ff6b6b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    .rtl-text {
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

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


def get_gemini_client():
    """Initialize Gemini client"""
    api_key = os.getenv('GEMINI_API_KEY') or st.session_state.get('gemini_api_key')
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def generate_concepts(title: str, client) -> list:
    """Generate 10 emotional thumbnail concepts for a video title"""

    prompt = CONCEPT_GENERATION_PROMPT.format(title=title)

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[prompt]
        )

        # Parse JSON from response
        text = response.text.strip()

        # Remove markdown code blocks if present
        if '```' in text:
            # Find content between code blocks
            parts = text.split('```')
            for part in parts:
                if part.strip().startswith('json'):
                    text = part.strip()[4:].strip()
                    break
                elif part.strip().startswith('['):
                    text = part.strip()
                    break

        # Clean up
        text = text.strip()
        if not text.startswith('['):
            # Try to find the array
            start = text.find('[')
            end = text.rfind(']') + 1
            if start != -1 and end > start:
                text = text[start:end]

        concepts = json.loads(text)
        return concepts

    except json.JSONDecodeError as e:
        st.error(f"خطأ في تحليل الأفكار: {e}")
        st.code(text[:500] if 'text' in dir() else "No response")
        return []
    except Exception as e:
        st.error(f"خطأ في توليد الأفكار: {e}")
        return []


def generate_thumbnail(concept: dict, reference_images: list, client) -> Image.Image:
    """Generate a single thumbnail based on concept"""

    # Different prompt based on whether we have reference images
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
- This should look like it could be a real photograph

**ARABIC TEXT:** "{concept['arabic_text']}"
- Position: {concept['text_position']}
- Style: {concept['text_style']}
- MUST be readable, proper Arabic (RTL), correctly connected letters
- Make it LARGE and impactful
- Use bold, clean font

**CRITICAL REQUIREMENTS:**
1. Should look like a REAL photograph, not AI art
2. Simple background (solid color, gradient, or plain wall)
3. FACIAL EXPRESSION is the main focus - it carries the emotion
4. Clean, minimal design - no clutter
5. The emotion ({concept['emotion']}) must be INSTANTLY obvious
6. Arabic text must be PERFECTLY readable

**OUTPUT:** 1920x1080 (16:9), professional YouTube thumbnail quality"""

    try:
        # Build contents list
        contents = [prompt]
        if reference_images:
            contents.extend(reference_images)

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
                    # Get raw bytes from inline_data
                    inline_data = part.inline_data

                    # Access the raw image bytes
                    if hasattr(inline_data, 'data'):
                        # Raw bytes available
                        img_bytes = inline_data.data
                        pil_image = Image.open(BytesIO(img_bytes))
                        return pil_image
                    else:
                        # Try as_image() and save to buffer without format arg
                        gemini_image = inline_data.as_image()
                        img_buffer = BytesIO()
                        gemini_image.save(img_buffer)
                        img_buffer.seek(0)
                        pil_image = Image.open(img_buffer)
                        pil_image.load()
                        return pil_image

        return None

    except Exception as e:
        st.error(f"خطأ في توليد الثمبنيل: {e}")
        return None


def image_to_base64(img: Image.Image) -> str:
    """Convert PIL Image to base64 string for download"""
    buffered = BytesIO()
    img.save(buffered, format="JPEG", quality=90)
    return base64.b64encode(buffered.getvalue()).decode()


# =============================================================================
# STREAMLIT UI
# =============================================================================

def main():
    # Header
    st.markdown('<p class="main-header">🎨 مولد الثمبنيل</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">صمم ثمبنيلات YouTube تخلي الناس تضغط</p>', unsafe_allow_html=True)

    # ==========================================================================
    # HOW TO USE - 3 Simple Steps
    # ==========================================================================
    with st.container(border=True):
        st.markdown("### 📖 كيف تستخدم الأداة")

        col1, col2, col3 = st.columns(3)

        with col3:  # RTL - start from right
            st.markdown("""
            <div class="rtl-text">
            <b>الخطوة ١: أدخل العنوان</b>

            اكتب عنوان فيديو YouTube بالعربي. الـ AI بيحلل العنوان ويفهم مشاعر المشاهدين.
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="rtl-text">
            <b>الخطوة ٢: اختر الأفكار</b>

            بتحصل على ١٠ أفكار للثمبنيل. كل فكرة تبين النص والتعبير والإحساس. اختر اللي تعجبك.
            </div>
            """, unsafe_allow_html=True)

        with col1:
            st.markdown("""
            <div class="rtl-text">
            <b>الخطوة ٣: ولّد وحمّل</b>

            اضغط توليد وانتظر. حمّل الثمبنيلات واستخدمها. اختياري: ارفع صورتك عشان وجهك يظهر.
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")  # Spacer

    # Sidebar
    with st.sidebar:
        st.header("⚙️ الإعدادات")
        st.caption("ضبط الـ API Key وصور المرجع")

        # API Key
        api_key = st.text_input(
            "🔑 Gemini API Key",
            type="password",
            value=os.getenv('GEMINI_API_KEY', ''),
            help="مطلوب لتوليد الثمبنيلات. احصل على key مجاني من Google AI Studio"
        )
        if api_key:
            st.session_state['gemini_api_key'] = api_key
            os.environ['GEMINI_API_KEY'] = api_key
            st.success("✅ تم حفظ الـ API Key")
        else:
            st.warning("⚠️ أدخل الـ API Key للبدء")

        st.divider()

        # Reference images (OPTIONAL)
        st.header("📷 صورتك (اختياري)")
        st.caption("تبي وجهك يظهر بالثمبنيل؟ ارفع ٢-٣ صور. غير كذا الـ AI بيولد شخص عشوائي.")

        uploaded_files = st.file_uploader(
            "📤 ارفع صور مرجعية",
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            key="reference_images",
            help="اختياري: ارفع ٢-٣ صور واضحة لوجهك من زوايا مختلفة"
        )

        # Store in session state for access outside sidebar
        st.session_state['uploaded_files'] = uploaded_files

        if uploaded_files:
            st.success(f"✅ تم رفع {len(uploaded_files)} صور")
            cols = st.columns(min(len(uploaded_files), 3))
            for i, file in enumerate(uploaded_files[:3]):
                with cols[i]:
                    img = Image.open(file)
                    st.image(img, width=80)
        else:
            st.info("ℹ️ ما فيه صور - بيستخدم شخص AI")

        st.divider()

        # Process explanation
        st.header("📋 كيف تشتغل")
        st.markdown("""
        ١. **أدخل عنوان الفيديو**
        ٢. **احصل على ١٠ أفكار** - بناءً على مشاعر المشاهد
        ٣. **اختر اللي تبيها**
        ٤. **ولّد الثمبنيلات**
        ٥. **حمّل واستخدم!**

        *الثمبنيلات تركز على المشاعر - الناس تضغط على الإحساس مو المعلومة.*
        """)

    # Initialize session state
    if 'concepts' not in st.session_state:
        st.session_state.concepts = []
    if 'generated_thumbnails' not in st.session_state:
        st.session_state.generated_thumbnails = {}
    if 'current_title' not in st.session_state:
        st.session_state.current_title = ""
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

    # ==========================================================================
    # STEP 1: Enter Title
    # ==========================================================================
    st.markdown("### 📝 الخطوة ١: أدخل عنوان الفيديو")
    st.caption("اكتب عنوان فيديو YouTube. الـ AI بيحلله ويلاقي المشاعر اللي يحس فيها المشاهد.")

    col1, col2 = st.columns([3, 1])

    with col1:
        title = st.text_input(
            "عنوان الفيديو",
            placeholder="مثال: هل تأخرت على تعلم الذكاء الأصطناعي؟",
            label_visibility="collapsed",
            help="اكتب عنوان الفيديو بالعربي أو الإنجليزي"
        )

    with col2:
        generate_ideas_btn = st.button(
            "🧠 ولّد أفكار",
            type="primary",
            use_container_width=True,
            disabled=not title,
            help="اضغط لتوليد ١٠ أفكار ثمبنيل بناءً على العنوان"
        )

    if not title:
        st.info("👆 أدخل عنوان الفيديو فوق للبدء")

    # Generate concepts
    if generate_ideas_btn and title:
        client = get_gemini_client()
        if not client:
            st.error("⚠️ أدخل الـ Gemini API Key في الشريط الجانبي")
        else:
            with st.spinner("🧠 يحلل المشاعر ويولد ١٠ أفكار..."):
                concepts = generate_concepts(title, client)
                if concepts:
                    st.session_state.concepts = concepts
                    st.session_state.generated_thumbnails = {}
                    st.session_state.current_title = title
                    st.success(f"✅ تم توليد {len(concepts)} فكرة!")
                    st.rerun()

    # ==========================================================================
    # STEP 2: Display & Select Concepts
    # ==========================================================================
    if st.session_state.concepts:
        st.divider()
        st.markdown("### 🎯 الخطوة ٢: اختر الثمبنيلات للتوليد")
        st.caption(f"العنوان: **{st.session_state.current_title}**")
        st.info("✅ **اختر المربعات** جنب الأفكار اللي تبي تولدها. كل فكرة تبين الإحساس والنص والمشهد.")

        selected_ids = []

        # Display concepts in 2 columns
        cols = st.columns(2)

        for i, concept in enumerate(st.session_state.concepts):
            with cols[i % 2]:
                with st.container(border=True):
                    # Checkbox with concept name
                    checked = st.checkbox(
                        f"**{concept['id']}. {concept['name_ar']}**",
                        key=f"select_{concept['id']}"
                    )

                    if checked:
                        selected_ids.append(concept['id'])

                    # Emotion badge
                    st.markdown(f"<span class='emotion-badge'>😢 {concept['emotion']}</span>", unsafe_allow_html=True)

                    # Arabic text preview
                    st.markdown(f"<p class='arabic-text'>« {concept['arabic_text']} »</p>", unsafe_allow_html=True)

                    # Details in expander
                    with st.expander("📋 شوف التفاصيل"):
                        st.markdown(f"**😶 التعبير:** {concept['expression']}")
                        st.markdown(f"**🖼️ المشهد:** {concept['scene']}")
                        st.markdown(f"**🎨 الخلفية:** {concept['background']}")
                        if 'viewer_pain' in concept:
                            st.markdown(f"**😰 ألم المشاهد:** {concept['viewer_pain']}")
                        if 'why_it_works' in concept:
                            st.markdown(f"**✅ ليش تشتغل:** {concept['why_it_works']}")

        # ==========================================================================
        # STEP 3: Generate Selected
        # ==========================================================================
        if selected_ids:
            st.divider()
            st.markdown("### 🎨 الخطوة ٣: ولّد الثمبنيلات")
            st.caption("هذا بيولد ثمبنيلات حقيقية باستخدام AI. يأخذ تقريباً ٣٠-٦٠ ثانية لكل ثمبنيل.")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # Get uploaded files from session state
                user_photos = st.session_state.get('uploaded_files', [])

                # Show what will be generated
                ref_status = "بوجهك" if user_photos else "بشخص AI"
                st.info(f"جاهز لتوليد **{len(selected_ids)} ثمبنيل** {ref_status}")

                generate_btn = st.button(
                    f"🎨 ولّد {len(selected_ids)} ثمبنيل",
                    type="primary",
                    use_container_width=True,
                    help="اضغط لبدء توليد الثمبنيلات المختارة باستخدام AI"
                )

            if generate_btn:
                client = get_gemini_client()
                if not client:
                    st.error("⚠️ أدخل الـ Gemini API Key في الشريط الجانبي")
                else:
                    # Load reference images if provided
                    ref_images = []
                    user_photos = st.session_state.get('uploaded_files', [])
                    if user_photos:
                        for file in user_photos[:3]:
                            file.seek(0)
                            img = Image.open(file)
                            ref_images.append(img)

                    # Get selected concepts
                    selected_concepts = [c for c in st.session_state.concepts if c['id'] in selected_ids]

                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for i, concept in enumerate(selected_concepts):
                        status_text.markdown(f"**يولد:** {concept['name_ar']} ({concept['emotion']})")

                        thumbnail = generate_thumbnail(concept, ref_images, client)

                        if thumbnail:
                            st.session_state.generated_thumbnails[concept['id']] = {
                                'image': thumbnail,
                                'concept': concept
                            }

                        progress_bar.progress((i + 1) / len(selected_concepts))

                        # Delay between generations to avoid rate limits
                        if i < len(selected_concepts) - 1:
                            time.sleep(3)

                    status_text.markdown("**✅ اكتمل التوليد!**")
                    st.balloons()

    # ==========================================================================
    # STEP 4: Display Generated Thumbnails
    # ==========================================================================
    if st.session_state.generated_thumbnails:
        st.divider()
        st.markdown("### 🖼️ الخطوة ٤: حمّل الثمبنيلات")
        st.caption("اضغط زر التحميل لحفظ كل ثمبنيل على جهازك. استخدم الأفضل لفيديو YouTube!")
        st.success(f"🎉 **{len(st.session_state.generated_thumbnails)} ثمبنيل جاهز!** اضغط تحميل لحفظها.")

        cols = st.columns(2)

        for i, (concept_id, data) in enumerate(st.session_state.generated_thumbnails.items()):
            with cols[i % 2]:
                concept = data['concept']
                img = data['image']

                # Title
                st.markdown(f"**{concept['name_ar']}**")
                st.caption(f"{concept['emotion']} • {concept['arabic_text']}")

                # Image
                st.image(img, use_container_width=True)

                # Download button
                img_b64 = image_to_base64(img)
                filename = f"thumbnail_{concept_id}_{concept['name_en'].replace(' ', '_')}.jpg"

                st.download_button(
                    label="📥 حمّل هذا الثمبنيل",
                    data=base64.b64decode(img_b64),
                    file_name=filename,
                    mime="image/jpeg",
                    use_container_width=True,
                    help="حفظ الثمبنيل كملف JPG على جهازك"
                )

                st.markdown("---")


if __name__ == "__main__":
    main()
