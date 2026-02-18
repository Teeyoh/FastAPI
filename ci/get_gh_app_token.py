import os
import time

import httpx
import jwt  # pyjwt


def main() -> None:
    app_id = os.environ["GH_APP_ID"]
    key_path = os.environ["GH_APP_KEYFILE"]
    owner = os.environ["GH_OWNER"]
    repo = os.environ["GH_REPO"]

    with open(key_path, "rb") as f:
        private_key = f.read()

    now = int(time.time())
    payload = {"iat": now - 30, "exp": now + 9 * 60, "iss": app_id}
    app_jwt = jwt.encode(payload, private_key, algorithm="RS256")

    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
    }

    with httpx.Client(timeout=30.0, headers=headers) as client:
        # Find installation for this repo
        inst_resp = client.get(f"https://api.github.com/repos/{owner}/{repo}/installation")
        inst_resp.raise_for_status()
        inst_id = inst_resp.json()["id"]

        # Create short-lived installation token
        tok_resp = client.post(f"https://api.github.com/app/installations/{inst_id}/access_tokens")
        tok_resp.raise_for_status()
        print(tok_resp.json()["token"])


if __name__ == "__main__":
    main()
