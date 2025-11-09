import os
import pathlib
from typing import List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES_READONLY = ["https://www.googleapis.com/auth/gmail.readonly"]
SCOPES_MODIFY   = ["https://www.googleapis.com/auth/gmail.modify"]

def _paths():
    token_dir = pathlib.Path(os.getenv("TOKEN_DIR", "./data/tokens"))
    token_dir.mkdir(parents=True, exist_ok=True)
    secrets = pathlib.Path(os.getenv("GOOGLE_CLIENT_SECRETS", "./client_secret.json"))
    return token_dir, secrets

def gmail_service(modify: bool = False):
    token_dir, secrets = _paths()
    scope = SCOPES_MODIFY if modify else SCOPES_READONLY
    token_path = token_dir / ("token-modify.json" if modify else "token-read.json")

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scope)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh existing credentials
            creds.refresh(Request())
        else:
            # Installed app flow for local/desktop
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets), scope)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def search_threads(service, q: str, max_results: int = 500) -> List[str]:
    """
    Search threads matching query `q` and return up to `max_results` IDs.
    - Paginates through all result pages instead of returning only the first 500.
    - If `max_results` is None or <= 0, returns all available matches.
    """
    ids: List[str] = []
    page_token = None
    # None means "no limit" (collect all)
    remaining = max_results if max_results and max_results > 0 else None
    while True:
        # Gmail API allows up to 500 per page
        page_size = min(500, remaining) if remaining is not None else 500
        kwargs = {"userId": "me", "q": q, "maxResults": page_size}
        if page_token:
            kwargs["pageToken"] = page_token
        resp = service.users().threads().list(**kwargs).execute()
        batch = [t.get("id") for t in resp.get("threads", [])]
        if batch:
            ids.extend(batch)
        # Stop if we've reached the requested count
        if remaining is not None:
            remaining -= len(batch)
            if remaining <= 0:
                break
        # Advance page; stop if no more pages or no results
        page_token = resp.get("nextPageToken")
        if not page_token or not batch:
            break
    return ids if remaining is None else ids[:max_results]

def ensure_label(service, label_name: str) -> str:
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for lb in labels:
        if lb["name"] == label_name:
            return lb["id"]
    created = service.users().labels().create(userId="me", body={
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show"
    }).execute()
    return created["id"]

def batch_label(service, thread_ids: List[str], add_label_id: str):
    if not thread_ids:
        return 0
    n = 0
    for tid in thread_ids:
        try:
            body = {"addLabelIds": [add_label_id], "removeLabelIds": []}
            service.users().threads().modify(userId="me", id=tid, body=body).execute()
            n += 1
        except Exception:
            # Skip failures to proceed with others
            continue
    return n

def batch_delete(service, thread_ids: List[str], move_to_trash: bool = True) -> int:
    """
    Delete threads by ID.
    - If move_to_trash=True (default), use threads.trash (safer, visible in Gmail Trash).
    - If move_to_trash=False, permanently delete via threads.delete.
    Returns the number of threads successfully processed.
    """
    if not thread_ids:
        return 0
    ok = 0
    errors = 0
    for tid in thread_ids:
        try:
            if move_to_trash:
                service.users().threads().trash(userId="me", id=tid).execute()
            else:
                service.users().threads().delete(userId="me", id=tid).execute()
            ok += 1
        except Exception as e:
            # Count failures; optionally print a few for visibility
            errors += 1
            if errors <= 3:
                print(f"Failed to process thread {tid}: {e}")
            continue
    return ok
