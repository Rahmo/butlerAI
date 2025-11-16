import os
from typing import List, Optional, Dict, Any
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.responses import JSONResponse
from fastmcp import FastMCP
from dotenv import load_dotenv
import requests
from gmail_client import gmail_service, search_threads, ensure_label, batch_label, batch_delete
from rules import DEFAULT_RULES
import logging
import re
load_dotenv()
REVIEW_LABEL = os.getenv("REVIEW_LABEL", "trash-can")

mcp = FastMCP("gmail-cleanup")

# Health endpoint for k8s/ingress
@mcp.custom_route("/health", methods=["GET"])
async def health(_req) -> PlainTextResponse:
    return PlainTextResponse("ok")


@mcp.tool
def preview_cleanup(rules: Optional[List[str]] = None, limit_per_rule: int = 500) -> Dict[str, Any]:
    """
    Dry-run. Return counts and sample thread IDs that match cleanup rules.
    """

    logger = logging.getLogger(__name__)

    try:
        svc = gmail_service(modify=False)
    except Exception as e:
        logger.error(f"Failed to initialize Gmail service: {e}")
        return {"error": "Failed to connect to Gmail service", "total_hits": 0, "by_rule": {}}

    rules = rules or DEFAULT_RULES
    summary = {}
    total = 0
    errors = []

    for rule in rules:
        try:
            logger.debug(f"Processing rule: {rule}")
            ids = search_threads(svc, rule, max_results=limit_per_rule)
            summary[rule] = {"count": len(ids), "sample": ids[:10]}
            total += len(ids)
            logger.debug(f"Rule '{rule}' matched {len(ids)} threads")
        except Exception as e:
            logger.error(f"Error processing rule '{rule}': {e}")
            errors.append(f"Rule '{rule}': {str(e)}")
            summary[rule] = {"count": 0, "sample": [], "error": str(e)}

    result = {
        "total_hits": total,
        "by_rule": summary,
        "review_label": REVIEW_LABEL
    }

    if errors:
        result["errors"] = errors

    return result


@mcp.tool
def label_candidates(rules: Optional[List[str]] = None, review_label: Optional[str] = None) -> Dict[str, Any]:
    """
    Apply the review label to all threads matching the rules (safe step).
    """
    svc = gmail_service(modify=True)
    rules = rules or DEFAULT_RULES
    label_name = review_label or REVIEW_LABEL
    label_id = ensure_label(svc, label_name)
    labeled_total = 0
    per_rule = {}
    for rule in rules:
        ids = search_threads(svc, rule, max_results=0)
        n = batch_label(svc, ids, label_id)
        labeled_total += n
        per_rule[rule] = n
    return {"labeled_total": labeled_total, "label": label_name, "per_rule": per_rule}

@mcp.tool
def delete_labeled(label: Optional[str] = None, older_than_days: int = 7, dry_run: bool = True, permanent: bool = False) -> Dict[str, Any]:
    """
    Delete threads that have the review label AND are older than N days.
    Use dry_run=true to return counts without deleting.
    """
    svc_ro = gmail_service(modify=False)
    svc = gmail_service(modify=True)
    label_name = label or REVIEW_LABEL
    q = f'label:"{label_name}" older_than:{older_than_days}d'
    # Fetch ALL matching threads (0 => no limit) so we don't stop at 500
    ids = search_threads(svc_ro, q, max_results=0)
    if dry_run:
        return {"would_delete": len(ids), "query": q, "label": label_name, "sample": ids[:10]}
    deleted = batch_delete(svc, ids, move_to_trash=not permanent)
    failed = max(0, len(ids) - deleted)
    return {"deleted": deleted, "failed": failed, "label": label_name, "query": q, "permanent": permanent}

@mcp.tool
def top_noisy_senders(since_days: int = 60, max_senders: int = 20) -> Dict[str, int]:
    """
    Return the senders that show up most frequently since N days (rough heuristic via query batching).
    """
    svc = gmail_service(modify=False)
    # Query recent threads, then expand and tally senders (cheap approach via messages.list + headers).
    ids = search_threads(svc, f"newer_than:{since_days}d", max_results=1000)
    senders: Dict[str, int] = {}
    for tid in ids[:1000]:
        thread = svc.users().threads().get(userId="me", id=tid, format="metadata", metadataHeaders=["From"]).execute()
        for msg in thread.get("messages", []):
            for h in msg.get("payload", {}).get("headers", []):
                if h.get("name") == "From":
                    senders[h["value"]] = senders.get(h["value"], 0) + 1
    # Return top-N
    top = dict(sorted(senders.items(), key=lambda kv: kv[1], reverse=True)[:max_senders])
    return top


@mcp.tool
def auto_unsubscribe(max_emails: int = 500, dry_run: bool = True) -> dict:
    """
    Scans recent messages for List-Unsubscribe headers and performs opt-outs.
    """
    svc = gmail_service(modify=True)
    # get recent threads
    threads = svc.users().threads().list(userId="me", q="list:(*) newer_than:60d", maxResults=max_emails).execute().get("threads", [])
    unsub_links = []

    for t in threads:
        msg = svc.users().messages().get(userId="me", id=t["id"], format="metadata", metadataHeaders=["List-Unsubscribe"]).execute()
        for h in msg.get("payload", {}).get("headers", []):
            if h["name"].lower() == "list-unsubscribe":
                value = h["value"]
                # Extract links (mailto: or http)
                urls = re.findall(r"<([^>]+)>", value)
                for u in urls:
                    unsub_links.append(u)

    if dry_run:
        return {"found": len(unsub_links), "sample": unsub_links[:10]}

    success = []
    for u in unsub_links:
        try:
            if u.startswith("mailto:"):
                success.append({"mailto": u})
                continue  # sending mail would require SMTP creds
            r = requests.get(u, timeout=10)
            success.append({"url": u, "status": r.status_code})
        except Exception as e:
            success.append({"url": u, "error": str(e)})

    return {"unsubscribed": len(success), "details": success[:10]}

@mcp.tool
def info() -> Dict[str, Any]:
    """
    Server info & safety policy.
    """
    return {
        "name": "gmail-cleanup",
        "policy": "label-first delete-later; minimal scopes; logs recommended",
        "review_label": REVIEW_LABEL,
        "default_rules": DEFAULT_RULES,
    }

# async def api_delete_labeled(request):
#     body = await request.json()
#     args = {
#       "label": body.get("label","Trash-Candidate"),
#       "older_than_days": body.get("older_than_days", 7),
#       "dry_run": body.get("dry_run", True)
#     }
#     # call MCP tool in-process (direct function) or via JSON-RPC client if split
#     result = delete_labeled(**args)   # direct call since it’s same process
#     return JSONResponse(result)



# ASGI app for Uvicorn
app = mcp.http_app()
# app.routes.append(Route("/api/delete_labeled", api_delete_labeled, methods=["POST"]))