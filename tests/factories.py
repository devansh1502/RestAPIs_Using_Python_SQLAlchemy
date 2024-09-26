import random
import string
import time
from datetime import date, timedelta
from typing import Literal, Optional
from urllib.parse import parse_qs

from aws_lambda_typing.events import APIGatewayProxyEventV2

from metr.models import Meter


def generate_meters(count: int) -> list[Meter]:
    return [
        Meter(
            meter_id=i,
            external_reference="".join(random.sample(string.printable, 10)),
            supply_start_date=date.today() + timedelta(days=i),
            supply_end_date=(
                date.today() + timedelta(days=10 * i) if random.random() < 0.5 else None
            ),
            enabled=random.random() < 0.5,
            annual_quantity=random.random() * 100_000,
        )
        for i in range(count)
    ]


def generate_api_gateway_proxy_event_v2(
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
    path: str,
    path_params: Optional[dict[str, str]] = None,
    query_string: str = "",
    body: str = "",
) -> APIGatewayProxyEventV2:
    return APIGatewayProxyEventV2(
        version="2.0",
        routeKey="$default",
        rawPath=path,
        rawQueryString=query_string,
        cookies=[],
        headers={},
        queryStringParameters={
            p: ",".join(v) for p, v in parse_qs(query_string).items()
        },
        requestContext={
            "timeEpoch": int(time.time() * 1000),
            "domainName": "metr.local",
            "http": {
                "method": method,
                "path": path,
                "protocol": "https",
                "sourceIp": "127.0.0.1",
                "userAgent": "curl/7.64.1",
            },
        },
        body=body,
        pathParameters=path_params or {},
        isBase64Encoded=False,
        stageVariables={},
    )
