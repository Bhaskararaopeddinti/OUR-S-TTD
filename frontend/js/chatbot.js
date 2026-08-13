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
let isSending = false;

// Toggle panel
chatFab?.addEventListener('click', () => {
  if (chatPanel) {
    chatPanel.hidden = !chatPanel.hidden;
    if (!chatPanel.hidden) chatInput?.focus();
  }
});
chatClose?.addEventListener('click', () => { if (chatPanel) chatPanel.hidden = true; });

// Clear chat
chatClear?.addEventListener('click', () => {
  if (chatMessages) {
    chatMessages.innerHTML = `<div class="msg bot">Namaste! 🙏 How can I help you with your Tirumala pilgrimage?</div>`;
  }
  chatHistory = [];
});

// Load locations for context
async function loadLocations() {
  if (locationsCache) return locationsCache;
  
  try {
    const data = await API.get('locations');
    locationsCache = data.locations || [];
    return locationsCache;
  } catch (error) {
    console.error('Failed to load locations:', error);
    return [];
  }
}

// Helper to determine base URL dynamically
function getChatEndpoint() {
  if (window.location.origin && window.location.origin.startsWith('http')) {
    return window.location.origin + '/api/chat';
  }
  return 'http://127.0.0.1:8001/api/chat';
}

// Send message
async function sendMessage() {
  if (!chatInput || isSending) return;
  const text = chatInput.value.trim();
  if (!text) return;

  isSending = true;
  if (chatSend) chatSend.disabled = true;

  appendMsg(text, 'user');
  chatInput.value = '';
  const thinking = appendMsg('Thinking…', 'bot thinking');

  const lang = document.getElementById('language')?.value || 'English';

  try {
    let data;
    if (typeof API !== 'undefined' && API.post) {
      data = await API.post('chat', {
        message: text,
        language: lang,
        history: chatHistory
      });
    } else {
      const response = await fetch(getChatEndpoint(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          language: lang,
          history: chatHistory
        })
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      data = await response.json();
    }

    thinking.remove();
    
    const reply = data.reply || data.response || data.message || 'I could not generate a reply.';
    appendMsg(reply, 'bot');
    speakReply(reply, lang);

    // Save turn to history
    chatHistory.push({ role: 'user', content: text });
    chatHistory.push({ role: 'assistant', content: reply });
  } catch (err) {
    thinking.remove();
    console.error('Chat error:', err);
    
    // Check if it's an API key configuration issue
    const errorMsg = err?.message || err?.detail || '';
    if (errorMsg.includes('API') || errorMsg.includes('key') || errorMsg.includes('configured')) {
      appendMsg('The AI assistant requires API configuration. Using fallback responses for basic guidance.', 'bot');
    } else {
      appendMsg('The AI assistant is temporarily unavailable. Please try again in a moment.', 'bot');
    }
  } finally {
    isSending = false;
    if (chatSend) chatSend.disabled = false;
    chatInput.focus();
  }
}

chatSend?.addEventListener('click', sendMessage);
chatInput?.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) sendMessage(); });

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
