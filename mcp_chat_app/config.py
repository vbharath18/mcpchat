# This file is for storing configurations.

# Default list of MCP (Minecraft Profile) server configurations.
DEFAULT_MCP_SERVERS = [
    {'name': 'Hypixel', 'host': 'mc.hypixel.net', 'port': 25565, 'type': 'Minecraft Java'},
    {'name': 'Example Server 1', 'host': 'play.exampleserver.one', 'port': 25565, 'type': 'Minecraft Java'},
    {'name': 'Local Test Bedrock', 'host': '127.0.0.1', 'port': 19132, 'type': 'Minecraft Bedrock'},
    {'name': 'Another Java Server', 'host': 'javaminecraft.example.org', 'port': 25565, 'type': 'Minecraft Java'}
]

# In-memory store for MCP server configurations.
MCP_SERVERS = []

# OpenAI API Key
# IMPORTANT: Storing API keys directly in config files or committing them to version control
# is NOT SECURE for production environments. This is for local development/testing only.
# Consider using environment variables or a secure vault for production.
OPENAI_API_KEY = None

# Example of other configurations we might add later:
# DEBUG = True
# SECRET_KEY = 'your_secret_key_here'
