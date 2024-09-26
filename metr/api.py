import json
from datetime import datetime
from decimal import Decimal

from aws_lambda_typing.context import Context
from aws_lambda_typing.events import APIGatewayProxyEventV2
from aws_lambda_typing.responses import APIGatewayProxyResponseV2
from pydantic import ValidationError
from sqlalchemy.orm.exc import NoResultFound

from metr.database import Session
from metr.models import Meter, MeterInput, MeterInputPatch, MeterInputQueryParams


def get_meters(
    event: APIGatewayProxyEventV2, context: Context
) -> APIGatewayProxyResponseV2:
    header = {"content-type": "application/json"}

    try:
        session = Session()
        query_params = event.get("queryStringParameters", {})

        # Fetch limit & offset if exists unless set to default
        limit = int(query_params.get("limit", 10))
        offset = int(query_params.get("offset", 0))

        # query the Meter table
        query = session.query(Meter)

        converted_query_params = convert_query_params(query_params)

        query_data = MeterInputQueryParams(**converted_query_params)

        query_data_dict = query_data.model_dump(exclude_unset=True)

        for key, value in query_data_dict.items():
            if hasattr(Meter, key):
                column_attr = getattr(Meter, key)

                # Debugging to ensure correct attribute is fetched
                print(
                    f"Processing key: {key}, value: {value}, column_attr: {column_attr}"
                )

                query = query.filter(column_attr == value)

        # Geting total number of records before applying limit/offset
        total_count = query.count()

        # applying pagination(limit and offset) to query
        query = query.offset(offset).limit(limit)

        # Fetch all meters from the database
        rows = query.all()

        # Converting each Meter object to a dictionary using the `to_dict()` method
        meters = [row.to_dict() for row in rows]

        # Generating next page link if there are more results
        next_offset = offset + limit
        next_link = None
        if next_offset < total_count:
            next_link = f"/meters?limit={limit}&offset={next_offset}"
        response_body = {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "meters": meters,
            "next_link": next_link,
        }

        # Serializing the list of meters to JSON
        json_data = json.dumps(response_body)

        # Returning the list of meters with a 200 OK status
        return APIGatewayProxyResponseV2(statusCode=200, headers=header, body=json_data)

    except ValidationError as ve:
        return APIGatewayProxyResponseV2(
            statusCode=400,
            headers=header,
            body=json.dumps({"error": f"Invalid query parameters: {str(ve)}"}),
        )

    # Return a 500 response in case of a database error
    except Exception as e:
        error_message = {"error": str(e)}
        return APIGatewayProxyResponseV2(
            statusCode=500, headers=header, body=json.dumps(error_message)
        )

    # Closing session properly
    finally:
        session.close()


def post_meters(
    event: APIGatewayProxyEventV2, context: Context
) -> APIGatewayProxyResponseV2:
    session = Session()
    header = {"content-type": "application/json"}

    try:
        # Parse and validate the request body
        body = json.loads(event.get("body", ""))

        # Validate input using pydantic
        MeterInput(**body)

        meter = Meter(
            meter_id=body["meter_id"],
            external_reference=body["external_reference"],
            supply_start_date=datetime.strptime(body["supply_start_date"], "%Y-%m-%d"),
            supply_end_date=(
                datetime.strptime(body["supply_end_date"], "%Y-%m-%d")
                if body.get("supply_end_date")
                else None
            ),
            enabled=body["enabled"],
            annual_quantity=body["annual_quantity"],
        )

        # Check for duplicate meter ID or external reference
        if session.query(Meter).filter_by(meter_id=meter.meter_id).first():
            return APIGatewayProxyResponseV2(
                statusCode=409,
                headers=header,
                body=json.dumps({"error": "Duplicate meter ID"}),
            )

        if (
            session.query(Meter)
            .filter_by(external_reference=meter.external_reference)
            .first()
        ):
            return APIGatewayProxyResponseV2(
                statusCode=409,
                headers=header,
                body=json.dumps({"error": "Duplicate external reference"}),
            )

        # Add the new meter to the database
        session.add(meter)
        session.commit()

        return APIGatewayProxyResponseV2(
            statusCode=201,
            headers=header,
            body=json.dumps(
                {
                    "message": "Meter Details added successfully",
                    "meter_id": meter.meter_id,
                }
            ),
        )

    # Raise exception if unable to decode event body
    except json.JSONDecodeError:
        return APIGatewayProxyResponseV2(
            statusCode=400,
            headers=header,
            body=json.dumps({"error": "Invalid JSON format"}),
        )

    # Raise exception if input is not validated properly,
    # or when input has incorrect data types or if any required field is missing
    except ValidationError as e:
        return APIGatewayProxyResponseV2(
            statusCode=400,
            headers=header,
            body=json.dumps({"error": "Validation error", "details": e.errors()}),
        )

    # Returning error in case of any exception and also rolling back the transaction
    except Exception as e:
        session.rollback()
        error_message = {"error": str(e)}
        return APIGatewayProxyResponseV2(
            statusCode=500, headers=header, body=json.dumps(error_message)
        )

    finally:
        session.close()


def get_meter(
    event: APIGatewayProxyEventV2, context: Context
) -> APIGatewayProxyResponseV2:
    session = Session()
    header = {"content-type": "application/json"}

    try:
        meter_id = event["pathParameters"].get("meter_id")
        # Query the meter by ID
        row = session.query(Meter).filter_by(meter_id=meter_id).one()
        json_data = json.dumps(row.to_dict())

        # Return 200 OK with the meter data
        return APIGatewayProxyResponseV2(statusCode=200, headers=header, body=json_data)

    # Return 404(Not Found), if the meter is not found
    except NoResultFound:
        return APIGatewayProxyResponseV2(
            statusCode=404,
            headers=header,
            body=json.dumps({"error": "Meter not found"}),
        )

    # Return 500 for any database-related errors
    except Exception as e:
        return APIGatewayProxyResponseV2(
            statusCode=500,
            headers=header,
            body=json.dumps({"error": "Database error", "details": str(e)}),
        )

    finally:
        session.close()


def put_meter(
    event: APIGatewayProxyEventV2, context: Context
) -> APIGatewayProxyResponseV2:
    session = Session()
    header = {"content-type": "application/json"}

    try:
        # Parse and validate the request body
        body = json.loads(event.get("body", ""))

        # Validate body using Pydantic
        MeterInput(**body)

        meter = Meter(
            meter_id=body["meter_id"],
            external_reference=body["external_reference"],
            supply_start_date=datetime.strptime(body["supply_start_date"], "%Y-%m-%d"),
            supply_end_date=(
                datetime.strptime(body["supply_end_date"], "%Y-%m-%d")
                if body.get("supply_end_date")
                else None
            ),
            enabled=body["enabled"],
            annual_quantity=body["annual_quantity"],
        )

        # Try to find the existing meter in the database
        existing_meter = (
            session.query(Meter).filter_by(meter_id=meter.meter_id).one_or_none()
        )

        # Check if meter exists or not
        if not existing_meter:
            return APIGatewayProxyResponseV2(
                statusCode=404,
                headers=header,
                body=json.dumps(
                    {"message": f"Could not find the meter with ID: {meter.meter_id}"}
                ),
            )

        # update and commit the changes
        session.merge(meter)
        session.commit()

        return APIGatewayProxyResponseV2(
            statusCode=200,
            headers=header,
            body=json.dumps(
                {"message": "Meter updated successfully", "meter_id": meter.meter_id}
            ),
        )

    # Raise exception if unable to decode event body
    except json.JSONDecodeError:
        return APIGatewayProxyResponseV2(
            statusCode=400,
            headers=header,
            body=json.dumps({"error": "Invalid JSON format"}),
        )

    # Raise exception if input is not validated properly,
    # or when input has incorrect data types or if any required field is missing
    except ValidationError as e:
        return APIGatewayProxyResponseV2(
            statusCode=400,
            headers=header,
            body=json.dumps({"error": "Validation error", "details": e.errors()}),
        )

    # Returning error in case of any exception and also rolling back the transaction
    except Exception as e:
        session.rollback()
        error_message = {"error": str(e)}
        return APIGatewayProxyResponseV2(
            statusCode=500, headers=header, body=json.dumps(error_message)
        )

    finally:
        session.close()


def delete_meter(
    event: APIGatewayProxyEventV2, context: Context
) -> APIGatewayProxyResponseV2:
    session = Session()
    header = {"content-type": "application/json"}
    meter_id = event["pathParameters"].get("meter_id")

    try:
        # Query the meter by ID
        row = session.query(Meter).filter_by(meter_id=meter_id).one_or_none()

        # Returning 204(not found), if meter details not found by given ID
        if not row:
            return APIGatewayProxyResponseV2(
                statusCode=204,
                headers=header,
                body=json.dumps(
                    {"message": f"Could not find the meter with ID: {meter_id}"}
                ),
            )

        # Deleting the row if meter id is found
        session.delete(row)
        session.commit()
        return APIGatewayProxyResponseV2(
            statusCode=200,
            headers=header,
            body=json.dumps(
                {"message": "Meter with {meter_id} ID deleted successfully"}
            ),
        )

    # Returning error in case of any exception and also rolling back the transaction
    except Exception as er:
        session.rollback()
        error_message = {"error": str(er)}
        return APIGatewayProxyResponseV2(
            statusCode=500, headers=header, body=json.dumps(error_message)
        )

    finally:
        session.close()


# Patch meter details
def patch_meter(
    event: APIGatewayProxyEventV2, context: Context
) -> APIGatewayProxyResponseV2:
    session = Session()
    header = {"content-type": "application/json"}

    try:
        meter_id = event["pathParameters"].get("meter_id")

        # Parse and validate the request body
        body = json.loads(event.get("body", ""))

        meter_input = MeterInputPatch(**body)

        # Find the existing meter
        existing_meter = session.query(Meter).filter_by(meter_id=meter_id).one_or_none()

        # Check if meter exists or not
        if not existing_meter:
            return APIGatewayProxyResponseV2(
                statusCode=404,
                headers=header,
                body=json.dumps(
                    {"message": f"Could not find the meter with ID: {meter_id}"}
                ),
            )

        # Update the fields provided in the request body
        meter_data = meter_input.model_dump(exclude_unset=True)

        for key, value in meter_data.items():
            setattr(existing_meter, key, value)

        # Commit the changes
        session.merge(existing_meter)
        session.commit()

        return APIGatewayProxyResponseV2(
            statusCode=200,
            headers=header,
            body=json.dumps(
                {"message": "Meter updated successfully", "meter_id": meter_id}
            ),
        )

    # Raise exception if unable to decode event body
    except json.JSONDecodeError as e:
        return APIGatewayProxyResponseV2(
            statusCode=400,
            headers=header,
            body=json.dumps({"error": f"Invalid JSON format: {e}"}),
        )

    except ValidationError as ve:
        return APIGatewayProxyResponseV2(
            statusCode=400,
            headers=header,
            body=json.dumps({"error": f"Invalid data: {str(ve)}"}),
        )

    except Exception as e:
        session.rollback()
        error_message = {"error": str(e)}
        return APIGatewayProxyResponseV2(
            statusCode=500, headers=header, body=json.dumps(error_message)
        )

    finally:
        session.close()


def convert_query_params(params):
    converted = {}
    if "supply_start_date" in params:
        converted["supply_start_date"] = datetime.strptime(
            params["supply_start_date"], "%Y-%m-%d"
        ).date()
    if "supply_end_date" in params:
        converted["supply_end_date"] = datetime.strptime(
            params["supply_end_date"], "%Y-%m-%d"
        ).date()
    if "enabled" in params:
        converted["enabled"] = params["enabled"].lower() == "true"
    if "annual_quantity" in params:
        converted["annual_quantity"] = Decimal(params["annual_quantity"])

    # Copying any other parameters as strings
    for key, value in params.items():
        if key not in converted:
            converted[key] = value

    return converted
