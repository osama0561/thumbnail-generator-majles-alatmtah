import { GoogleGenAI } from '@google/genai';

export const maxDuration = 60;

const CONCEPT_PROMPT = `You are a YouTube thumbnail expert specializing in EMOTIONAL thumbnails that make people CLICK.

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

Return ONLY a valid JSON array with 10 objects:
[
  {
    "id": 1,
    "name_ar": "اسم المفهوم",
    "name_en": "Concept Name",
    "emotion": "core emotion in English",
    "expression": "detailed facial expression description",
    "pose": "body pose/position (simple)",
    "scene": "simple scene description",
    "background": "plain background description",
    "arabic_text": "النص العربي للثمبنيل",
    "text_position": "where text goes",
    "text_style": "text appearance",
    "why_it_works": "why this will make someone click"
  }
]

Return ONLY the JSON array, no markdown or extra text.`;

export async function POST(request) {
  try {
    const { title, apiKey } = await request.json();

    if (!title) {
      return Response.json({ error: 'Title is required' }, { status: 400 });
    }

    const geminiKey = apiKey || process.env.GEMINI_API_KEY;
    if (!geminiKey) {
      return Response.json({ error: 'Gemini API key is required' }, { status: 400 });
    }

    const ai = new GoogleGenAI({ apiKey: geminiKey });

    const prompt = CONCEPT_PROMPT.replace('{title}', title);

    const response = await ai.models.generateContent({
      model: 'gemini-2.0-flash',
      contents: [{ role: 'user', parts: [{ text: prompt }] }],
    });

    let text = response.text || '';

    // Clean up markdown if present
    if (text.includes('```')) {
      const match = text.match(/```(?:json)?\s*([\s\S]*?)```/);
      if (match) {
        text = match[1].trim();
      }
    }

    // Find the JSON array
    const start = text.indexOf('[');
    const end = text.lastIndexOf(']') + 1;
    if (start !== -1 && end > start) {
      text = text.substring(start, end);
    }

    const concepts = JSON.parse(text);

    return Response.json({
      success: true,
      concepts,
      count: concepts.length
    });

  } catch (error) {
    console.error('Generate ideas error:', error);
    return Response.json({
      error: error.message || 'Failed to generate ideas'
    }, { status: 500 });
  }
}
