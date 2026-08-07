/**
 * chatbot-page.js – AI Assistant page functionality
 * Handles chat interface, quick prompts, and AI integration
 */
'use strict';

let chatHistory = [];

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

// Send message
function sendMessage() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  
  if (!message) return;
  
  // Add user message to chat
  addMessage(message, 'user');
  
  // Clear input
  input.value = '';
  
  // Get AI response
  getAIResponse(message);
}

// Send quick prompt
function sendQuickPrompt(prompt) {
  document.getElementById('chatInput').value = prompt;
  sendMessage();
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
  
  // Add to history
  chatHistory.push({ type, content, timestamp: new Date().toISOString() });
}

// Get AI response
async function getAIResponse(message) {
  const chatMessages = document.getElementById('chatMessages');
  
  // Add typing indicator
  const typingDiv = document.createElement('div');
  typingDiv.className = 'message bot-message typing';
  typingDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">
      <p>Thinking...</p>
    </div>
  `;
  chatMessages.appendChild(typingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  try {
    // Call AI API
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message, history: chatHistory })
    });
    
    const data = await response.json();
    
    // Remove typing indicator
    typingDiv.remove();
    
    // Add AI response
    addMessage(data.response || data.message || 'I apologize, but I could not process your request.', 'bot');
    
  } catch (error) {
    // Remove typing indicator
    typingDiv.remove();
    
    // Add error message
    addMessage('I apologize, but I am having trouble connecting. Please try again later.', 'bot');
    
    console.error('AI chat error:', error);
  }
}

// Start voice input
function startVoiceInput() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    showToast('Voice input not supported in this browser', 'error');
    return;
  }
  
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  
  recognition.lang = 'en-US';
  recognition.continuous = false;
  recognition.interimResults = false;
  
  recognition.onstart = () => {
    showToast('Listening...', 'info');
  };
  
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById('chatInput').value = transcript;
    showToast('Voice captured!', 'success');
  };
  
  recognition.onerror = (event) => {
    showToast('Voice input error: ' + event.error, 'error');
  };
  
  recognition.onend = () => {
    // Automatically send if we got a result
    if (document.getElementById('chatInput').value) {
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
  showToast('Chat cleared', 'info');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  if (document.querySelector('.chatbot-page')) {
    initChatbot();
  }
});
