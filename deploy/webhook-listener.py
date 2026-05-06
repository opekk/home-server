import hashlib
import hmac
import json
import os
import re
import subprocess

from http.server import HTTPServer, BaseHTTPRequestHandler

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
REPOS_CONFIG = "/app/repos.json"

SKIP_TYPES = {"docs", "chore", "style", "test", "ci"}
SKIP_MARKER_RE = re.compile(r"\[skip (?:deploy|ci)\]", re.IGNORECASE)
CC_PREFIX_RE = re.compile(r"^(\w+)(?:\([^)]*\))?!?:")


def should_skip_deploy(commit_messages):
    if not commit_messages:
        return False, "no commits in payload"

    for msg in commit_messages:
        if SKIP_MARKER_RE.search(msg):
            return True, "[skip deploy] / [skip ci] marker found"

    types = []
    for msg in commit_messages:
        first_line = msg.splitlines()[0] if msg else ""
        m = CC_PREFIX_RE.match(first_line)
        if not m:
            return False, f"non-conventional commit: {first_line!r}"
        types.append(m.group(1).lower())

    if all(t in SKIP_TYPES for t in types):
        return True, f"all commits are non-code types: {types}"
    return False, f"code-affecting types present: {types}"


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
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid Content-Length")
            return
        payload = self.rfile.read(content_length)

        signature = self.headers.get("X-Hub-Signature-256", "")
        if not verify_signature(payload, signature):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Invalid signature")
            return

        event = self.headers.get("X-GitHub-Event", "")
        if event != "push":
            self.send_response(204)
            self.end_headers()
            return

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON payload")
            return
        ref = data.get("ref", "")
        repo_name = data.get("repository", {}).get("name", "unknown")

        print(f"Push to {repo_name} on {ref}")

        try:
            repos = load_repos()
        except (OSError, json.JSONDecodeError) as e:
            print(f"Failed to load {REPOS_CONFIG}: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Server config error")
            return
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

        commit_messages = [c.get("message", "") for c in data.get("commits", [])]
        skip, reason = should_skip_deploy(commit_messages)
        if skip:
            print(f"Skipping deploy for {repo_name}: {reason}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"Skipped: {reason}".encode())
            return
        print(f"Proceeding with deploy for {repo_name}: {reason}")

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
