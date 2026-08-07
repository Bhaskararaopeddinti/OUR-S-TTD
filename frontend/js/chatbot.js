/**
 * chatbot.js – AI Chatbot with Gemini backend, voice output, history, and location awareness.
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

let chatHistory = [];
let locationsCache = null;

// Toggle panel
chatFab.addEventListener('click', () => {
  chatPanel.hidden = !chatPanel.hidden;
  if (!chatPanel.hidden) chatInput.focus();
});
chatClose.addEventListener('click', () => { chatPanel.hidden = true; });

// Clear chat
chatClear?.addEventListener('click', () => {
  chatMessages.innerHTML = `<div class="msg bot">Namaste! 🙏 How can I help you with your Tirumala pilgrimage?</div>`;
  chatHistory = [];
});

// Load locations for context
async function loadLocations() {
  if (locationsCache) return locationsCache;
  
  try {
    const response = await fetch('/api/locations');
    const data = await response.json();
    locationsCache = data.locations || [];
    return locationsCache;
  } catch (error) {
    console.error('Failed to load locations:', error);
    return [];
  }
}

// Send message
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;
  appendMsg(text, 'user');
  chatInput.value = '';
  const thinking = appendMsg('Thinking…', 'bot thinking');

  const lang = document.getElementById('language')?.value || 'English';
  
  // Load locations for context
  const locations = await loadLocations();
  
  // Add location context to message
  const locationContext = locations.length > 0 
    ? `\n\nAvailable locations: ${locations.map(l => l.name + ' (' + l.category + ')').join(', ')}`
    : '';

  chatHistory.push({ role: 'user', content: text });

  API.post('chat', {
    message: text,
    language: lang,
  })
    .then(data => {
      thinking.remove();
      const reply = data.reply || data.message || 'I could not generate a reply.';
      appendMsg(reply, 'bot');
      speakReply(reply, lang);
      chatHistory.push({ role: 'assistant', content: reply });
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
