/**
 * chatbot-page.js – AI Assistant page functionality
 * Handles chat interface, quick prompts, and AI integration
 */
'use strict';

let chatHistory = [];
let isPageSending = false;

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

// Add message to chat
function addMessage(content, type) {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;
  
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${type}-message`;
  
  const avatar = type === 'user' ? '👤' : '🤖';
  
  messageDiv.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-content">
      <p>${content}</p>
    </div>
  `;
  
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Helper to determine base URL dynamically
function getApiEndpoint() {
  if (window.location.origin && window.location.origin.startsWith('http')) {
    return window.location.origin + '/api/chat';
  }
  return 'http://127.0.0.1:8001/api/chat';
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
  
  try {
    const languageCode = document.getElementById('chatLanguage')?.value || 'en';
    const language = LANGUAGE_LABELS[languageCode] || 'English';

    let data;
    if (typeof API !== 'undefined' && API.post) {
      data = await API.post('chat', {
        message: message,
        language: language,
        history: chatHistory
      });
    } else {
      const response = await fetch(getApiEndpoint(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          language: language,
          history: chatHistory
        })
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      data = await response.json();
    }
    
    // Remove typing indicator
    typingDiv.remove();
    
    const reply = data.reply || data.response || data.message || 'I apologize, but I could not process your request.';
    addMessage(reply, 'bot');

    // Save turn to history
    chatHistory.push({ role: 'user', content: message });
    chatHistory.push({ role: 'assistant', content: reply });
    
  } catch (error) {
    typingDiv.remove();
    addMessage('The AI assistant is temporarily unavailable. Please try again in a moment.', 'bot');
    console.error('AI chat error:', error);
  } finally {
    isPageSending = false;
    if (sendBtn) sendBtn.disabled = false;
  }
}

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
