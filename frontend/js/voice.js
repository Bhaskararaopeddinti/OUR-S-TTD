/**
 * voice.js – Standalone voice input for hero section button (if present).
 */
'use strict';

const voiceStartBtn = document.getElementById('voiceStart');
if (voiceStartBtn) {
  voiceStartBtn.addEventListener('click', () => {
    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Speech) {
      document.getElementById('chatFab')?.click();
      document.getElementById('chatInput')?.focus();
      return;
    }
    const rec = new Speech();
    rec.lang = 'en-IN';
    rec.onresult = e => {
      document.getElementById('chatFab')?.click();
      const input = document.getElementById('chatInput');
      if (input) {
        input.value = e.results[0][0].transcript;
        document.getElementById('chatSend')?.click();
      }
    };
    rec.start();
  });
}
