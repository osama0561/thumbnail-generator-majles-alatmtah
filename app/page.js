'use client';

import { useState } from 'react';

export default function Home() {
  // Settings
  const [geminiKey, setGeminiKey] = useState('');
  const [supabaseUrl, setSupabaseUrl] = useState('https://wkzlezxxtbqfodyustav.supabase.co');
  const [supabaseKey, setSupabaseKey] = useState('');

  // State
  const [title, setTitle] = useState('');
  const [concepts, setConcepts] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [thumbnails, setThumbnails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [debug, setDebug] = useState('');
  const [projectId] = useState(() => crypto.randomUUID());

  // Generate ideas
  const generateIdeas = async () => {
    if (!title.trim()) {
      setStatus('error:أدخل عنوان الفيديو');
      return;
    }

    setLoading(true);
    setStatus('loading:يحلل المشاعر ويولد ١٠ أفكار...');
    setConcepts([]);
    setSelectedIds([]);
    setThumbnails([]);

    try {
      const res = await fetch('/api/generate-ideas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, apiKey: geminiKey }),
      });

      const data = await res.json();

      if (data.error) {
        setStatus(`error:${data.error}`);
        setDebug(JSON.stringify(data, null, 2));
      } else {
        setConcepts(data.concepts);
        setStatus(`success:تم توليد ${data.count} فكرة!`);
      }
    } catch (error) {
      setStatus(`error:${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Toggle concept selection
  const toggleConcept = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  // Generate thumbnails
  const generateThumbnails = async () => {
    if (selectedIds.length === 0) {
      setStatus('error:اختر فكرة واحدة على الأقل');
      return;
    }

    setLoading(true);
    setThumbnails([]);
    setDebug('');

    const selectedConcepts = concepts.filter(c => selectedIds.includes(c.id));
    let debugLog = [];

    for (let i = 0; i < selectedConcepts.length; i++) {
      const concept = selectedConcepts[i];
      setStatus(`loading:يولد ${i + 1}/${selectedConcepts.length}: ${concept.name_ar}`);

      try {
        const res = await fetch('/api/generate-thumbnail', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            concept,
            apiKey: geminiKey,
            supabaseUrl,
            supabaseKey,
            projectId,
          }),
        });

        const data = await res.json();

        if (data.debug) {
          debugLog = [...debugLog, `--- ${concept.name_en} ---`, ...data.debug];
        }

        if (data.error) {
          debugLog.push(`ERROR: ${data.error}`);
        } else if (data.imageData) {
          setThumbnails(prev => [...prev, {
            concept,
            imageData: data.imageData,
            imageUrl: data.imageUrl,
            model: data.model,
          }]);
        }

        setDebug(debugLog.join('\n'));

      } catch (error) {
        debugLog.push(`FETCH ERROR: ${error.message}`);
        setDebug(debugLog.join('\n'));
      }

      // Small delay between requests
      if (i < selectedConcepts.length - 1) {
        await new Promise(r => setTimeout(r, 2000));
      }
    }

    setLoading(false);
    setStatus(thumbnails.length > 0 ? `success:تم توليد ${thumbnails.length} ثمبنيل!` : 'error:فشل توليد الثمبنيلات');
  };

  // Download thumbnail
  const downloadThumbnail = (imageData, filename) => {
    const link = document.createElement('a');
    link.href = imageData;
    link.download = filename;
    link.click();
  };

  // Parse status
  const statusType = status.split(':')[0];
  const statusMsg = status.split(':').slice(1).join(':');

  return (
    <div className="container">
      <div className="header">
        <h1>🎨 مولد الثمبنيل</h1>
        <p>صمم ثمبنيلات YouTube تخلي الناس تضغط</p>
      </div>

      {/* Settings */}
      <div className="card">
        <h2>⚙️ الإعدادات</h2>
        <div className="settings-panel">
          <div className="input-group">
            <label>🔑 Gemini API Key</label>
            <input
              type="password"
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              placeholder="AIzaSy..."
            />
          </div>
          <div className="input-group">
            <label>🔑 Supabase Key (اختياري)</label>
            <input
              type="password"
              value={supabaseKey}
              onChange={(e) => setSupabaseKey(e.target.value)}
              placeholder="للحفظ الدائم"
            />
          </div>
        </div>
      </div>

      {/* Step 1: Title */}
      <div className="card">
        <h2>📝 الخطوة ١: أدخل عنوان الفيديو</h2>
        <div className="input-group">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="مثال: هل تأخرت على تعلم الذكاء الاصطناعي؟"
            disabled={loading}
          />
        </div>
        <button
          className="btn btn-primary"
          onClick={generateIdeas}
          disabled={loading || !title.trim()}
        >
          🧠 ولّد أفكار
        </button>
      </div>

      {/* Status */}
      {status && (
        <div className={`status ${statusType}`}>
          {statusType === 'loading' && '⏳ '}
          {statusType === 'success' && '✅ '}
          {statusType === 'error' && '❌ '}
          {statusMsg}
        </div>
      )}

      {/* Step 2: Concepts */}
      {concepts.length > 0 && (
        <div className="card">
          <h2>🎯 الخطوة ٢: اختر الأفكار ({selectedIds.length} مختارة)</h2>
          <div className="concepts-grid">
            {concepts.map((concept) => (
              <div
                key={concept.id}
                className={`concept-card ${selectedIds.includes(concept.id) ? 'selected' : ''}`}
                onClick={() => toggleConcept(concept.id)}
              >
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(concept.id)}
                    onChange={() => toggleConcept(concept.id)}
                  />
                  <h3>{concept.id}. {concept.name_ar}</h3>
                </label>
                <span className="emotion">{concept.emotion}</span>
                <p className="arabic-text">« {concept.arabic_text} »</p>
                <small>{concept.scene}</small>
              </div>
            ))}
          </div>

          {selectedIds.length > 0 && (
            <button
              className="btn btn-primary"
              onClick={generateThumbnails}
              disabled={loading}
              style={{ marginTop: '1rem' }}
            >
              🎨 ولّد {selectedIds.length} ثمبنيل
            </button>
          )}
        </div>
      )}

      {/* Step 3: Generated Thumbnails */}
      {thumbnails.length > 0 && (
        <div className="card">
          <h2>🖼️ الخطوة ٣: الثمبنيلات الجاهزة</h2>
          <div className="thumbnails-grid">
            {thumbnails.map((item, idx) => (
              <div key={idx} className="thumbnail-card">
                <img src={item.imageData} alt={item.concept.name_ar} />
                <div className="info">
                  <h4>{item.concept.name_ar}</h4>
                  <p>{item.concept.emotion} • {item.concept.arabic_text}</p>
                  <small>Model: {item.model}</small>
                  {item.imageUrl && <small> • Saved to Supabase</small>}
                  <div className="actions">
                    <button
                      className="btn btn-primary"
                      onClick={() => downloadThumbnail(
                        item.imageData,
                        `thumbnail_${item.concept.id}_${item.concept.name_en.replace(/\s+/g, '_')}.jpg`
                      )}
                    >
                      📥 حمّل
                    </button>
                    {item.imageUrl && (
                      <a href={item.imageUrl} target="_blank" rel="noopener" className="btn btn-secondary">
                        🔗 فتح الرابط
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Debug */}
      {debug && (
        <div className="card">
          <h2>🔍 Debug Log</h2>
          <div className="debug">{debug}</div>
        </div>
      )}
    </div>
  );
}
