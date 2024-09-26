import json

import pytest

from metr import api
from tests.factories import generate_api_gateway_proxy_event_v2


@pytest.mark.parametrize(
    "body_change",
    [
        {"meter_id": "StringABC"},
        {"enabled": 100},
        {"supply_start_date": "StringABC"},
        {"annual_quantity": "NaN"},
    ],
)
def test_post_meter_invalid_body(body_change, fresh_db, lambda_context):
    base_body = {
        "meter_id": 1,
        "external_reference": "123XYZ",
        "supply_start_date": "2021-01-01",
        "supply_end_date": None,
        "enabled": True,
        "annual_quantity": 123.45,
    }
    base_body.update(body_change)

    event = generate_api_gateway_proxy_event_v2(
        "POST", "/meters", body=json.dumps(base_body)
    )
    resp = api.post_meters(event, lambda_context)

    assert resp["statusCode"] == 400
    assert "application/json" in resp["headers"]["content-type"]
    assert json.loads(resp["body"]).get("error") == "Validation error"


def test_put_meter_invalid_body(lambda_context):
    meter_id = 999

    event = generate_api_gateway_proxy_event_v2(
        "PUT",
        f"/meters/{meter_id}",
        body=json.dumps(
            {
                "meter_id": meter_id,
                "external_reference": "123XYZ",
                "supply_start_date": "2021-01-01",
                "supply_end_date": None,
                "enabled": 100,  # Invalid Type, Should be boolean
                "annual_quantity": 123.45,
            }
        ),
    )
    resp = api.put_meter(event, lambda_context)
    assert resp["statusCode"] == 400
    assert "application/json" in resp["headers"]["content-type"]
    assert json.loads(resp["body"])


def test_post_meter_duplicate_id(db_meters, lambda_context):
    event = generate_api_gateway_proxy_event_v2(
        "POST",
        "/meters",
        body=json.dumps(
            {
                "meter_id": db_meters[0].meter_id,
                "external_reference": "123XYZ",
                "supply_start_date": "2021-01-01",
                "supply_end_date": None,
                "enabled": True,
                "annual_quantity": 123.45,
            }
        ),
    )
    resp = api.post_meters(event, lambda_context)

    assert resp["statusCode"] == 409
    assert "application/json" in resp["headers"]["content-type"]
    assert json.loads(resp["body"]).get("error") == "Duplicate meter ID"


def test_post_meter_duplicate_ref(db_meters, lambda_context):
    event = generate_api_gateway_proxy_event_v2(
        "POST",
        "/meters",
        body=json.dumps(
            {
                "meter_id": 999,
                "external_reference": db_meters[0].external_reference,
                "supply_start_date": "2021-01-01",
                "supply_end_date": None,
                "enabled": True,
                "annual_quantity": 123.45,
            }
        ),
    )
    resp = api.post_meters(event, lambda_context)

    assert resp["statusCode"] == 409
    assert "application/json" in resp["headers"]["content-type"]
    assert json.loads(resp["body"]).get("error") == "Duplicate external reference"


# checking if the input json is valid or not
def test_post_meter_invalid_JSON_Input(lambda_context):
    event = generate_api_gateway_proxy_event_v2(
        "POST",
        "/meters",
    )
    resp = api.post_meters(event, lambda_context)

    assert resp["statusCode"] == 400
    assert "application/json" in resp["headers"]["content-type"]
    assert json.loads(resp["body"]).get("error") == "Invalid JSON format"


def test_put_meter_invalid_JSON_Input(db_meters, lambda_context):
    meter_id = db_meters[0].meter_id
    event = generate_api_gateway_proxy_event_v2(
        "PUT",
        f"/meters/{meter_id}",
        {"meter_id": str(meter_id)},
    )
    resp = api.put_meter(event, lambda_context)

    assert resp["statusCode"] == 400
    assert "application/json" in resp["headers"]["content-type"]
    assert json.loads(resp["body"])


def test_patch_meter_invalid_JSON_Input(db_meters, lambda_context):
    meter_id = db_meters[0].meter_id
    event = generate_api_gateway_proxy_event_v2(
        "patch",
        f"/meters/{meter_id}",
        {"meter_id": str(meter_id)},
    )
    resp = api.patch_meter(event, lambda_context)

    assert resp["statusCode"] == 400
    assert "application/json" in resp["headers"]["content-type"]
    assert json.loads(resp["body"])
