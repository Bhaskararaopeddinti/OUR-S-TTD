/**
 * language.js – Language selector with AI-powered translation via backend.
 * Falls back gracefully if the translation service is unavailable.
 */
'use strict';

const langSelect = document.getElementById('language');
const LANG_CODES = {
  'English': 'en', 'Telugu': 'te', 'Hindi': 'hi',
  'Tamil': 'ta', 'Kannada': 'kn', 'Malayalam': 'ml',
  'Marathi': 'mr', 'Bengali': 'bn',
};

// Restore saved language
const savedLang = localStorage.getItem('lang') || 'English';
if (langSelect) {
  langSelect.value = savedLang;
  document.documentElement.lang = LANG_CODES[savedLang] || 'en';
}

langSelect?.addEventListener('change', async () => {
  const lang = langSelect.value;
  localStorage.setItem('lang', lang);
  document.documentElement.lang = LANG_CODES[lang] || 'en';

  if (lang === 'English') {
    // Restore original text for all data-translate elements
    document.querySelectorAll('[data-translate]').forEach(el => {
      if (el.dataset.original) el.textContent = el.dataset.original;
    });
    return;
  }

  // Collect all translateable elements
  const els = Array.from(document.querySelectorAll('[data-translate]'));
  const texts = els.map(el => {
    if (!el.dataset.original) el.dataset.original = el.textContent;
    return el.dataset.original;
  });

  // Batch translate via backend (which uses Google Translate or Gemini)
  try {
    const joined = texts.join('\n||||\n');
    const res = await API.post('translate', { text: joined, target_language: lang });
    const parts = res.translated.split('\n||||\n');
    els.forEach((el, i) => {
      if (parts[i]) el.textContent = parts[i].trim();
    });
  } catch (e) {
    console.warn('Translation unavailable:', e);
  }
});
