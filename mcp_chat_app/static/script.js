// This file will contain JavaScript for chat interface interactivity.

console.log("MCP Chat script loaded.");

// Get DOM elements
const chatBox = document.getElementById('chat-box');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

function displayMessage(user, message) {
    /**
     * Displays a message in the chat box.
     * @param {string} user - The user sending the message.
     * @param {string} message - The message content.
     */
    const messageElement = document.createElement('p');
    // Sanitize user and message if necessary, though for "You" it's controlled.
    // For messages from server, ensure proper escaping/sanitization on server-side or client-side.
    messageElement.textContent = `${user}: ${message}`;
    chatBox.appendChild(messageElement);
    // Scroll to the bottom of the chat box
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    /**
     * Gets the message from the input field, displays it locally,
     * sends it to the server, and clears the input.
     */
    const messageText = messageInput.value.trim();

    if (messageText) {
        // Display the user's own message immediately
        displayMessage("You", messageText);

        // Clear the input field
        messageInput.value = '';

        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: messageText })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Message sent successfully:', result);
                // Optionally, display a server confirmation or echo if needed
                // For example, if the server pre-pends "[Broadcast]" or similar
                // displayMessage("Server", result.message_echo); // Example
            } else {
                const errorResult = await response.json();
                console.error('Error sending message:', response.status, errorResult);
                displayMessage("System", `Error: Could not send message. ${errorResult.message || 'Server error'}`);
            }
        } catch (error) {
            console.error('Network error or other issue sending message:', error);
            displayMessage("System", "Error: Could not connect to the server to send message.");
        }
    }
}

// Event Listeners
if (sendButton) {
    sendButton.addEventListener('click', sendMessage);
}

if (messageInput) {
    messageInput.addEventListener('keypress', function(event) {
        // Check if the pressed key is Enter
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
}

// Example initial message
// displayMessage("System", "Welcome to MCP Chat! Type your message and press Send or Enter.");
// This can be part of the initial HTML or loaded from server if needed.
// For now, let's assume the chat starts empty or with server-loaded messages.
console.log("Event listeners attached. Ready for chat.");
