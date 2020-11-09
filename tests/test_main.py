import json

import pytest
import respx
from respx.patterns import M

from src.main import event_handler, sentry_cli, verify_handler


@pytest.fixture(autouse=True)
def mocked_config(mocker):
    mocker.patch("src.config.FACEBOOK_APP_ID", "12345")
    mocker.patch("src.config.FACEBOOK_APP_SECRET", "abcd")
    mocker.patch("src.config.SLACK_API_TOKEN", "ijkl")
    mocker.patch("src.config.SLACK_CHANNEL", "#general")
    mocker.patch("src.config.DOMAINS_LIST", ["example.com"])
    # Deactivate Sentry in tests
    mocker.patch("src.config.SENTRY_DSN", "")
    sentry_cli.__exit__(None, None, None)
    yield mocker


@pytest.fixture
def mocked_slack(mocker):
    yield mocker.patch("src.main.slack_client.chat_postMessage")


BASE_LAMBDA_EVENT = {
    "resource": "/",
    "path": "/",
    "httpMethod": "GET",
    "headers": {},
    "multiValueHeaders": {},
    "queryStringParameters": None,
    "multiValueQueryStringParameters": None,
    "pathParameters": None,
    "stageVariables": None,
    "requestContext": {},
    "body": None,
    "isBase64Encoded": False,
}

VERIFY_EVENT = {
    **BASE_LAMBDA_EVENT,
    "httpMethod": "GET",
    "queryStringParameters": {
        "hub.challenge": "123456",
        "hub.mode": "subscribe",
        "hub.verify_token": "some-random-value",
    },
    "multiValueQueryStringParameters": {
        "hub.challenge": ["123456"],
        "hub.mode": ["subscribe"],
        "hub.verify_token": ["some-random-value"],
    },
}

NOTIFICATION_PAYLOAD = {
    "object": "certificate_transparency",
    "entry": [
        {
            "id": "98467385784",
            "time": 1603636648,
            "changes": [
                {
                    "field": "certificate",
                    "value": {
                        "certificate_pem": "",
                        "cert_hash_sha256": "65ef1234",
                    },
                }
            ],
        }
    ],
}

NOTIFICATION_EVENT = {
    **BASE_LAMBDA_EVENT,
    "httpMethod": "POST",
    "body": json.dumps(NOTIFICATION_PAYLOAD),
}

DIGICERT_CA = "/C=US/O=DigiCert Inc/OU=www.digicert.com/CN=DigiCert CA"
LETSENCRYPT_CA = "/C=US/O=Let's Encrypt/CN=Let's Encrypt Authority X3"
BASE_SEARCH_PARAMS = {
    "access_token": "12345|abcd",
    "query": "example.com",
    "fields": "domains,issuer_name",
}
SEARCH_CERT_URL = "https://graph.facebook.com/v8.0/certificates"


def test_verify():
    assert verify_handler(VERIFY_EVENT, None) == {
        "body": "123456",
        "headers": {"Content-Type": "text/plain"},
        "statusCode": 200,
    }


def test_event_empty_body():
    empty_body_event = {
        **BASE_LAMBDA_EVENT,
        "httpMethod": "POST",
    }
    assert event_handler(empty_body_event, None) == {
        "statusCode": 400,
        "headers": {"Content-Type": "text/plain"},
        "body": "Empty body",
    }


@respx.mock
def test_event_no_certificates():
    request = respx.get(SEARCH_CERT_URL, params=BASE_SEARCH_PARAMS, json={"data": []})
    assert event_handler(NOTIFICATION_EVENT, None) == {
        "body": "No cert found",
        "headers": {"Content-Type": "text/plain"},
        "statusCode": 200,
    }
    assert request.called


@respx.mock
@pytest.mark.parametrize(
    ("issuer_name", "expected_name"),
    [
        (DIGICERT_CA, "DigiCert CA"),
        (LETSENCRYPT_CA, "Let's Encrypt Authority X3"),
    ],
    ids=["digicert", "letsencrypt"],
)
def test_event_matching_result(mocked_slack, issuer_name, expected_name):
    exp_response = {
        "data": [
            {
                "domains": ["example.com"],
                "issuer_name": issuer_name,
                "id": "98467385784",
            }
        ]
    }
    request = respx.get(SEARCH_CERT_URL, params=BASE_SEARCH_PARAMS, json=exp_response)
    assert event_handler(NOTIFICATION_EVENT, None) == {
        "body": "Success: received valid cert transparency event",
        "headers": {"Content-Type": "text/plain"},
        "statusCode": 200,
    }
    assert request.called
    mocked_slack.assert_called_with(
        channel="#general",
        text=f"New certificate issued for `['example.com']` by `{expected_name}`",
    )


@respx.mock
def test_pagination(mocked_slack):
    search_route = M(method="GET") & M(url=SEARCH_CERT_URL)
    # Request for page 1: the ID we're looking for is not in it
    request_1 = respx.route(search_route & M(params__eq=BASE_SEARCH_PARAMS)).respond(
        json={
            "data": [
                {
                    "domains": ["example.com"],
                    "issuer_name": DIGICERT_CA,
                    "id": "1111",
                }
            ],
            "paging": {
                "cursors": {"before": "cursor-1", "after": "cursor-2"},
                "next": "https://graph.facebook.com/v8.0/certificates",
            },
        }
    )
    # Request for page 2: the one we're looking for
    request_2 = respx.route(
        search_route
        & M(
            params__eq={
                **BASE_SEARCH_PARAMS,
                "after": "cursor-2",
            }
        )
    ).respond(
        json={
            "data": [
                {
                    "domains": ["example.com"],
                    "issuer_name": DIGICERT_CA,
                    "id": "98467385784",
                }
            ],
            "paging": {
                "cursors": {"before": "cursor-2", "after": "cursor-3"},
                "previous": "https://graph.facebook.com/v8.0/certificates",
            },
        }
    )
    assert event_handler(NOTIFICATION_EVENT, None) == {
        "body": "Success: received valid cert transparency event",
        "headers": {"Content-Type": "text/plain"},
        "statusCode": 200,
    }
    assert request_1.called
    assert request_2.called
    mocked_slack.assert_called_with(
        channel="#general",
        text="New certificate issued for `['example.com']` by `DigiCert CA`",
    )
