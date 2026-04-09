// Simple Mistral Chat Application
// This is a basic implementation that demonstrates how to interact with Mistral API

// DOM elements
const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');

// Configuration - REPLACE WITH YOUR ACTUAL API KEY
const API_KEY = 'YOUR_MISTRAL_API_KEY'; // Replace this with your actual API key
const API_URL = 'https://api.mistral.ai/v1/chat/completions';

// Add message to chat container
function addMessage(text, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
    messageDiv.textContent = text;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Show typing indicator
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot';
    typingDiv.id = 'typing-indicator';

    const dots = document.createElement('div');
    dots.style.display = 'flex';
    dots.style.alignItems = 'center';

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'typing-indicator';
        dots.appendChild(dot);
    }

    typingDiv.appendChild(dots);
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Call Mistral API
async function callMistralAPI(userMessage) {
    try {
        showTypingIndicator();

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`
            },
            body: JSON.stringify({
                model: 'mistral-tiny', // You can change this to other models
                messages: [
                    {
                        role: 'user',
                        content: userMessage
                    }
                ],
                temperature: 0.7,
                max_tokens: 500
            })
        });

        if (!response.ok) {
            throw new Error(`API request failed with status ${response.status}`);
        }

        const data = await response.json();
        removeTypingIndicator();

        if (data.choices && data.choices.length > 0) {
            return data.choices[0].message.content;
        } else {
            throw new Error('No response from API');
        }
    } catch (error) {
        removeTypingIndicator();
        console.error('Error calling Mistral API:', error);
        return `Error: ${error.message}. Please check your API key and try again.`;
    }
}

// Handle user input
async function handleUserInput() {
    const message = userInput.value.trim();

    if (message) {
        addMessage(message, true);
        userInput.value = '';

        const botResponse = await callMistralAPI(message);
        addMessage(botResponse, false);
    }
}

// Event listeners
sendButton.addEventListener('click', handleUserInput);

userInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        handleUserInput();
    }
});

// Initial message
addMessage('Hello! I am your Mistral AI assistant. How can I help you today?', false);
