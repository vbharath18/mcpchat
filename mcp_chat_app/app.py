# This is the main Flask application file.

import copy
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from openai import OpenAI # Import OpenAI

# Import configurations. We will be modifying MCP_SERVERS and OPENAI_API_KEY.
from . import config # Use relative import for config within the package
from .mcp_client import MCPClient # Import MCPClient

# Create a Flask application instance
app = Flask(__name__)

# Secret key for session management (required for flash messages)
# IMPORTANT: Change this to a random, secure key in a real application!
app.secret_key = 'dev_secret_key_123!'


# --- Application Initialization ---
def initialize_app_config():
    """Initializes application configuration, like loading default servers."""
    if hasattr(config, 'DEFAULT_MCP_SERVERS') and not config.MCP_SERVERS:
        print("MCP_SERVERS is empty, loading defaults.")
        config.MCP_SERVERS.extend(copy.deepcopy(config.DEFAULT_MCP_SERVERS))
    else:
        print(f"MCP_SERVERS already populated or no defaults found. Count: {len(config.MCP_SERVERS)}")

initialize_app_config()


# --- Routes ---
@app.route('/')
def index():
    """Serves the main chat interface page. Passes server list for dropdown."""
    return render_template('index.html', servers=config.MCP_SERVERS)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """
    Serves the admin page for managing MCP server configurations and OpenAI API Key.
    """
    error_message = request.args.get('error') # Get error from redirect if any

    # For displaying API key status
    openai_api_key_set = bool(config.OPENAI_API_KEY)
    openai_api_key_display = config.OPENAI_API_KEY[:4] if config.OPENAI_API_KEY else ""


    if request.method == 'POST': # This handles "Add Server" form
        server_name = request.form.get('server-name')
        server_host = request.form.get('server-host')
        server_port_str = request.form.get('server-port')
        server_type = request.form.get('server-type', 'Unknown')

        if server_name and server_host and server_port_str:
            try:
                port = int(server_port_str)
                if port <= 0 or port > 65535:
                    raise ValueError("Port out of range")
                new_server = {"name": server_name, "host": server_host, "port": port, "type": server_type}
                config.MCP_SERVERS.append(new_server)
                flash(f"Server '{server_name}' added successfully!", "success")
                return redirect(url_for('admin'))
            except ValueError:
                error_message = f"Invalid port number: '{server_port_str}'. Port must be between 1 and 65535."
        else:
            error_message = "All fields (Server Name, Host, Port) for adding a server are required."

    return render_template('admin.html',
                           servers=config.MCP_SERVERS,
                           error=error_message,
                           openai_api_key_set=openai_api_key_set,
                           openai_api_key_display=openai_api_key_display)


@app.route('/admin/save_api_key', methods=['POST'])
def save_api_key():
    """Saves the OpenAI API Key."""
    if request.method == 'POST':
        api_key = request.form.get('openai-api-key')
        if api_key:
            config.OPENAI_API_KEY = api_key
            flash("OpenAI API Key saved successfully.", "success")
            print(f"OpenAI API Key updated. Current key (partial): {config.OPENAI_API_KEY[:4]}...")
        else:
            # config.OPENAI_API_KEY = None # Or keep the old one if field is empty
            flash("API Key field was empty. No changes made or key cleared if that's intended.", "warning")
    return redirect(url_for('admin'))


@app.route('/admin/delete_server/<int:server_id>', methods=['POST'])
def delete_server(server_id):
    """Handles deletion of an MCP server."""
    try:
        if 0 <= server_id < len(config.MCP_SERVERS):
            deleted_server = config.MCP_SERVERS.pop(server_id)
            flash(f"Server '{deleted_server.get('name')}' deleted successfully.", "success")
        else:
            flash("Error: Attempted to delete server with invalid ID.", "error")
    except IndexError:
        flash("Error: Server ID out of range during delete.", "error")
    return redirect(url_for('admin'))


@app.route('/admin/edit_server/<int:server_id>', methods=['GET', 'POST'])
def edit_server(server_id):
    """Handles editing of an MCP server."""
    error_message = None
    server_to_edit = None

    try:
        if not (0 <= server_id < len(config.MCP_SERVERS)):
            flash("Error: Server ID for edit is invalid or out of range.", "error")
            return redirect(url_for('admin'))
        server_to_edit = config.MCP_SERVERS[server_id]
    except IndexError: # Should be caught by the check above
        flash("Critical Error: Server ID out of range during edit access.", "error")
        return redirect(url_for('admin'))

    if request.method == 'POST':
        new_server_name = request.form.get('server-name')
        new_server_host = request.form.get('server-host')
        new_server_port_str = request.form.get('server-port')
        new_server_type = request.form.get('server-type', server_to_edit.get('type', 'Unknown'))

        if new_server_name and new_server_host and new_server_port_str:
            try:
                new_port = int(new_server_port_str)
                if not (0 < new_port <= 65535): raise ValueError("Port out of range")

                config.MCP_SERVERS[server_id] = {
                    "name": new_server_name, "host": new_server_host,
                    "port": new_port, "type": new_server_type
                }
                flash(f"Server '{new_server_name}' updated successfully.", "success")
                return redirect(url_for('admin'))
            except ValueError:
                error_message = f"Invalid port: '{new_server_port_str}'. Must be 1-65535."
        else:
            error_message = "All fields (Server Name, Host, Port) are required."

        current_form_data = {"name": new_server_name, "host": new_server_host,
                             "port": new_server_port_str, "type": new_server_type}
        return render_template('edit_server.html', server=current_form_data, server_id=server_id, error=error_message)

    return render_template('edit_server.html', server=server_to_edit, server_id=server_id, error=error_message)


@app.route('/chat_with_llm', methods=['POST'])
def chat_with_llm():
    """
    Handles chat messages, optionally fetches MCP server data,
    and interacts with OpenAI LLM.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    user_message = data.get('message')
    server_id_str = data.get('server_id') # Will be string like "0", "1", or ""

    if not user_message:
        return jsonify({"error": "No message content provided"}), 400

    if not config.OPENAI_API_KEY:
        return jsonify({"error": "OpenAI API Key not configured by admin."}), 503 # Service Unavailable

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    server_data_for_llm = None
    server_name_for_prompt = "the selected server" # Default

    prompt_context = ""

    if server_id_str and server_id_str.isdigit():
        server_id = int(server_id_str)
        if 0 <= server_id < len(config.MCP_SERVERS):
            server_info = config.MCP_SERVERS[server_id]
            server_name_for_prompt = server_info.get('name', 'this server')
            print(f"Fetching status for {server_info['host']}:{server_info['port']} for LLM context.")
            # Use a shorter timeout for LLM integration to avoid long waits
            status_result = MCPClient.get_server_status(server_info['host'], server_info['port'], timeout=3)
            server_data_for_llm = status_result # For returning to client

            if status_result.get("online"):
                prompt_context = (
                    f"The user is asking about the Minecraft server named '{server_name_for_prompt}' "
                    f"(Host: {server_info['host']}:{server_info['port']}). "
                    f"It is currently online. Version: {status_result.get('version', 'N/A')}. "
                    f"MOTD: \"{status_result.get('motd', 'N/A')}\". "
                    f"Players: {status_result.get('player_count', 'N/A')}/{status_result.get('player_max', 'N/A')}. "
                )
            else:
                prompt_context = (
                    f"The user is asking about the Minecraft server named '{server_name_for_prompt}' "
                    f"(Host: {server_info['host']}:{server_info['port']}). "
                    f"It appears to be offline or there was an issue fetching its status. "
                    f"Error: {status_result.get('error', 'Not specified')}. "
                )
        else:
            prompt_context = "The user selected a server, but the ID was invalid. "

    full_prompt = prompt_context + f"User's message: \"{user_message}\""

    try:
        print(f"Sending to OpenAI. Prompt context prefix: {prompt_context[:200]}...") # Log part of context
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. If the user asks about a Minecraft server and context for that server is provided, use that context to inform your answer. Otherwise, answer generally."},
                {"role": "user", "content": full_prompt}
            ]
        )
        llm_response = completion.choices[0].message.content
        return jsonify({'reply': llm_response, 'server_data_used': server_data_for_llm})
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return jsonify({'error': f'OpenAI API error: {str(e)}'}), 500


@app.route('/send_message', methods=['POST']) # Old endpoint, can be deprecated or removed
def send_message_route():
    if not request.is_json: return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    data = request.get_json()
    message_text = data.get('message')
    if message_text:
        print(f"Received message via /send_message (deprecated): {message_text}")
        return jsonify({"status": "Message received via deprecated endpoint", "message_echo": message_text}), 200
    else:
        return jsonify({"status": "error", "message": "No message content provided"}), 400

# Main execution block
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
