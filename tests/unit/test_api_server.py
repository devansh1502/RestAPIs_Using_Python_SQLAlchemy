import json
from unittest.mock import patch

from metr import api
from tests.factories import generate_api_gateway_proxy_event_v2


def test_get_meters_exception_handling(lambda_context):
    event = generate_api_gateway_proxy_event_v2("GET", "/meters")

    # Mocking the Session object and forcing it to raise an exception
    with patch("metr.api.Session", return_value=MySession()):
        resp = api.get_meters(event, lambda_context)
        assert resp["statusCode"] == 500
        assert "application/json" in resp["headers"]["content-type"]
        assert json.loads(resp["body"])["error"] == "Server error"


def test_post_meters_exception_handling(lambda_context):
    event = {
        "body": json.dumps(
            {
                "meter_id": 1,
                "external_reference": "123XYZ",
                "supply_start_date": "2021-01-01",
                "supply_end_date": None,
                "enabled": True,
                "annual_quantity": 123.45,
            }
        )
    }

    # Mocking the Session object and forcing it to raise an exception
    with patch("metr.api.Session", return_value=MySession()):
        resp = api.post_meters(event, lambda_context)
        assert resp["statusCode"] == 500
        assert "application/json" in resp["headers"]["content-type"]
        assert json.loads(resp["body"])["error"] == "Server error"


def test_get_meter_exception_handling(db_meters, lambda_context):
    meter_id = db_meters[0].meter_id

    event = generate_api_gateway_proxy_event_v2(
        "GET", f"/meters/{meter_id}", {"meter_id": str(meter_id)}
    )

    # Mocking the Session object and forcing it to raise an exception
    with patch("metr.api.Session", return_value=MySession()):
        resp = api.get_meter(event, lambda_context)
        assert resp["statusCode"] == 500
        assert "application/json" in resp["headers"]["content-type"]
        assert json.loads(resp["body"])["error"] == "Database error"


def test_put_meter_exception_handling(lambda_context):
    event = {
        "body": json.dumps(
            {
                "meter_id": 1,
                "external_reference": "123XYZ",
                "supply_start_date": "2021-01-01",
                "supply_end_date": None,
                "enabled": True,
                "annual_quantity": 123.45,
            }
        )
    }

    # Mocking the Session object and forcing it to raise an exception
    with patch("metr.api.Session", return_value=MySession()):
        resp = api.put_meter(event, lambda_context)
        assert resp["statusCode"] == 500
        assert "application/json" in resp["headers"]["content-type"]
        assert json.loads(resp["body"])["error"] == "Server error"


def test_delete_meter_exception_handling(db_meters, lambda_context):
    meter_id = db_meters[1].meter_id

    event = generate_api_gateway_proxy_event_v2(
        "DELETE", f"/meters/{meter_id}", {"meter_id": str(meter_id)}
    )

    # Mocking the Session object and forcing it to raise an exception
    with patch("metr.api.Session", return_value=MySession()):
        resp = api.delete_meter(event, lambda_context)
        assert resp["statusCode"] == 500
        assert "application/json" in resp["headers"]["content-type"]
        assert json.loads(resp["body"])["error"] == "Server error"


def test_patch_meter_exception_handling(db_meters, lambda_context):
    meter_id = db_meters[1].meter_id

    event = generate_api_gateway_proxy_event_v2(
        "PATCH",
        f"/meters/{meter_id}",
        {"meter_id": str(meter_id)},
        body=json.dumps({"external_reference": "456ABC"}),
    )

    # Mocking the Session object and forcing it to raise an exception
    with patch("metr.api.Session", return_value=MySession()):
        resp = api.patch_meter(event, lambda_context)
        assert resp["statusCode"] == 500
        assert "application/json" in resp["headers"]["content-type"]
        assert json.loads(resp["body"])["error"] == "Server error"


# Creating Empty Session and let it fail for exception
class MySession:
    def query(self, model):
        return self

    def filter_by(self, **kwargs):
        return self

    def count(self):
        raise Exception("Server error")

    def first(self):
        raise Exception("Server error")

    def one(self):
        raise Exception("Server error")

    def one_or_none(self):
        raise Exception("Server error")

    def all(self):
        raise Exception("Server error")

    def rollback(self):
        return

    def close(self):
        return
