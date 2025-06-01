# This is the main Flask application file.

from flask import Flask, render_template, request, jsonify, redirect, url_for

# Import configurations. We will be modifying MCP_SERVERS.
# Note: In a real multi-process/multi-threaded server, directly modifying
# a list like this without thread safety mechanisms (locks) would be problematic.
# For this educational example, it's fine.
import config # This way we can access config.MCP_SERVERS

# Create a Flask application instance
app = Flask(__name__)
# Flask will automatically look for 'templates' and 'static' folders
# in the same directory as this file.

# Load configurations if needed (e.g., app.config.from_object('config'))
# For now, we directly use the imported config.MCP_SERVERS list.


@app.route('/')
def index():
    """
    Serves the main chat interface page.
    Renders the index.html template.
    """
    return render_template('index.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """
    Serves the admin configuration page.
    Handles GET requests to display the page and server list.
    Handles POST requests to add a new server configuration.
    """
    if request.method == 'POST':
        # Get data from the form
        server_name = request.form.get('server-name')
        server_host = request.form.get('server-host')
        server_port = request.form.get('server-port')

        # Basic validation (in a real app, this would be more robust)
        if server_name and server_host and server_port:
            try:
                # Ensure port is an integer
                port = int(server_port)
                new_server = {
                    "name": server_name,
                    "host": server_host,
                    "port": port
                }
                config.MCP_SERVERS.append(new_server)
                print(f"Added new server: {new_server}") # Server-side log
                # Redirect to the admin page (GET request) to display the updated list
                return redirect(url_for('admin'))
            except ValueError:
                # Handle error if port is not a valid number
                # For simplicity, just re-render with an error message or ignore
                print(f"Error: Port '{server_port}' is not a valid number.")
                # Pass an error message to the template if desired
                return render_template('admin.html', servers=config.MCP_SERVERS, error="Invalid port number.")
        else:
            # Handle error if any field is missing
            print("Error: Missing form data for adding server.")
            return render_template('admin.html', servers=config.MCP_SERVERS, error="All fields are required.")

    # For GET requests, just render the page with the current list of servers
    return render_template('admin.html', servers=config.MCP_SERVERS)


@app.route('/send_message', methods=['POST'])
def send_message_route():
    """
    API endpoint to receive messages from the chat interface.
    Expects a JSON payload with a "message" field.
    """
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    data = request.get_json()
    message_text = data.get('message')

    if message_text:
        print(f"Received message via /send_message: {message_text}")
        # Here, you would typically process the message:
        # - Send it to the MCPClient
        # - Broadcast it to other users via WebSockets, etc.
        # For now, we just acknowledge receipt.
        return jsonify({"status": "Message received", "message_echo": message_text}), 200
    else:
        return jsonify({"status": "error", "message": "No message content provided"}), 400


# Main execution block to run the Flask development server
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
