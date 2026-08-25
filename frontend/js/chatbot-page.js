/**
 * chatbot-page.js – AI Assistant page functionality
 * Handles chat interface, quick prompts, and AI integration
 */

// Share chat history with chatbot.js via window namespace to prevent duplicate declaration
if (!window._chatHistoryGlobal) window._chatHistoryGlobal = [];
var chatHistory = window._chatHistoryGlobal;
var isPageSending = false;

// Initialize chatbot page
function initChatbot() {
  // Send button
  document.getElementById('sendBtn')?.addEventListener('click', sendMessage);
  
  // Voice button
  document.getElementById('voiceBtn')?.addEventListener('click', startVoiceInput);
  
  // Enter key to send
  document.getElementById('chatInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });
  
  // Language change
  document.getElementById('chatLanguage')?.addEventListener('change', (e) => {
    showToast(`Language changed to ${e.target.options[e.target.selectedIndex].text}`, 'info');
  });
}

const LANGUAGE_LABELS = {
  en: 'English',
  te: 'Telugu',
  hi: 'Hindi',
  ta: 'Tamil',
  kn: 'Kannada',
  ml: 'Malayalam',
  mr: 'Marathi',
  bn: 'Bengali'
};

// Send message
function sendMessage() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  
  if (!message || isPageSending) return;
  
  // Add user message to chat
  addMessage(message, 'user');
  
  // Clear input
  input.value = '';
  
  // Get AI response
  getAIResponse(message);
}

// Send quick prompt
function sendQuickPrompt(prompt) {
  const input = document.getElementById('chatInput');
  if (input) {
    input.value = prompt;
    sendMessage();
  }
}

function formatChatText(text) {
  if (!text) return '';
  let safe = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  
  safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  const lines = safe.split('\n');
  const formattedLines = lines.map(line => {
    const trimmed = line.trim();
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
      const itemContent = trimmed.substring(2);
      return `<div class="chat-bullet-item" style="display:flex; align-items:flex-start; gap:0.45rem; margin:0.3rem 0;"><span style="color:var(--gold, #F59E0B); font-size:1.1rem; line-height:1.2;">•</span><span>${itemContent}</span></div>`;
    }
    return line ? `<p style="margin:0.25rem 0;">${line}</p>` : '<div style="height:0.35rem;"></div>';
  });

  return formattedLines.join('');
}

// Add message to chat
function addMessage(content, type) {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;
  
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${type}-message`;
  
  const avatar = type === 'user' ? '👤' : '🤖';
  const bodyHtml = type === 'bot' ? formatChatText(content) : `<p>${content}</p>`;
  
  messageDiv.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-content">
      ${bodyHtml}
    </div>
  `;
  
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function getApiEndpoint() {
  if (typeof window !== 'undefined' && window.location) {
    const { hostname, port, protocol } = window.location;
    if (hostname === 'localhost' || hostname === '127.0.0.1' || protocol === 'file:') {
      if (port === '8000') {
        return '/api/ai/chat';
      }
      return 'http://127.0.0.1:8000/api/ai/chat';
    }
    return '/api/ai/chat';
  }
  return '/api/ai/chat';
}

// Get AI response
async function getAIResponse(message) {
  const chatMessages = document.getElementById('chatMessages');
  const sendBtn = document.getElementById('sendBtn');
  
  isPageSending = true;
  if (sendBtn) sendBtn.disabled = true;

  // Add typing indicator
  const typingDiv = document.createElement('div');
  typingDiv.className = 'message bot-message typing';
  typingDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">
      <p>Thinking...</p>
    </div>
  `;
  chatMessages?.appendChild(typingDiv);
  if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
  
  const apiUrl = getApiEndpoint();
  console.log("AI question:", message);
  console.log("AI API URL:", apiUrl);

  try {
    const languageCode = document.getElementById('chatLanguage')?.value || 'en';
    const language = LANGUAGE_LABELS[languageCode] || 'English';

    const payload = {
      message: message,
      language: language,
      history: chatHistory
    };

    let data;
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    console.log("AI response status:", response.status);

    if (!response.ok) {
      const errText = await response.text();
      console.error("AI HTTP Error:", response.status, errText);
      throw new Error(`HTTP ${response.status}: ${errText}`);
    }

    data = await response.json();
    console.log("AI response:", data);
    
    // Remove typing indicator
    typingDiv.remove();
    
    const reply = data.answer || data.reply || data.response || data.message || "• AI service is temporarily unavailable.\n• Please try again shortly.";
    addMessage(reply, 'bot');

    // Save turn to history
    chatHistory.push({ role: 'user', content: message });
    chatHistory.push({ role: 'assistant', content: reply });
    
  } catch (error) {
    typingDiv.remove();
    console.error('AI chat error:', error);
    addMessage("• AI service is temporarily unavailable.\n• Please try again shortly.", 'bot');
  } finally {
    isPageSending = false;
    if (sendBtn) sendBtn.disabled = false;
    const chatInput = document.getElementById('chatInput');
    if (chatInput) chatInput.focus();
  }
}

window.sendMessage = sendMessage;
window.sendQuickPrompt = sendQuickPrompt;
window.clearChat = clearChat;
window.initChatbot = initChatbot;

// Start voice input
function startVoiceInput() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    if (typeof showToast === 'function') showToast('Voice input not supported in this browser', 'error');
    return;
  }
  
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  
  recognition.lang = 'en-US';
  recognition.continuous = false;
  recognition.interimResults = false;
  
  recognition.onstart = () => {
    if (typeof showToast === 'function') showToast('Listening...', 'info');
  };
  
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    const input = document.getElementById('chatInput');
    if (input) input.value = transcript;
    if (typeof showToast === 'function') showToast('Voice captured!', 'success');
  };
  
  recognition.onerror = (event) => {
    if (typeof showToast === 'function') showToast('Voice input error: ' + event.error, 'error');
  };
  
  recognition.onend = () => {
    if (document.getElementById('chatInput')?.value) {
      sendMessage();
    }
  };
  
  recognition.start();
}

// Clear chat
function clearChat() {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;
  
  chatMessages.innerHTML = `
    <div class="message bot-message">
      <div class="message-avatar">🤖</div>
      <div class="message-content">
        <p>Chat cleared. How can I help you today?</p>
      </div>
    </div>
  `;
  
  chatHistory = [];
  if (typeof showToast === 'function') showToast('Chat cleared', 'info');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  if (document.querySelector('.chatbot-page')) {
    initChatbot();
  }
});
