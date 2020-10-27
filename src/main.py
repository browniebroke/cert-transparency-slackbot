import json
import logging
from typing import Any, Dict

from slack import WebClient

from . import config, fb

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.INFO)

slack_client = WebClient(token=config.SLACK_API_TOKEN)


def event_handler(event, context):
    logging.info("Event handler: event=%r -- context=%r", event, context)
    event_body = event["body"]
    if not event_body:
        logging.error("Body was empty")
        return _make_response("Empty body", 400)

    event_json = json.loads(event_body)
    if event_json.get("object") == "certificate_transparency":
        event_entries = event_json.get("entry") or []
        logging.info("Handling certificate_transparency: %r", event_entries)
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

    logging.info("Missing condition in cert transparency event")
    return _make_response("Invalid cert transparency event: no action taken", 400)


def verify_handler(event, context):
    logging.info("Verify handler: event=%r -- context=%r", event, context)
    query_params = event["queryStringParameters"]
    if query_params is None:
        logging.error("No query parameters provided")
        return _make_response("No query parameters provided", 400)
    hub_challenge = query_params.get("hub.challenge", "")
    if not hub_challenge:
        logging.error("Missing challenge in query parameters: %s", query_params)
        return _make_response("Missing challenge in query parameters", 400)
    return _make_response(hub_challenge)


def _make_response(content: str, status_code: int = 200) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "text/plain"},
        "body": content,
    }


def _handle_cert_event(event_entry: Dict) -> bool:
    logger.info("Received valid cert transparency event: %r", event_entry)
    log_entry = _find_log_entry(event_entry["id"])
    if log_entry:
        domains = log_entry["domains"]
        authority_name = _clean_name(log_entry["issuer_name"])
        message_content = (
            f"New certificate issued for `{domains}` by `{authority_name}`"
        )
        logger.info("Posting message to Slack: %s", message_content)
        slack_client.chat_postMessage(
            channel=config.SLACK_CHANNEL, text=message_content
        )
        return True
    logger.info("Not matching log entry found, no message sent")
    return False


def _clean_name(issuer_name: str) -> str:
    name_parts = (p.split("=", 1) for p in issuer_name.split("/") if p)
    issuer_infos = dict(name_parts)
    return issuer_infos["CN"]


def _find_log_entry(object_id: str) -> Dict[str, Any]:
    fb_client = fb.Client()
    logger.info("Searching log entry with ID: %s", object_id)
    for domain in config.DOMAINS_LIST:
        logger.info("Checking domain: %s", domain)
        log_entries = fb_client.search_logs(domain)
        for log_entry in log_entries:
            if log_entry["id"] == object_id:
                logger.info("Found: %s", log_entry)
                return log_entry
        logger.info("Nothing found...")
