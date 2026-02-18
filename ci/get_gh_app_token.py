import json
import os
import time
import subprocess

import jwt

app_id = os.environ["GH_APP_ID"]
key_path = os.environ["GH_APP_KEYFILE"]
owner = os.environ["GH_OWNER"]
repo = os.environ["GH_REPO"]

with open(key_path, "rb") as f:
    private_key = f.read()

now = int(time.time())
payload = {"iat": now - 30, "exp": now + 9 * 60, "iss": app_id}
app_jwt = jwt.encode(payload, private_key, algorithm="RS256")

headers = [
    "-H",
    f"Authorization: Bearer {app_jwt}",
    "-H",
    "Accept: application/vnd.github+json",
]


def curl_json(cmd: list[str]) -> dict:
    out = subprocess.check_output(cmd)
    return json.loads(out.decode("utf-8"))


inst = curl_json(
    ["curl", "-sS"] + headers + [f"https://api.github.com/repos/{owner}/{repo}/installation"]
)
inst_id = inst["id"]

tok = curl_json(
    ["curl", "-sS", "-X", "POST"]
    + headers
    + [f"https://api.github.com/app/installations/{inst_id}/access_tokens"]
)

print(tok["token"])
