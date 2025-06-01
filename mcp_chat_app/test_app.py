import unittest
import json
import copy
from unittest.mock import patch, MagicMock

# Assuming test_app.py is in mcp_chat_app directory, or mcp_chat_app is in PYTHONPATH
from .app import app, initialize_app_config # Import Flask app instance and init function
from . import config # Import config module (mcp_chat_app.config)
from .mcp_client import MCPClient # Import MCPClient for direct testing

class TestApp(unittest.TestCase):

    def setUp(self):
        """Set up test client and clear/reset configurations before each test."""
        app.testing = True
        self.client = app.test_client()

        # Reset MCP_SERVERS and load defaults by calling the app's initialization logic
        config.MCP_SERVERS.clear()
        # Ensure DEFAULT_MCP_SERVERS is available for re-initialization
        if not hasattr(config, 'DEFAULT_MCP_SERVERS_ORIGINAL'):
            # Store an original copy if not already stored, to prevent modification by tests
            config.DEFAULT_MCP_SERVERS_ORIGINAL = copy.deepcopy(config.DEFAULT_MCP_SERVERS)
        else:
             # Ensure DEFAULT_MCP_SERVERS is reset to original state before re-initializing
            config.DEFAULT_MCP_SERVERS = copy.deepcopy(config.DEFAULT_MCP_SERVERS_ORIGINAL)

        initialize_app_config() # This should load defaults into MCP_SERVERS

        # Reset OpenAI API Key
        config.OPENAI_API_KEY = None

        # Set a dummy secret key for flash messages context
        app.secret_key = 'test_secret_key_for_unittest'


    def tearDown(self):
        """Clean up after tests if necessary."""
        config.MCP_SERVERS.clear()
        config.OPENAI_API_KEY = None
        # Restore original DEFAULT_MCP_SERVERS if it was modified or ensure it's clean for next setUp
        if hasattr(config, 'DEFAULT_MCP_SERVERS_ORIGINAL'):
            config.DEFAULT_MCP_SERVERS = copy.deepcopy(config.DEFAULT_MCP_SERVERS_ORIGINAL)


    # --- Test Index and Basic Admin Pages ---
    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"MCP Chat with LLM", response.data)
        self.assertIn(b"mcp-server-select", response.data) # Check for server dropdown

    def test_admin_page_get(self):
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"MCP Server & LLM Configuration", response.data)
        # Defaults should be loaded by setUp->initialize_app_config
        if config.DEFAULT_MCP_SERVERS:
             self.assertIn(bytes(config.DEFAULT_MCP_SERVERS[0]['name'], 'utf-8'), response.data)
        else:
            self.assertIn(b"No servers configured yet.", response.data)


    # --- Test Default Server Loading ---
    def test_admin_page_loads_defaults_explicitly(self):
        config.MCP_SERVERS.clear() # Ensure it's empty
        # Re-initialize DEFAULT_MCP_SERVERS to original state before calling initialize_app_config
        if hasattr(config, 'DEFAULT_MCP_SERVERS_ORIGINAL'):
            config.DEFAULT_MCP_SERVERS = copy.deepcopy(config.DEFAULT_MCP_SERVERS_ORIGINAL)
        else: # Should not happen if setUp is working
            config.DEFAULT_MCP_SERVERS = [{'name':'FallbackDefault','host':'fb.host','port':123,'type':'Test'}]

        initialize_app_config() # Call the specific function from app.py
        self.assertTrue(len(config.MCP_SERVERS) > 0, "MCP_SERVERS should be populated from defaults")
        if config.DEFAULT_MCP_SERVERS: # Check if there are defaults to compare against
            self.assertEqual(config.MCP_SERVERS[0]['name'], config.DEFAULT_MCP_SERVERS[0]['name'])


    # --- Test Server Management ---
    def test_add_server_to_admin_page(self):
        initial_server_count = len(config.MCP_SERVERS)
        response_post = self.client.post('/admin', data={
            'server-name': 'NewTestServer', 'server-host': 'new.host.com',
            'server-port': '5555', 'server-type': 'TestType'
        }, follow_redirects=True) # Follow redirect to check flash message and final page
        self.assertEqual(response_post.status_code, 200)
        self.assertIn(b"Server &#39;NewTestServer&#39; added successfully!", response_post.data)
        self.assertEqual(len(config.MCP_SERVERS), initial_server_count + 1)
        self.assertEqual(config.MCP_SERVERS[-1]['name'], 'NewTestServer')

    def test_delete_server(self):
        # Ensure there's a server to delete (defaults are loaded in setUp)
        if not config.MCP_SERVERS: self.fail("MCP_SERVERS empty, cannot test delete.")

        initial_server_count = len(config.MCP_SERVERS)
        server_name_to_delete = config.MCP_SERVERS[0]['name']

        response = self.client.post(f'/admin/delete_server/0', follow_redirects=True)
        self.assertEqual(response.status_code, 200) # After redirect
        # Check for HTML escaped apostrophe: &#39;
        self.assertIn(bytes(f"Server &#39;{server_name_to_delete}&#39; deleted successfully.", 'utf-8'), response.data)
        self.assertEqual(len(config.MCP_SERVERS), initial_server_count - 1)

    def test_delete_server_invalid_index(self):
        initial_server_count = len(config.MCP_SERVERS)
        response = self.client.post('/admin/delete_server/999', follow_redirects=True) # Invalid index
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Error: Attempted to delete server with invalid ID.", response.data)
        self.assertEqual(len(config.MCP_SERVERS), initial_server_count) # No change

    def test_edit_server_get(self):
        if not config.MCP_SERVERS: self.fail("MCP_SERVERS empty, cannot test edit GET.")
        server_to_edit = config.MCP_SERVERS[0]
        response = self.client.get(f'/admin/edit_server/0')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Edit Server Configuration", response.data)
        self.assertIn(bytes(server_to_edit['name'], 'utf-8'), response.data)
        self.assertIn(bytes(server_to_edit['host'], 'utf-8'), response.data)

    def test_edit_server_post_success(self):
        if not config.MCP_SERVERS: self.fail("MCP_SERVERS empty, cannot test edit POST.")
        original_server_name = config.MCP_SERVERS[0]['name']

        response = self.client.post('/admin/edit_server/0', data={
            'server-name': 'UpdatedServer', 'server-host': 'updated.host.com',
            'server-port': '12345', 'server-type': 'UpdatedType'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(f"Server &#39;UpdatedServer&#39; updated successfully.", 'utf-8'), response.data)
        self.assertEqual(config.MCP_SERVERS[0]['name'], 'UpdatedServer')
        self.assertEqual(config.MCP_SERVERS[0]['host'], 'updated.host.com')
        self.assertNotEqual(config.MCP_SERVERS[0]['name'], original_server_name)

    def test_edit_server_post_invalid_data(self):
        if not config.MCP_SERVERS: self.fail("MCP_SERVERS empty, cannot test edit POST invalid.")
        original_server = copy.deepcopy(config.MCP_SERVERS[0])

        response = self.client.post('/admin/edit_server/0', data={
            'server-name': '', 'server-host': 'updated.host.com', # Empty name
            'server-port': '12345', 'server-type': 'UpdatedType'
        }) # No redirect follow, check rendered page
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"All fields (Server Name, Host, Port) are required.", response.data)
        self.assertEqual(config.MCP_SERVERS[0]['name'], original_server['name']) # Should not change


    # --- Test API Key Configuration ---
    def test_save_api_key(self):
        response = self.client.post('/admin/save_api_key', data={'openai-api-key': 'test_key_123'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"OpenAI API Key saved successfully.", response.data)
        self.assertEqual(config.OPENAI_API_KEY, 'test_key_123')

    def test_admin_page_shows_api_key_status(self):
        config.OPENAI_API_KEY = None
        response_none = self.client.get('/admin')
        self.assertIn(b"API Key is NOT set.", response_none.data)

        config.OPENAI_API_KEY = "test_key_123"
        response_set = self.client.get('/admin')
        self.assertIn(b"API Key is set", response_set.data)
        self.assertIn(b"test...", response_set.data) # Check for partial key display


    # --- Test MCPClient (with mocks) ---
    @patch('mcp_chat_app.mcp_client.JavaServer.lookup')
    def test_mcp_client_get_status_online(self, mock_lookup):
        mock_server_instance = MagicMock()
        mock_status_response = MagicMock()
        mock_status_response.version.name = "1.19 Test"
        mock_status_response.version.protocol = 750
        mock_status_response.motd.to_plain.return_value = "Test MOTD" # Mock to_plain()
        mock_status_response.players.online = 10
        mock_status_response.players.max = 100
        mock_status_response.latency = 50.0

        mock_server_instance.status.return_value = mock_status_response
        mock_lookup.return_value = mock_server_instance

        client_result = MCPClient.get_server_status('dummy.host', 25565)

        self.assertTrue(client_result['online'])
        self.assertEqual(client_result['version'], "1.19 Test")
        self.assertEqual(client_result['motd'], "Test MOTD")
        self.assertEqual(client_result['player_count'], 10)
        mock_lookup.assert_called_once_with("dummy.host:25565", timeout=5) # Default timeout

    @patch('mcp_chat_app.mcp_client.JavaServer.lookup')
    def test_mcp_client_get_status_offline_or_error(self, mock_lookup):
        mock_lookup.side_effect = Exception("Test connection error")
        client_result = MCPClient.get_server_status('error.host', 25565)
        self.assertFalse(client_result['online'])
        self.assertIn("Test connection error", client_result['error'])


    # --- Test /chat_with_llm Endpoint (with mocks) ---
    @patch('mcp_chat_app.app.MCPClient.get_server_status') # Path to MCPClient as imported in app.py
    @patch('mcp_chat_app.app.OpenAI') # Path to OpenAI as imported in app.py
    def test_chat_with_llm_no_api_key(self, mock_openai_class, mock_mcp_get_status):
        config.OPENAI_API_KEY = None
        response = self.client.post('/chat_with_llm', json={'message': 'Hello'})
        self.assertEqual(response.status_code, 503) # Service Unavailable
        json_data = response.get_json()
        self.assertIn("OpenAI API Key not configured", json_data['error'])

    @patch('mcp_chat_app.app.MCPClient.get_server_status')
    @patch('mcp_chat_app.app.OpenAI')
    def test_chat_with_llm_general_query(self, mock_openai_class, mock_mcp_get_status):
        config.OPENAI_API_KEY = 'fake_test_key'
        mock_openai_instance = mock_openai_class.return_value
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "LLM general reply"
        mock_openai_instance.chat.completions.create.return_value = mock_completion

        response = self.client.post('/chat_with_llm', json={'message': 'Hello', 'server_id': ''})
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['reply'], "LLM general reply")
        mock_mcp_get_status.assert_not_called() # No server_id, so no MCP client call
        # Check that the prompt doesn't contain server specific context markers
        args, kwargs = mock_openai_instance.chat.completions.create.call_args
        user_prompt = kwargs['messages'][-1]['content']
        self.assertNotIn("The user is asking about the Minecraft server", user_prompt)


    @patch('mcp_chat_app.app.MCPClient.get_server_status')
    @patch('mcp_chat_app.app.OpenAI')
    def test_chat_with_llm_with_mcp_server_online(self, mock_openai_class, mock_mcp_get_status):
        config.OPENAI_API_KEY = 'fake_test_key'
        # Ensure there's a server to select
        if not config.MCP_SERVERS: self.fail("MCP_SERVERS empty, cannot test LLM with server context.")

        mock_mcp_get_status.return_value = {
            "online": True, "version": "1.20", "motd": "Test Online MOTD",
            "player_count": 5, "player_max": 20, "latency": 30
        }
        mock_openai_instance = mock_openai_class.return_value
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "LLM reply about online server"
        mock_openai_instance.chat.completions.create.return_value = mock_completion

        server_to_query = config.MCP_SERVERS[0]
        response = self.client.post('/chat_with_llm', json={'message': 'Tell me about this server.', 'server_id': '0'})

        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['reply'], "LLM reply about online server")
        mock_mcp_get_status.assert_called_once_with(server_to_query['host'], server_to_query['port'], timeout=3)

        args, kwargs = mock_openai_instance.chat.completions.create.call_args
        user_prompt = kwargs['messages'][-1]['content']
        self.assertIn("Test Online MOTD", user_prompt) # Check if server context is in prompt
        self.assertIn(f"Players: 5/20", user_prompt)


    @patch('mcp_chat_app.app.MCPClient.get_server_status')
    @patch('mcp_chat_app.app.OpenAI')
    def test_chat_with_llm_with_mcp_server_offline(self, mock_openai_class, mock_mcp_get_status):
        config.OPENAI_API_KEY = 'fake_test_key'
        if not config.MCP_SERVERS: self.fail("MCP_SERVERS empty for offline test.")

        mock_mcp_get_status.return_value = {"online": False, "error": "Connection timed out"}
        mock_openai_instance = mock_openai_class.return_value
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "LLM reply about offline server"
        mock_openai_instance.chat.completions.create.return_value = mock_completion

        response = self.client.post('/chat_with_llm', json={'message': 'Is this server down?', 'server_id': '0'})
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['reply'], "LLM reply about offline server")

        args, kwargs = mock_openai_instance.chat.completions.create.call_args
        user_prompt = kwargs['messages'][-1]['content']
        self.assertIn("appears to be offline", user_prompt)
        self.assertIn("Error: Connection timed out", user_prompt)


    @patch('mcp_chat_app.app.MCPClient.get_server_status')
    @patch('mcp_chat_app.app.OpenAI')
    def test_chat_with_llm_openai_api_error(self, mock_openai_class, mock_mcp_get_status):
        config.OPENAI_API_KEY = 'fake_test_key'
        mock_openai_instance = mock_openai_class.return_value
        mock_openai_instance.chat.completions.create.side_effect = Exception("OpenAI API is down")

        response = self.client.post('/chat_with_llm', json={'message': 'Hello', 'server_id': ''})
        self.assertEqual(response.status_code, 500)
        json_data = response.get_json()
        self.assertIn("OpenAI API error: OpenAI API is down", json_data['error'])


if __name__ == '__main__':
    unittest.main()
