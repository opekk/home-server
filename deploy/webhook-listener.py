import hashlib
import hmac
import json
import os
import subprocess

from http.server import HTTPServer, BaseHTTPRequestHandler

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
REPOS_CONFIG = "/app/repos.json"


def verify_signature(payload: bytes, signature: str) -> bool:
    if not WEBHOOK_SECRET:
        return False
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def load_repos():
    with open(REPOS_CONFIG) as f:
        return json.load(f)


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(content_length)

        signature = self.headers.get("X-Hub-Signature-256", "")
        if not verify_signature(payload, signature):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Invalid signature")
            return

        event = self.headers.get("X-GitHub-Event", "")
        if event != "push":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Ignored event: " + event.encode())
            return

        data = json.loads(payload)
        ref = data.get("ref", "")
        repo_name = data.get("repository", {}).get("name", "unknown")

        print(f"Push to {repo_name} on {ref}")

        repos = load_repos()
        if repo_name not in repos:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"No config for repo: {repo_name}".encode())
            return

        config = repos[repo_name]
        branch = config.get("branch", "main")

        if ref != f"refs/heads/{branch}":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"Ignored branch: {ref}".encode())
            return

        subprocess.Popen(
            [
                "/bin/sh", "/app/deploy.sh",
                repo_name,
                config["clone_url"],
                config["path"],
                config["service"],
                branch,
            ],
            cwd="/app/repo",
        )

        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"Deploying {repo_name}...".encode())

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Webhook listener is running")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 9000), WebhookHandler)
    print("Webhook listener running on port 9000")
    server.serve_forever()
