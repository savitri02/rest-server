# REST Server with Dynamic Routes

## Available Resource Endpoints

Each resource supports the following operations:
- `GET /{resource}?page=1&per_page=10` - List all items (paginated)
- `GET /{resource}/<id>` - Get a single item
- `POST /{resource}` - Create a new item
- `PUT /{resource}/<id>` - Update an item
- `DELETE /{resource}/<id>` - Delete an item

## Schema Management Endpoints
- `GET /schemas` - List all available schemas
- `GET /schemas/<resource_name>` - Get schema for specific resource
- `PUT /schemas/<resource_name>` - Update schema for specific resource
- **NEW:** [Schema Creator](/schema-creator) - Visual tool to create schemas from JavaScript objects

## Documentation
- Detailed API documentation available at `/info`

## Pagination
- `page`: Query parameter for page number (default: 1)
- `per_page`: Query parameter for items per page (default: 10, max: 100)
