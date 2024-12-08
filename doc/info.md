# REST Server API Documentation

This server provides REST endpoints for managing users, devices, locations, and consumption data. All endpoints return JSON responses with pagination support and schema validation.

## Base URL
```
http://localhost:3000
```

## Schema Management

### Schema Endpoints
- **GET /schemas** - List all available schemas
- **GET /schemas/{resource_name}** - Get schema for specific resource
- **PUT /schemas/{resource_name}** - Update schema for specific resource

### Example Requests
```bash
# List all schemas
curl http://localhost:3000/schemas

# Get users schema
curl http://localhost:3000/schemas/users

# Update users schema
curl -X PUT http://localhost:3000/schemas/users \
  -H "Content-Type: application/json" \
  -d '{
    "type": "object",
    "properties": {
      "name": {"type": "string", "minLength": 1},
      "email": {"type": "string", "format": "email"}
    },
    "required": ["name", "email"]
  }'
```

> **Note:** When updating a schema, ensure it is a valid JSON Schema. The new schema will be used for validating all subsequent requests for that resource.

## Pagination

### Query Parameters
- **page**: Page number (default: 1)
- **per_page**: Items per page (default: 10, max: 100)

### Example Request
```bash
# Get page 2 with 5 items per page
curl http://localhost:3000/users?page=2&per_page=5
```

### Response Format
All list endpoints return paginated responses with the following structure:

```json
{
  "data": [
    // Array of items for current page
  ],
  "metadata": {
    "total_items": 50,      // Total number of items
    "total_pages": 5,       // Total number of pages
    "current_page": 2,      // Current page number
    "per_page": 10,         // Items per page
    "first_page": "http://localhost:3000/users?page=1&per_page=10",
    "last_page": "http://localhost:3000/users?page=5&per_page=10",
    "next_page": "http://localhost:3000/users?page=3&per_page=10",
    "prev_page": "http://localhost:3000/users?page=1&per_page=10"
  }
}
```

> **Note:** The metadata includes navigation URLs for first, last, next, and previous pages. URLs will be null if the page does not exist.

## Available Resources
- Users (/users)
- Devices (/devices)
- Locations (/locations)
- Consumption (/consumption)

## Example Requests

### GET List All Resources
Retrieve all items for a resource with pagination support.

```bash
# Get all users (first page, default 10 items)
curl http://localhost:3000/users

# Get second page of devices with 5 items per page
curl http://localhost:3000/devices?page=2&per_page=5

# Get all locations with maximum items per page
curl http://localhost:3000/locations?per_page=100
```

### GET Single Item
Retrieve a specific item by ID.

```bash
# Get user with ID 1
curl http://localhost:3000/users/1

# Get device with ID 2
curl http://localhost:3000/devices/2
```

### POST Create New Item
Create a new resource item. The request must conform to the resource schema.

```bash
# Create new user
curl -X POST http://localhost:3000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Create new device
curl -X POST http://localhost:3000/devices \
  -H "Content-Type: application/json" \
  -d '{"name": "Smart Thermostat", "type": "temperature", "location_id": 1}'
```

### PUT Update Item
Update an existing item by ID. The request must conform to the resource schema.

```bash
# Update user with ID 1
curl -X PUT http://localhost:3000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "John Smith", "email": "john.smith@example.com"}'

# Update device with ID 2
curl -X PUT http://localhost:3000/devices/2 \
  -H "Content-Type: application/json" \
  -d '{"name": "Smart Thermostat v2", "type": "temperature", "location_id": 1}'
```

### DELETE Item
Delete an item by ID.

```bash
# Delete user with ID 1
curl -X DELETE http://localhost:3000/users/1

# Delete device with ID 2
curl -X DELETE http://localhost:3000/devices/2
```

## Response Codes
- **200 OK** - Request successful
- **201 Created** - Resource created successfully
- **400 Bad Request** - Invalid request (e.g., missing required fields or schema validation failed)
- **404 Not Found** - Resource or schema not found
