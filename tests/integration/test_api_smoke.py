import json

from metr import api
from tests.factories import generate_api_gateway_proxy_event_v2


def test_get_meters_smoke(db_meters, lambda_context):
    event = generate_api_gateway_proxy_event_v2("GET", "/meters")
    resp = api.get_meters(event, lambda_context)

    assert resp["statusCode"] == 200
    assert "application/json" in resp["headers"]["content-type"]
    assert json.loads(resp["body"])


def test_get_meters_smoke_filter(db_meters, lambda_context):
    queryParams = "enabled=false"
    event = generate_api_gateway_proxy_event_v2(
        "GET", "/meters", query_string=queryParams
    )
    resp = api.get_meters(event, lambda_context)

    assert resp["statusCode"] == 200
    assert "application/json" in resp["headers"]["content-type"]
    body = json.loads(resp["body"])
    assert len(body["meters"]) == 10
    assert all(meter["enabled"] is False for meter in body["meters"])


def test_get_meters_smoke_filter_and_pagination(db_meters, lambda_context):
    queryParams = "enabled=true&limit=9"
    event = generate_api_gateway_proxy_event_v2(
        "GET", "/meters", query_string=queryParams
    )
    resp = api.get_meters(event, lambda_context)

    assert resp["statusCode"] == 200
    assert "application/json" in resp["headers"]["content-type"]
    body = json.loads(resp["body"])
    assert len(body["meters"]) == 9
    assert all(meter["enabled"] is True for meter in body["meters"])


def test_get_meters_smoke_pagination(db_meters, lambda_context):
    queryParams = "limit=5&offset=5"
    event = generate_api_gateway_proxy_event_v2(
        "GET", "/meters", query_string=queryParams
    )
    resp = api.get_meters(event, lambda_context)

    assert resp["statusCode"] == 200
    assert "application/json" in resp["headers"]["content-type"]
    body = json.loads(resp["body"])
    assert len(body["meters"]) == 5

def test_get_meters_smoke_pagination_next_link_not_available(db_meters, lambda_context):
    queryParams = "limit=5&offset=99"
    event = generate_api_gateway_proxy_event_v2(
        "GET", "/meters", query_string=queryParams
    )
    resp = api.get_meters(event, lambda_context)

    assert resp["statusCode"] == 200
    assert "application/json" in resp["headers"]["content-type"]
    body = json.loads(resp["body"])
    assert len(body["meters"]) == 1
    assert body["next_link"] == None


def test_get_meter_smoke(db_meters, lambda_context):
    meter_id = db_meters[0].meter_id

    event = generate_api_gateway_proxy_event_v2(
        "GET", f"/meters/{meter_id}", {"meter_id": str(meter_id)}
    )
    resp = api.get_meter(event, lambda_context)

    assert resp["statusCode"] == 200
    assert "application/json" in resp["headers"]["content-type"]
    assert json.loads(resp["body"])


def test_get_meter_not_found(fresh_db, lambda_context):
    meter_id = 999
    event = generate_api_gateway_proxy_event_v2(
        "GET", f"/meters/{meter_id}", {"meter_id": str(meter_id)}
    )
    resp = api.get_meter(event, lambda_context)

    assert resp["statusCode"] == 404
    assert "application/json" in resp["headers"]["content-type"]
    assert json.loads(resp["body"]).get("error") == "Meter not found"


def test_post_meters_smoke(fresh_db, lambda_context):
    event = generate_api_gateway_proxy_event_v2(
        "POST",
        "/meters",
        body=json.dumps(
            {
                "meter_id": 1,
                "external_reference": "123XYZ",
                "supply_start_date": "2021-01-01",
                "supply_end_date": None,
                "enabled": True,
                "annual_quantity": 123.45,
            }
        ),
    )
    resp = api.post_meters(event, lambda_context)

    assert resp["statusCode"] == 201
    assert "application/json" in resp["headers"]["content-type"]
    body = json.loads(resp["body"])
    assert body.get("message") == "Meter Details added successfully"
    assert body.get("meter_id") == 1


def test_put_meter_smoke(db_meters, lambda_context):
    meter_id = db_meters[0].meter_id

    event = generate_api_gateway_proxy_event_v2(
        "PUT",
        f"/meters/{meter_id}",
        body=json.dumps(
            {
                "meter_id": meter_id,
                "external_reference": "123XYZ",
                "supply_start_date": "2021-01-01",
                "supply_end_date": None,
                "enabled": True,
                "annual_quantity": 123.45,
            }
        ),
    )
    resp = api.put_meter(event, lambda_context)

    assert resp["statusCode"] == 200
    assert "application/json" in resp["headers"]["content-type"]
    body = json.loads(resp["body"])
    assert body.get("message") == "Meter updated successfully"
    assert body.get("meter_id") == meter_id


def test_put_meter_not_found(fresh_db, lambda_context):
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
                "enabled": True,
                "annual_quantity": 123.45,
            }
        ),
    )
    resp = api.put_meter(event, lambda_context)

    assert resp["statusCode"] == 404
    assert "application/json" in resp["headers"]["content-type"]
    assert (
        json.loads(resp["body"]).get("message")
        == f"Could not find the meter with ID: {meter_id}"
    )


def test_delete_meter_smoke(db_meters, lambda_context):
    meter_id = db_meters[-1].meter_id

    event = generate_api_gateway_proxy_event_v2(
        "DELETE", f"/meters/{meter_id}", {"meter_id": str(meter_id)}
    )
    resp = api.delete_meter(event, lambda_context)

    assert resp["statusCode"] == 200
    assert "application/json" in resp["headers"]["content-type"]
    body = json.loads(resp["body"])
    assert body.get("message") == "Meter with {meter_id} ID deleted successfully"


def test_delete_meter_not_found(fresh_db, lambda_context):
    meter_id = 999

    event = generate_api_gateway_proxy_event_v2(
        "DELETE", f"/meters/{meter_id}", {"meter_id": str(meter_id)}
    )
    resp = api.delete_meter(event, lambda_context)

    assert resp["statusCode"] == 204
    assert "application/json" in resp["headers"]["content-type"]
    body = json.loads(resp["body"])
    assert body.get("message") == f"Could not find the meter with ID: {meter_id}"


# Patch Meter test cases
def test_patch_meter_update_external_reference(db_meters, lambda_context):
    meter_id = db_meters[0].meter_id

    event = generate_api_gateway_proxy_event_v2(
        "PATCH",
        f"/meters/{meter_id}",
        {"meter_id": str(meter_id)},
        body=json.dumps({"external_reference": "456ABC"}),
    )

    resp = api.patch_meter(event, lambda_context)

    assert resp["statusCode"] == 200
    assert "application/json" in resp["headers"]["content-type"]
    body = json.loads(resp["body"])
    assert body.get("message") == "Meter updated successfully"
    assert body.get("meter_id") == str(meter_id)


def test_patch_meter_update_multiple_fields(db_meters, lambda_context):
    meter_id = db_meters[-1].meter_id

    event = generate_api_gateway_proxy_event_v2(
        "PATCH",
        f"/meters/{meter_id}",
        {"meter_id": str(meter_id)},
        body=json.dumps(
            {
                "external_reference": "456ABC",
                "supply_end_date": None,
                "enabled": False,
                "annual_quantity": 200.0,
            }
        ),
    )

    resp = api.patch_meter(event, lambda_context)

    assert resp["statusCode"] == 200
    assert "application/json" in resp["headers"]["content-type"]
    body = json.loads(resp["body"])
    assert body.get("message") == "Meter updated successfully"
    assert body.get("meter_id") == str(meter_id)


def test_patch_meter_invalid_body(db_meters, lambda_context):
    meter_id = db_meters[0].meter_id

    # Sending invalid body (e.g., non-string external_reference)
    event = generate_api_gateway_proxy_event_v2(
        "PATCH",
        f"/meters/{meter_id}",
        {"meter_id": str(meter_id)},
        body=json.dumps({"external_reference": 123}),  # Invalid type
    )

    resp = api.patch_meter(event, lambda_context)

    assert resp["statusCode"] == 400
    assert "application/json" in resp["headers"]["content-type"]
    assert json.loads(resp["body"])


# @pytest.mark.order("last")
def test_zpatch_meter_not_found(lambda_context):
    meter_id = 1000

    event = generate_api_gateway_proxy_event_v2(
        "PATCH",
        f"/meters/{meter_id}",
        {"meter_id": str(meter_id)},
        body=json.dumps({"external_reference": "456ABC"}),
    )

    resp = api.patch_meter(event, lambda_context)

    assert resp["statusCode"] == 404
    assert "application/json" in resp["headers"]["content-type"]
    assert (
        json.loads(resp["body"]).get("message")
        == f"Could not find the meter with ID: {meter_id}"
    )
