# MCP Test Client (Streamable HTTP)

This is a minimal pure MCP client to connect to your FastMCP server over Streamable HTTP and call tools.

- Server ASGI app: `server.py` (`app = mcp.http_app()`)
- Default endpoint path: `/mcp`

## Install

Use your existing venv and add the MCP client dependency:

```powershell
pip install mcp
```

Or, from this folder:

```powershell
pip install -r requirements.txt
```

## Run the server (separate terminal)

```powershell
uvicorn server:app --host 127.0.0.1 --port 8080
```

Health check:

```powershell
curl http://127.0.0.1:8080/health
```

## List tools
```powershell
 python client/async_run_client.py --server http://127.0.0.1:8080 --path /mcp --list
```
Available tools:
- preview_cleanup: Dry-run. Return counts and sample thread IDs that match cleanup rules.
- label_candidates: Apply the review label to all threads matching the rules (safe step).
- delete_labeled: Delete threads that have the review label AND are older than N days.
Use dry_run=true to return counts without deleting.
- top_noisy_senders: Return the senders that show up most frequently since N days (rough heuristic via query batching).
- info: Server info & safety policy.\
- 
```powershell
python client/async_run_client.py --server http://127.0.0.1:8080 --path /mcp --list
```

## Call tools

- `info` (no args)
```powershell
python client/async_run_client.py --tool info
python client/async_run_client.py --list

```

- `preview_cleanup(rules?, limit_per_rule?)`
```powershell
python client/async_run_client.py --tool preview_cleanup limit_per_rule=50

1. 
    - `rules` (optional)
    - (optional, default 500) `limit_per_rule`

python client/async_run_client.py --tool preview_cleanup --args '{\"limit_per_rule\": 50}'

```

- `label_candidates(rules?, review_label?)`
```powershell
1. **`label_candidates`** - Actually applies labels (no dry-run option)
    - `rules` (optional)
    - (optional) `review_label`

python client/async_run_client.py --tool label_candidates review_label=trash-candidate
python client/async_run_client.py --tool label_candidates --args '{\"review_label\": \"Trash-Candidate\"}'
```

- `delete_labeled(label?, older_than_days?, dry_run?)`
  - Dry run (recommended first):
```powershell
1. **`delete_labeled`** - Has dry-run functionality
    - `label` (optional)
    - (optional, default 7) `older_than_days`
    - (optional, default True) `dry_run`
    - `permanent` (optional, default False)

python client/async_run_client.py --tool delete_labeled label=Trash-Candidate older_than_days=0 dry_run=true
 
python client/async_run_client.py --tool delete_labeled --args '{\"older_than_days\": 7, \"dry_run\": true}'
```
  - Execute delete:
```powershell
python client/async_run_client.py --tool delete_labeled label=Trash-Candidate older_than_days=0 dry_run=false

python client/async_run_client.py --tool delete_labeled --args '{\"older_than_days\": 7, \"dry_run\": false}'
```

- `top_noisy_senders(since_days?, max_senders?)`
```powershell
python client/async_run_client.py --tool top_noisy_senders --args '{\"since_days\": 30, \"max_senders\": 10}'
```

- `auto_unsubscribe(max_emails?, dry_run?)`
```powershell
python client/async_run_client.py --tool auto_unsubscribe --args '{\"max_emails\": 1000, \"dry_run\": true}'
```
# Dry run (default) - just see what unsubscribe links are found
python client/async_run_client.py --tool auto_unsubscribe

# With custom parameters
python client/async_run_client.py --tool auto_unsubscribe max_emails=1000 dry_run=true

# Actually perform unsubscribes (use with caution!)
python client/async_run_client.py --tool auto_unsubscribe dry_run=false
## Notes
- The client defaults to `--server http://127.0.0.1:8080` and `--path /mcp`.
- First Gmail access will trigger OAuth in your browser and cache tokens under `TOKEN_DIR`.
- If you see a 404 at `/mcp`, try `--path /`.
