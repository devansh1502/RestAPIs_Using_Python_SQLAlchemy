# METR API

---

This is a fictional project.

---

METR is a serverless RESTful API to manage utility metering data with the
following endpoints:

- `GET /meters`: Get a list of known meters.
- `POST /meters`: Create a new meter.
- `GET /meters/{meter_id}`: Get details of a single meter.
- `PUT /meters/{meter_id}`: Update (replace) a meter.
- `DELETE /meters/{meter_id}`: Delete a meter.

It aims to be as friendly as possible to integrators by closely following
industry standards and being self-describing and explorable.

## Data Model

A meter has the following fields:

- `meter_id: integer`: Unique identifier for a meter.
- `external_reference: string`: Unique identifier as used by the integrators
  system.
- `supply_start_date: date`: The date this meter started or will start providing
  data.
- `supply_end_date: optional[date]`: The date this meter stopped or will stop
  providing data. Might be empty if not known.
- `enabled: boolean`: Whether this meter is currently active.
- `annual_quantity: float`: Best guess or average annual quantity this meter
  measured or will measure.
