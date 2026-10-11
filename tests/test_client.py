import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from cascadeur_session import client


class FakeServer(BaseHTTPRequestHandler):
    received = []

    def log_message(self, *a):
        pass

    def _reply(self, body):
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._reply({"status": "ok"})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeServer.received.append(body["code"])
        self._reply({"stdout": "hello\n", "error": None})


class ClientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = HTTPServer(("127.0.0.1", 0), FakeServer)
        cls.url = "http://127.0.0.1:%d" % cls.httpd.server_port
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def test_health(self):
        self.assertIn("ok", client.health(self.url))

    def test_run_prepends_current_scene(self):
        reply = client.run("print('hello')", self.url)
        self.assertTrue(FakeServer.received[-1].startswith("scene = app.current_scene()\n"))
        self.assertIn("hello", client.format_reply(reply))

    def test_connection_error_message(self):
        with self.assertRaises(client.ServerError) as cm:
            client.health("http://127.0.0.1:9", timeout=2)
        self.assertIn("Start script server", str(cm.exception))

    def test_format_reply_plain_text(self):
        self.assertEqual(client.format_reply("not json"), "not json")

    def test_log_path(self):
        self.assertTrue(client.log_path({"LOCALAPPDATA": "C:/L"}).endswith("cascadeur_log.log"))


if __name__ == "__main__":
    unittest.main()
