import { GoogleGenAI } from '@google/genai';
import { createClient } from '@supabase/supabase-js';

export const maxDuration = 120;

// Models to try in order
const IMAGE_MODELS = [
  'gemini-2.0-flash-preview-image-generation',
  'imagen-3.0-generate-002',
];

export async function POST(request) {
  try {
    const { concept, apiKey, supabaseUrl, supabaseKey, projectId } = await request.json();

    if (!concept) {
      return Response.json({ error: 'Concept is required' }, { status: 400 });
    }

    const geminiKey = apiKey || process.env.GEMINI_API_KEY;
    if (!geminiKey) {
      return Response.json({ error: 'Gemini API key is required' }, { status: 400 });
    }

    const ai = new GoogleGenAI({ apiKey: geminiKey });

    // Build the prompt
    const prompt = `Create a YouTube thumbnail image.

The person: A professional-looking Middle Eastern man in his 20s-30s
Expression: ${concept.expression}
Pose: ${concept.pose || 'simple pose'}

Scene: ${concept.scene}
Background: ${concept.background}
Emotion to convey: ${concept.emotion}

Include Arabic text: "${concept.arabic_text}"
Position text: ${concept.text_position}
Style: ${concept.text_style}

Make it look like a real YouTube thumbnail, 16:9 aspect ratio, professional quality.`;

    let imageData = null;
    let usedModel = null;
    let debugInfo = [];

    // Try each model
    for (const modelName of IMAGE_MODELS) {
      debugInfo.push(`Trying model: ${modelName}`);

      try {
        const response = await ai.models.generateContent({
          model: modelName,
          contents: [{ role: 'user', parts: [{ text: prompt }] }],
          config: {
            responseModalities: ['Text', 'Image'],
          },
        });

        debugInfo.push(`Response received from ${modelName}`);

        // Check for image in response
        if (response.candidates && response.candidates.length > 0) {
          const candidate = response.candidates[0];
          debugInfo.push(`Found ${candidate.content?.parts?.length || 0} parts`);

          for (const part of candidate.content?.parts || []) {
            if (part.inlineData) {
              debugInfo.push(`Found inlineData with mimeType: ${part.inlineData.mimeType}`);
              imageData = part.inlineData.data;
              usedModel = modelName;
              break;
            }
          }

          if (imageData) break;
        }

        debugInfo.push(`No image found in response from ${modelName}`);

      } catch (modelError) {
        debugInfo.push(`${modelName} error: ${modelError.message}`);
        continue;
      }
    }

    if (!imageData) {
      return Response.json({
        error: 'Failed to generate image with all models',
        debug: debugInfo
      }, { status: 500 });
    }

    // Upload to Supabase if configured
    let imageUrl = null;
    const sbUrl = supabaseUrl || process.env.SUPABASE_URL;
    const sbKey = supabaseKey || process.env.SUPABASE_KEY;

    if (sbUrl && sbKey) {
      try {
        const supabase = createClient(sbUrl, sbKey);

        const timestamp = Date.now();
        const filename = `${projectId || 'default'}/${concept.id}_${timestamp}.jpg`;

        // Convert base64 to buffer
        const buffer = Buffer.from(imageData, 'base64');

        const { data, error } = await supabase.storage
          .from('thumbnails')
          .upload(filename, buffer, {
            contentType: 'image/jpeg',
            upsert: true
          });

        if (!error) {
          const { data: urlData } = supabase.storage
            .from('thumbnails')
            .getPublicUrl(filename);

          imageUrl = urlData.publicUrl;
          debugInfo.push(`Uploaded to Supabase: ${imageUrl}`);
        } else {
          debugInfo.push(`Supabase upload error: ${error.message}`);
        }
      } catch (uploadError) {
        debugInfo.push(`Upload error: ${uploadError.message}`);
      }
    }

    return Response.json({
      success: true,
      imageData: `data:image/jpeg;base64,${imageData}`,
      imageUrl,
      model: usedModel,
      concept: concept,
      debug: debugInfo
    });

  } catch (error) {
    console.error('Generate thumbnail error:', error);
    return Response.json({
      error: error.message || 'Failed to generate thumbnail',
      stack: error.stack
    }, { status: 500 });
  }
}
