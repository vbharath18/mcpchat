# This file contains the MCP client logic for fetching Minecraft server status.

import sys
# Attempt to ensure user-local site-packages is in path, common in some environments
# This is a workaround for potential PYTHONPATH issues in specific execution contexts.
# The path /home/jules/.local/lib/python3.10/site-packages was identified via `pip show python-mcstatus`.
user_site_packages = "/home/jules/.local/lib/python3.10/site-packages"
if user_site_packages not in sys.path:
    sys.path.insert(0, user_site_packages)

from mcstatus import JavaServer
# For Bedrock servers, you might use: from mcstatus import BedrockServer
# However, mcstatus library's Bedrock support can be less comprehensive than Java.
# For simplicity, this example primarily focuses on JavaServer.

# Import config to use a default server for testing in __main__
# This assumes mcp_client.py is run from a context where 'config' can be imported,
# e.g., from the parent directory of mcp_chat_app or with mcp_chat_app in PYTHONPATH.
if __name__ == '__main__':
    import sys
    import os
    # Adjust path to import config if running mcp_client.py directly for testing
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from mcp_chat_app import config


class MCPClient:
    """
    A client for fetching status information from Minecraft Profile (MCP) servers.
    It uses the 'mcstatus' library to query Java Edition Minecraft servers.
    """

    @staticmethod
    def get_server_status(host: str, port: int = 25565, timeout: int = 5):
        """
        Fetches the status of a Minecraft Java Edition server.

        Args:
            host (str): The hostname or IP address of the Minecraft server.
            port (int): The port number of the Minecraft server (default is 25565).
            timeout (int): Connection timeout in seconds.

        Returns:
            dict: A dictionary containing server status information if online,
                  or an error message if offline or an error occurs.
                  Example online response:
                  {
                      "online": True,
                      "version": "1.19.4 (Paper)",
                      "motd": "A Minecraft Server - Powered by SpigotMC",
                      "player_count": 10,
                      "player_max": 100,
                      "latency": 42.5
                  }
                  Example offline/error response:
                  {
                      "online": False,
                      "error": "Connection timed out"
                  }
        """
        full_address = f"{host}:{port}"
        try:
            # JavaServer.lookup() can take a bit of time, especially if the server is offline.
            # It attempts to resolve the address and create a server object.
            # The actual status check happens with server.status().
            # We can pass a timeout to the lookup method directly in some versions,
            # or it's handled by the underlying socket operations.
            # For mcstatus, the timeout is usually applied to the socket connection.
            server = JavaServer.lookup(full_address, timeout=timeout)

            # Query the server's status. This performs the network request.
            status = server.status()

            return {
                "online": True,
                "version": status.version.name,
                "protocol_version": status.version.protocol,
                "motd": status.motd.to_plain(), # Get plain text MOTD
                "player_count": status.players.online,
                "player_max": status.players.max,
                "latency": status.latency, # Latency of the status ping
                # 'players_sample': status.players.sample # List of Player objects if available
            }
        except ConnectionRefusedError:
            return {"online": False, "error": "Connection refused."}
        except TimeoutError: # Python's built-in TimeoutError
            return {"online": False, "error": f"Connection timed out after {timeout} seconds."}
        except Exception as e:
            # Catch other exceptions from mcstatus (e.g., socket errors, invalid responses)
            # or if the host is not found.
            # str(e) can sometimes be verbose or not user-friendly.
            error_message = str(e)
            if "Name or service not known" in error_message or "nodename nor servname provided" in error_message:
                error_message = f"Server address '{host}' could not be resolved."
            elif not error_message: # Handle cases where str(e) is empty
                error_message = "An unknown error occurred while trying to reach the server."
            return {
                "online": False,
                "error": error_message
            }

if __name__ == '__main__':
    print("MCP Client Test - Fetching Server Status")

    # Use a server from the default config for testing.
    # Ensure this server is likely to be online for a good test, or use a known public one.
    # Hypixel often has specific connection requirements or might block simple pings.
    # Let's try the first server from the default list.
    if config.DEFAULT_MCP_SERVERS:
        test_server_info = config.DEFAULT_MCP_SERVERS[0] # e.g., Hypixel
        # For a more reliable test, one might pick a less complex public server or a local one.
        # test_server_info = {'name': 'A Public Server', 'host': 'demo.mcstatus.io', 'port': 25565} # mcstatus example server

        print(f"\nAttempting to get status for: {test_server_info['name']} ({test_server_info['host']}:{test_server_info['port']})")
        status_result = MCPClient.get_server_status(test_server_info['host'], int(test_server_info['port']))

        if status_result["online"]:
            print(f"  Status: Online")
            print(f"  Version: {status_result.get('version', 'N/A')}")
            print(f"  MOTD: \"{status_result.get('motd', 'N/A')}\"")
            print(f"  Players: {status_result.get('player_count', 'N/A')}/{status_result.get('player_max', 'N/A')}")
            print(f"  Latency: {status_result.get('latency', 'N/A')}ms")
        else:
            print(f"  Status: Offline or Error")
            print(f"  Error: {status_result.get('error', 'No error message provided.')}")
    else:
        print("No default servers configured in config.py to test with.")

    # Example of testing a likely offline or non-existent server
    print(f"\nAttempting to get status for: nonexistentserver.example.com:12345")
    offline_status_result = MCPClient.get_server_status("nonexistentserver.example.com", 12345)
    if not offline_status_result["online"]:
        print(f"  Status: Offline or Error (as expected)")
        print(f"  Error: {offline_status_result.get('error', 'No error message provided.')}")
    else:
        print(f"  Unexpectedly online: {offline_status_result}")

    print("\nMCP Client test finished.")
