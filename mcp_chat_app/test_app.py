import unittest
import json

# Assuming test_app.py is in mcp_chat_app directory, or mcp_chat_app is in PYTHONPATH
# For imports to work correctly when running `python -m unittest mcp_chat_app/test_app.py`
# from the parent directory of mcp_chat_app, the imports should be:
from .app import app # Relative import for app
import config # Direct import for config, will be mcp_chat_app.config

class TestApp(unittest.TestCase):

    def setUp(self):
        """Set up test client and clear MCP_SERVERS before each test."""
        app.testing = True
        self.client = app.test_client()
        # Access MCP_SERVERS through the imported config module
        config.MCP_SERVERS.clear()

    def test_index_page(self):
        """Test the index page loading and basic content."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"MCP Chat", response.data) # Check for title or key heading
        self.assertIn(b"chat-box", response.data) # Check for a key element ID
        self.assertIn(b"message-input", response.data)

    def test_admin_page_get(self):
        """Test the admin page loading and initial content."""
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Manage MCP Server Configurations", response.data)
        self.assertIn(b"No servers configured yet.", response.data)

    def test_add_server_to_admin_page(self):
        """Test adding a server via POST and then viewing it on the admin page."""
        # POST request to add a server
        response_post = self.client.post('/admin', data={
            'server-name': 'TestServer',
            'server-host': 'localhost',
            'server-port': '1234'
        }, follow_redirects=False) # Do not follow redirects to check 302
        self.assertEqual(response_post.status_code, 302) # Should redirect after POST
        self.assertEqual(len(config.MCP_SERVERS), 1)
        self.assertEqual(config.MCP_SERVERS[0]['name'], 'TestServer')
        self.assertEqual(config.MCP_SERVERS[0]['host'], 'localhost')
        self.assertEqual(config.MCP_SERVERS[0]['port'], 1234)

        # GET request to see the server listed
        response_get = self.client.get('/admin')
        self.assertEqual(response_get.status_code, 200)
        self.assertIn(b"TestServer", response_get.data)
        self.assertIn(b"localhost", response_get.data)
        self.assertIn(b"1234", response_get.data)
        self.assertNotIn(b"No servers configured yet.", response_get.data)

    def test_add_server_missing_fields(self):
        """Test adding a server with missing fields."""
        response = self.client.post('/admin', data={
            'server-name': 'TestServerIncomplete',
            # 'server-host' is missing
            'server-port': '5678'
        })
        self.assertEqual(response.status_code, 200) # Should re-render admin page with error
        self.assertIn(b"All fields are required.", response.data)
        self.assertEqual(len(config.MCP_SERVERS), 0) # No server should be added

    def test_add_server_invalid_port(self):
        """Test adding a server with an invalid port number."""
        response = self.client.post('/admin', data={
            'server-name': 'TestServerInvalidPort',
            'server-host': 'testhost',
            'server-port': 'abc' # Invalid port
        })
        self.assertEqual(response.status_code, 200) # Re-renders with error
        self.assertIn(b"Invalid port number.", response.data) # Check for specific error message
        self.assertEqual(len(config.MCP_SERVERS), 0)

    def test_send_message_endpoint(self):
        """Test the /send_message endpoint with valid JSON data."""
        response = self.client.post('/send_message',
                                     data=json.dumps({'message': 'Hello Test'}),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'Message received')
        self.assertEqual(json_response['message_echo'], 'Hello Test')

    def test_send_message_missing_message_key(self):
        """Test /send_message with a missing 'message' key in JSON payload."""
        response = self.client.post('/send_message',
                                     data=json.dumps({'msg': 'Hello Test'}), # Incorrect key
                                     content_type='application/json')
        self.assertEqual(response.status_code, 400)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'error')
        self.assertIn('No message content provided', json_response['message'])

    def test_send_message_not_json(self):
        """Test /send_message with non-JSON data."""
        response = self.client.post('/send_message',
                                     data={'message': 'Hello Test'}) # Form data, not JSON
        self.assertEqual(response.status_code, 400)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'error')
        self.assertIn('Request must be JSON', json_response['message'])

if __name__ == '__main__':
    # To run these tests:
    # 1. Navigate to the directory containing the 'mcp_chat_app' package.
    # 2. Run: python -m unittest mcp_chat_app/test_app.py
    unittest.main()
