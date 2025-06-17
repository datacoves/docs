"""
Launch mock service that responds to (https://pythonbasics.org/webserver/):
/api/connections/list
/api/workspaces/list
"""

from http.server import BaseHTTPRequestHandler, HTTPServer

host_name = "localhost"
server_port = 8001


class MockAirbyteServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(dict()))


if __name__ == "__main__":
    web_server = HTTPServer((host_name, server_port), MockAirbyteServer)
    print(f"Server started at http://{host_name}:{server_port}")
    web_server.serve_forever()
