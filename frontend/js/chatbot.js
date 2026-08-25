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

// Use shared window state to prevent duplicate declaration SyntaxError
// (chatbot.js and chatbot-page.js are both loaded on the page)
if (!window._chatHistoryGlobal) window._chatHistoryGlobal = [];
var chatHistory = window._chatHistoryGlobal;

var locationsCache = null;
var isSending = false;

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

function getChatEndpoint() {
  if (typeof API !== 'undefined' && API.post) {
    return '/api/chat';
  }
  if (window.location.origin && window.location.origin.startsWith('http') && !['5500', '5501'].includes(window.location.port)) {
    return window.location.origin + '/api/chat';
  }
  return 'http://localhost:8000/api/chat';
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
    
    const reply = data.reply || data.response || data.message || "Sorry, I couldn't process that request. Please try again.";
    appendMsg(reply, 'bot');
    speakReply(reply, lang);

    // Save turn to history
    chatHistory.push({ role: 'user', content: text });
    chatHistory.push({ role: 'assistant', content: reply });
  } catch (err) {
    thinking.remove();
    console.error('Chat error:', err);
    appendMsg("Sorry, I couldn't process that request. Please try again.", 'bot');
  } finally {
    isSending = false;
    if (chatSend) chatSend.disabled = false;
    chatInput.focus();
  }
}

chatSend?.addEventListener('click', sendMessage);
chatInput?.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) sendMessage(); });

function formatChatText(text) {
  if (!text) return '';
  // Convert escaped tags to safe text first
  let safe = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  
  // Format bold **text**
  safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Format list items starting with * or -
  const lines = safe.split('\n');
  const formattedLines = lines.map(line => {
    const trimmed = line.trim();
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
      const itemContent = trimmed.substring(2);
      return `<div class="chat-bullet-item" style="display:flex; align-items:flex-start; gap:0.4rem; margin:0.25rem 0;"><span style="color:var(--gold, #F59E0B); font-size:1.1rem; line-height:1.2;">•</span><span>${itemContent}</span></div>`;
    }
    return line ? `<p style="margin:0.2rem 0;">${line}</p>` : '<div style="height:0.3rem;"></div>';
  });

  return formattedLines.join('');
}

function appendMsg(text, className) {
  const div = document.createElement('div');
  div.className = `msg ${className}`;
  if (className.includes('thinking')) {
    div.textContent = text;
  } else if (className.includes('bot')) {
    div.innerHTML = formatChatText(text);
  } else {
    div.textContent = text;
  }
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
