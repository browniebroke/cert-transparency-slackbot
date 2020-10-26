import json
import logging
from typing import Any, Dict

from slack import WebClient

from . import config, fb

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

slack_client = WebClient(token=config.SLACK_API_TOKEN)


def event_handler(event, context):
    logging.info("Event handler: event=%r -- context=%r", event, context)
    event_body = event["body"]
    if not event_body:
        return _make_response("Empty body", 400)

    event_json = json.loads(event_body)
    if event_json.get("object") == "certificate_transparency":
        event_entries = event_json.get("entry") or []
        for event_entry in event_entries:
            event_changes = event_entry.get("changes") or []
            for change in event_changes:
                if change.get("field") == "certificate":
                    is_handled = _handle_cert_event(event_entry)
                    message = (
                        "Success: received valid cert transparency event"
                        if is_handled
                        else "No cert found"
                    )
                    return _make_response(message)

    return _make_response("Invalid cert transparency event: no action taken")


def verify_handler(event, context):
    logging.info("Verify handler: event=%r -- context=%r", event, context)
    query_params = event["queryStringParameters"]
    if query_params is None:
        return _make_response("No query parameters provided", 400)
    hub_challenge = query_params.get("hub.challenge", "")
    if not hub_challenge:
        return _make_response("Missing challenge in query parameters", 400)
    return _make_response(hub_challenge)


def _make_response(content: str, status_code: int = 200) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "text/plain"},
        "body": content,
    }


def _handle_cert_event(event_entry: Dict) -> bool:
    logger.info("Received valid cert transparency event")
    log_entry = _find_log_entry(event_entry["id"])
    if log_entry:
        domains = log_entry["domains"]
        authority_name = _clean_name(log_entry["issuer_name"])
        message_content = (
            f"New certificate issued for `{domains}` by `{authority_name}`"
        )
        slack_client.chat_postMessage(
            channel=config.SLACK_CHANNEL, text=message_content
        )
        return True
    return False


def _clean_name(issuer_name: str) -> str:
    name_parts = (p.split("=", 1) for p in issuer_name.split("/") if p)
    issuer_infos = dict(name_parts)
    return issuer_infos["CN"]


def _find_log_entry(object_id: str) -> Dict[str, Any]:
    fb_client = fb.Client()
    for domain in config.DOMAINS_LIST:
        logs_entries = fb_client.search_logs(domain)
        for log_entry in logs_entries:
            if log_entry["id"] == object_id:
                return log_entry
