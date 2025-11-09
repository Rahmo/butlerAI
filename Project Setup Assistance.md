# Cascade Chat Conversation

  Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

how to setup running this project? venv ?

### Planner Response

To give you precise setup steps, I’ll quickly read the key project files (`README.md`, `requirements.txt`, `.env.dev`, `server.py`, `gmail_client.py`, and `rules.py`) to see what environment variables and run commands are expected.

*Viewed [README.md](file:///C:/Users/rahmo/butlerAI/README.md) *

*Viewed [requirements.txt](file:///C:/Users/rahmo/butlerAI/requirements.txt) *

*Viewed [.env.dev](file:///C:/Users/rahmo/butlerAI/.env.dev) *

*Viewed [server.py](file:///C:/Users/rahmo/butlerAI/server.py) *

*Viewed [gmail_client.py](file:///C:/Users/rahmo/butlerAI/gmail_client.py) *

*Viewed [rules.py](file:///C:/Users/rahmo/butlerAI/rules.py) *

### Planner Response

Here’s the quickest way to set this up locally on Windows using a virtual environment.

# Setup Steps

- **[Create and activate venv]**
  - PowerShell:
    ```
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```
  - Verify:
    ```
    python --version
    pip --version
    ```

- **[Install dependencies]**
  ```
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  ```

- **[Create .env file]**
  - Duplicate [C:\Users\rahmo\butlerAI\.env.dev](cci:7://file:///C:/Users/rahmo/butlerAI/.env.dev:0:0-0:0) to `.env` in the same folder, then adjust values as needed:
    - `GOOGLE_CLIENT_SECRETS=./client_secret.json` → Place your OAuth client JSON there.
    - `TOKEN_DIR=./data/tokens` → Tokens are stored here (auto-created).
    - `ALLOWED_USERS` → Optional allowlist.
    - `REVIEW_LABEL`, `HOST`, `PORT` → Defaults are fine.

- **[Provide Google OAuth client]**
  - Download OAuth Client ID JSON (Desktop app) from Google Cloud Console and save as `client_secret.json` at repo root (or change `GOOGLE_CLIENT_SECRETS` in `.env`).
  - First run will open a browser for consent and create token files under `data/tokens/`.

- **[Run the server]**
  - Start the ASGI app:
    ```
    uvicorn server:app --host 0.0.0.0 --port 8080
    ```
  - Health check:
    ```
    curl http://localhost:8080/health
    ```
  - You can also hit the MCP tools via your MCP client if you’re integrating with one (the ASGI app is created in [server.py](cci:7://file:///C:/Users/rahmo/butlerAI/server.py:0:0-0:0) with `mcp.http_app()`).

# Available MCP Tools (from [server.py](cci:7://file:///C:/Users/rahmo/butlerAI/server.py:0:0-0:0))
- [preview_cleanup(rules?, limit_per_rule?)](cci:1://file:///C:/Users/rahmo/butlerAI/server.py:19:0-32:82)
- [label_candidates(rules?, review_label?)](cci:1://file:///C:/Users/rahmo/butlerAI/server.py:34:0-50:86)
- [delete_labeled(label?, older_than_days?, dry_run?)](cci:1://file:///C:/Users/rahmo/butlerAI/server.py:52:0-66:64)
- [top_noisy_senders(since_days?, max_senders?)](cci:1://file:///C:/Users/rahmo/butlerAI/server.py:68:0-85:14)
- [info()](cci:1://file:///C:/Users/rahmo/butlerAI/server.py:87:0-97:5)

# Notes and Tips

- **First-time auth**: The first call that touches Gmail will open your browser. After you finish consent, tokens are saved and reused.
- **Environment loading**: `python-dotenv` loads `.env` automatically via `load_dotenv()` in [server.py](cci:7://file:///C:/Users/rahmo/butlerAI/server.py:0:0-0:0).
- **Potential refresh bug**: In [gmail_client.py](cci:7://file:///C:/Users/rahmo/butlerAI/gmail_client.py:0:0-0:0), token refresh uses `requests.Request()` but should be `from google.auth.transport.requests import Request` and then `creds.refresh(Request())`. If you hit a refresh error, tell me and I’ll patch it.

# Deactivate venv
- When done:
  ```
  deactivate
  ```

Want me to run the commands for venv creation and requirements install from your project directory? I can propose them for you to approve.