# MCP Chat Application with LLM Integration

## Description

This project is a web-based chat application designed to interact with Minecraft Profile (MCP) servers and leverage OpenAI's Language Models (LLMs) for context-aware conversations. It features a chat interface, an admin panel for managing MCP server configurations and OpenAI API Key, and fetches live data from Minecraft servers.

## Features

-   **Chat Interface:** A user-friendly page for chatting with an AI assistant.
-   **Admin Panel:** Allows:
    -   Adding, editing, and deleting Minecraft Profile Server configurations.
    -   Configuration for your OpenAI API Key.
-   **Default Server List:** A predefined list of sample Minecraft Profile servers is loaded on the first run if no configurations exist.
-   **Live Minecraft Server Data:** Fetches live status (MOTD, player count/max, version, latency) from selected Minecraft Profile Servers using the `mcstatus` library.
-   **LLM Integration:** Interacts with OpenAI's GPT model (e.g., gpt-3.5-turbo) for generating chat responses.
-   **Context-Aware Chat:** The LLM uses live data fetched from a user-selected Minecraft Profile Server to provide more informed and relevant responses. If a server is offline or data fetching fails, the LLM is made aware of this.
-   **Unit Tests:** Comprehensive unit tests for backend logic, including mocked tests for server interactions and LLM integration.

## Project Structure

```
.
├── mcp_chat_app/
│   ├── app.py            # Main Flask application (routes, backend logic, LLM integration)
│   ├── mcp_client.py     # Functional client using `mcstatus` to query Minecraft server status.
│   ├── config.py         # Application configuration (MCP_SERVERS list, OpenAI API Key).
│   ├── __init__.py       # Makes mcp_chat_app a Python package.
│   ├── templates/
│   │   ├── index.html    # Chat interface HTML (with server selection).
│   │   └── admin.html    # Admin configuration page HTML (servers & API Key).
│   │   └── edit_server.html # HTML template for editing server details.
│   ├── static/
│   │   ├── style.css     # CSS styles for the application.
│   │   └── script.js     # JavaScript for chat interface interactivity and LLM communication.
│   └── test_app.py       # Unit tests for the Flask application.
├── requirements.txt      # Lists Python package dependencies (Flask, mcstatus, openai).
└── README.md             # This file.
```

## Setup and Running Instructions

### Prerequisites

-   Python 3.7+
-   Pip (Python package installer)

### Installation

1.  **Clone the repository** (or download and extract the files):
    ```bash
    # Example if it were a git repo:
    # git clone <repository_url>
    # cd <repository_directory>
    ```
    For now, ensure you have all the files in the structure described above.

2.  **Navigate to the project's root directory** (the directory containing `mcp_chat_app/` and `README.md`).

3.  **Install Dependencies:**
    Open your terminal or command prompt and run:
    ```bash
    pip install -r requirements.txt
    ```
    This will install Flask, mcstatus, and openai libraries.

### Configuration

**OpenAI API Key:**
To use the LLM chat features, you must configure your OpenAI API Key:
1.  Run the application (see next step).
2.  Open your browser and navigate to the admin page: `http://127.0.0.1:5000/admin`.
3.  Find the "OpenAI Configuration" section.
4.  Enter your valid OpenAI API key and click "Save API Key".
5.  **Security Note:** This application stores the API key in memory for the current session. This method is **not secure for production environments** and is intended for local development and testing only. In production, use environment variables or a secure vault service.

### Running the Application

1.  Ensure you are in the project's root directory.
2.  Execute the main application file:
    ```bash
    python mcp_chat_app/app.py
    ```
    You should see output indicating the Flask development server is running, typically on `http://127.0.0.1:5000/`.

3.  **Access the application in your browser:**
    -   **Chat Interface:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
    -   **Admin Panel:** [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)

## Using the Chat Interface

-   **General Chat:**
    -   Ensure your OpenAI API Key is configured (see Configuration section).
    -   If the "Context" dropdown is set to "Chat with LLM (General)", you can type messages and the LLM will respond without specific Minecraft server context.

-   **Chatting with Server Context:**
    1.  Ensure your OpenAI API Key is configured in the `/admin` panel.
    2.  From the "Context" dropdown menu above the message input field on the chat page, select one of the configured Minecraft Profile Servers.
    3.  Type your message and press Send or Enter.
    4.  The application will attempt to fetch live data (status, MOTD, player count, etc.) from the selected server.
    5.  This server data will be provided as context to the LLM for a more informed and relevant response.
    6.  If the selected server is offline or data fetching fails, the LLM will be informed of this situation and can respond accordingly.

## Running Tests

To run the unit tests for the Flask application:

1.  **Navigate to the project's root directory.**
2.  Execute the following command in your terminal:
    ```bash
    python -m unittest mcp_chat_app.test_app
    ```
    The tests will run, and you'll see output indicating the number of tests run and whether they passed or failed. All tests should pass if the application is set up correctly.
