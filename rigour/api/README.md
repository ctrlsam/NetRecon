# REST API Documentation

This documentation provides an overview of the REST API endpoints available for searching and retrieving host information.
The API allows users to perform searches with advanced query syntax, retrieve counts, and get detailed host data by IP address.

## Base URL

All endpoints are accessible under the following base URL:

```
http://<host>:1234/api/v1
```

---

## Endpoints

### 1. Search Hosts

**Endpoint:**

```
GET /host/search
```

**Description:**

Search for hosts using a query syntax with optional filters and retrieve summary information through facets.

**Query Parameters:**

- `query` (string, optional): Search query with optional filters in the `filter:value` format. For example, to find servers in Germany: `location.country_code:DE`.

- `skip` (integer, optional): Number of records to skip. Default is `0`. Must be greater than or equal to `0`.

- `limit` (integer, optional): Maximum number of records to return. Default is `10`. Must be between `1` and `100`.

**Response:**

- **Status Code:** `200 OK`
- **Body:** A list of host objects matching the search criteria.

**Response Model:**

A list of `Host` objects. The structure of `Host` includes host details such as IP address, port information, and metadata.

**Example Request:**

```
GET /api/v1/host/search?query=apache%20country:DE&skip=0&limit=10
```

---

### 2. Get Hosts Count

**Endpoint:**

```
GET /host/count
```

**Description:**

Retrieve the total number of hosts that match the search query, along with any requested facet information. This endpoint does not return host details.

**Query Parameters:**

- `query` (string, optional): Search query with optional filters in the `filter:value` format. For example: `location.country_code:DE`.

- `facet` (string, optional): Comma-separated list of properties for faceted search, optionally with counts. Example: `country:100`.

**Response:**

- **Status Code:** `200 OK`
- **Body:** A JSON object containing the total count and facet information.

**Response Format:**

```json
{
  "total": <integer>,
  "facets": {
    "<property>": [
      {
        "_id": "<facet_value>",
        "count": <integer>
      },
      ...
    ],
    ...
  }
}
```

**Example Request:**

```
GET /api/v1/host/count?query=apache%20country:DE&facet=country:10
```

**Example Response:**

```json
{
  "total": 500,
  "facets": {
    "country": [
      { "_id": "DE", "count": 300 },
      { "_id": "US", "count": 100 },
      { "_id": "FR", "count": 50 }
    ]
  }
}
```

---

### 3. Get Host by IP

**Endpoint:**

```
GET /host/{ip}
```

**Description:**

Retrieve detailed host information by specifying the IP address.

**Path Parameters:**

- `ip` (string, required): The IP address of the host.

**Response:**

- **Status Code:** `200 OK`
  - **Body:** A `Host` object containing host details.
- **Status Code:** `404 Not Found`
  - **Body:** `{ "detail": "Host not found" }`
- **Status Code:** `500 Internal Server Error`
  - **Body:** `{ "detail": "Invalid host data" }`

**Example Request:**

```
GET /api/v1/host/192.168.1.1
```

---

## Models

### Host

The `Host` model represents the structure of a host object returned by the API. It includes fields such as:

- `ip` (string): The IP address of the host.
- `port` (integer): The port number.
- `data` (string): Banner data or service information.
- `timestamp` (string): The timestamp when the data was collected.
- `location` (object): Geolocation data including country, city, latitude, and longitude.
- Additional metadata fields as defined in the model.

_Note: The exact structure may vary based on the data stored in the database._
