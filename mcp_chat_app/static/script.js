// This file will contain JavaScript for chat interface interactivity.

console.log("MCP Chat script (v2.1 - UI Refinements) loaded.");

// Get DOM elements
const chatBox = document.getElementById('chat-box');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const serverSelect = document.getElementById('mcp-server-select'); // Server select dropdown

// To keep track of the "Thinking..." message element
let thinkingMessageElement = null;

function displayMessage(sender, message, messageType = 'normal') {
    /**
     * Displays a message in the chat box.
     * @param {string} sender - The user sending the message (e.g., "You", "LLM", "System").
     * @param {string} message - The message content.
     * @param {string} messageType - Used as a CSS class for styling (e.g., 'user', 'llm', 'error', 'info', 'system').
     */
    const messageElement = document.createElement('p');
    messageElement.classList.add('chat-message', `${messageType}-message`);

    const senderSpan = document.createElement('span');
    senderSpan.classList.add('sender');
    senderSpan.textContent = `${sender}:`;
    messageElement.appendChild(senderSpan);

    // Basic Markdown-like formatting for bold and italic
    message = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); // Bold
    message = message.replace(/\*(.*?)\*/g, '<em>$1</em>');       // Italic

    const contentSpan = document.createElement('span');
    contentSpan.classList.add('content');
    contentSpan.innerHTML = message; // Use innerHTML to render basic formatting
    messageElement.appendChild(contentSpan);

    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight; // Scroll to the bottom
    return messageElement; // Return the created element
}

function showThinkingIndicator() {
    if (thinkingMessageElement) { // Remove previous if any (should not happen often)
        chatBox.removeChild(thinkingMessageElement);
    }
    thinkingMessageElement = displayMessage("LLM Assistant", "Thinking...", "info");
}

function removeThinkingIndicator() {
    if (thinkingMessageElement && thinkingMessageElement.parentNode === chatBox) {
        chatBox.removeChild(thinkingMessageElement);
    }
    thinkingMessageElement = null;
}

async function sendMessage() {
    /**
     * Gets the message from input, selected server, displays user message,
     * shows thinking indicator, sends to backend, and displays LLM response or error.
     */
    const messageText = messageInput.value.trim();
    const selectedServerId = serverSelect ? serverSelect.value : "";

    if (messageText) {
        displayMessage("You", messageText, "user"); // Use 'user' type
        messageInput.value = '';
        showThinkingIndicator();

        try {
            const response = await fetch('/chat_with_llm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: messageText,
                    server_id: selectedServerId
                })
            });

            removeThinkingIndicator();

            if (response.ok) {
                const result = await response.json();
                if (result.reply) {
                    displayMessage("LLM Assistant", result.reply, "llm"); // Use 'llm' type
                } else if (result.error) { // Errors from the backend (e.g. API key missing)
                    displayMessage("System", `Error: ${result.error}`, "error");
                }
                if (result.server_data_used) {
                    console.log("Server data used by LLM:", result.server_data_used);
                    // displayMessage("System", `(Debug: Server context used: ${JSON.stringify(result.server_data_used, null, 2)})`, "info");
                }
            } else { // HTTP errors (e.g. 500, 400 from backend itself)
                let errorMsg = `Failed to get response from server (HTTP ${response.status})`;
                try {
                    const errorResult = await response.json();
                    if (errorResult && errorResult.error) {
                        errorMsg = errorResult.error;
                    }
                } catch (e) {
                    // Could not parse JSON error, use default HTTP error.
                    console.warn("Could not parse JSON error response from server:", e);
                }
                displayMessage("System", `Error: ${errorMsg}`, "error");
            }
        } catch (error) { // Network errors or other JS errors during fetch
            removeThinkingIndicator();
            console.error('Network error or other issue sending message:', error);
            displayMessage("System", `Network Error: Could not connect. ${error.message}`, "error");
        }
    }
}

// Event Listeners
if (sendButton) {
    sendButton.addEventListener('click', sendMessage);
}

if (messageInput) {
    messageInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
}

// Initial welcome message in index.html is good.
// Client-side API key check is optional, the backend handles it.
console.log("Event listeners attached. Ready for LLM chat with UI refinements.");
