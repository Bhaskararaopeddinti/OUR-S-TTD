/**
 * chatbot.js – AI Chatbot with Gemini backend, voice output, history.
 * Requires: api.js loaded first.
 */
'use strict';

const chatFab      = document.getElementById('chatFab');
const chatPanel    = document.getElementById('chatPanel');
const chatClose    = document.getElementById('chatClose');
const chatMessages = document.getElementById('chatMessages');
const chatInput    = document.getElementById('chatInput');
const chatSend     = document.getElementById('chatSend');
const chatClear    = document.getElementById('chatClearBtn');
const voiceBtn     = document.getElementById('voiceInputBtn');

// Toggle panel
chatFab.addEventListener('click', () => {
  chatPanel.hidden = !chatPanel.hidden;
  if (!chatPanel.hidden) chatInput.focus();
});
chatClose.addEventListener('click', () => { chatPanel.hidden = true; });

// Clear chat
chatClear?.addEventListener('click', () => {
  chatMessages.innerHTML = `<div class="msg bot">Namaste! 🙏 How can I help you with your Tirumala pilgrimage?</div>`;
});

// Send message
function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;
  appendMsg(text, 'user');
  chatInput.value = '';
  const thinking = appendMsg('Thinking…', 'bot thinking');

  const lang = document.getElementById('language')?.value || 'English';

  API.post('chat', { message: text, language: lang })
    .then(data => {
      thinking.remove();
      const reply = appendMsg(data.reply || 'I could not generate a reply.', 'bot');
      speakReply(data.reply, lang);
    })
    .catch(err => {
      thinking.remove();
      appendMsg('I am reconnecting. Please try again in a moment.', 'bot');
    });
}

chatSend.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) sendMessage(); });

function appendMsg(text, className) {
  const div = document.createElement('div');
  div.className = `msg ${className}`;
  div.textContent = text;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div;
}

// Voice output (text-to-speech)
function speakReply(text, lang) {
  if (!('speechSynthesis' in window) || !text) return;
  const langCode = {
    'Telugu': 'te-IN', 'Hindi': 'hi-IN', 'Tamil': 'ta-IN',
    'Kannada': 'kn-IN', 'Malayalam': 'ml-IN', 'Marathi': 'mr-IN',
    'Bengali': 'bn-IN', 'English': 'en-IN',
  }[lang] || 'en-IN';
  const utt = new SpeechSynthesisUtterance(text.slice(0, 300));
  utt.lang = langCode;
  utt.rate = 0.92;
  speechSynthesis.cancel();
  speechSynthesis.speak(utt);
}

// Voice input
voiceBtn?.addEventListener('click', () => {
  const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Speech) { chatInput.focus(); return; }
  const rec = new Speech();
  const lang = document.getElementById('language')?.value || 'English';
  const langCode = {
    'Telugu': 'te-IN', 'Hindi': 'hi-IN', 'Tamil': 'ta-IN',
    'Kannada': 'kn-IN', 'Malayalam': 'ml-IN', 'Marathi': 'mr-IN',
    'Bengali': 'bn-BD', 'English': 'en-IN',
  }[lang] || 'en-IN';
  rec.lang = langCode;
  rec.onstart = () => { voiceBtn.textContent = '🔴 Listening…'; };
  rec.onresult = e => {
    chatInput.value = e.results[0][0].transcript;
    voiceBtn.textContent = '🎙 Voice';
    sendMessage();
  };
  rec.onerror = () => { voiceBtn.textContent = '🎙 Voice'; };
  rec.onend   = () => { voiceBtn.textContent = '🎙 Voice'; };
  rec.start();
});
