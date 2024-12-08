import os
import json
from flask import Flask, request, jsonify, send_file
from http import HTTPStatus
from pathlib import Path
from typing import Dict, List, Any, Optional
from functools import partial
from jsonschema import validate, ValidationError

app = Flask(__name__)
# Enable pretty printing of JSON
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
# Enable more detailed logging
app.config['DEBUG'] = True

# Ensure directories exist
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
SCHEMA_DIR = Path("schemas")
SCHEMA_DIR.mkdir(exist_ok=True)

# Initialize default schemas if they don't exist
DEFAULT_SCHEMAS = {
    "users": {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "name": {"type": "string", "minLength": 1},
            "email": {
                "type": "string",
                "format": "email",
                "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
            }
        },
        "required": ["name", "email"],
        "additionalProperties": False
    },
    "locations": {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "name": {"type": "string", "minLength": 1},
            "address": {"type": "string", "minLength": 1}
        },
        "required": ["name", "address"],
        "additionalProperties": False
    },
    "devices": {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "name": {"type": "string", "minLength": 1},
            "type": {"type": "string", "minLength": 1},
            "location_id": {"type": "integer", "minimum": 1},
            "user_id": {"type": ["integer", "null"], "minimum": 1}
        },
        "required": ["name", "type", "location_id"],
        "additionalProperties": False
    },
    "consumption": {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "name": {"type": "string", "minLength": 1},
            "type": {"type": "string", "minLength": 1},
            "location_id": {"type": "integer", "minimum": 1},
            "user_id": {"type": ["integer", "null"], "minimum": 1}
        },
        "required": ["name", "type", "location_id"],
        "additionalProperties": False
    }
}

def init_schemas():
    """Initialize default schemas if they don't exist."""
    for name, schema in DEFAULT_SCHEMAS.items():
        schema_file = SCHEMA_DIR / f"{name}.json"
        if not schema_file.exists():
            with open(schema_file, 'w') as f:
                json.dump(schema, f, indent=2)

init_schemas()

class SchemaHandler:
    """Handler for schema operations."""
    
    @staticmethod
    def get_schema(resource_name: str) -> Optional[Dict]:
        """Get schema for a resource."""
        schema_file = SCHEMA_DIR / f"{resource_name}.json"
        if not schema_file.exists():
            return None
        with open(schema_file, 'r') as f:
            return json.load(f)

    @staticmethod
    def save_schema(resource_name: str, schema: Dict) -> None:
        """Save schema for a resource."""
        schema_file = SCHEMA_DIR / f"{resource_name}.json"
        with open(schema_file, 'w') as f:
            json.dump(schema, f, indent=2)

    @staticmethod
    def list_schemas() -> Dict[str, Dict]:
        """List all available schemas."""
        schemas = {}
        for schema_file in SCHEMA_DIR.glob("*.json"):
            with open(schema_file, 'r') as f:
                schemas[schema_file.stem] = json.load(f)
        return schemas

class JSONFileHandler:
    """Generic handler for JSON file operations."""
    
    @staticmethod
    def get_resource_files() -> Dict[str, Path]:
        """Get all JSON files in the data directory."""
        return {
            file.stem: file
            for file in DATA_DIR.glob("*.json")
        }

    @staticmethod
    def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
        """Load data from a JSON file. Create if doesn't exist."""
        if not file_path.exists():
            with open(file_path, 'w') as f:
                json.dump([], f, indent=2)
            return []
        with open(file_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def save_json_file(file_path: Path, data: List[Dict[str, Any]]) -> None:
        """Save data to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

class ResourceHandler:
    """Handler for resource-specific operations."""
    
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    
    def __init__(self, resource_name: str, file_path: Path):
        self.resource_name = resource_name
        self.file_path = file_path
        self.schema_handler = SchemaHandler()

    def validate_data(self, data: Dict[str, Any], check_required: bool = True) -> None:
        """Validate data against the schema."""
        schema = self.schema_handler.get_schema(self.resource_name)
        if not schema:
            app.logger.warning(f"No schema defined for resource: {self.resource_name}")
            return
        
        try:
            # For updates, we don't check required fields as it might be a partial update
            if not check_required:
                schema = {
                    **schema,
                    "required": []  # Don't enforce required fields for updates
                }
            validate(instance=data, schema=schema)
        except ValidationError as e:
            app.logger.error(f"Validation error: {str(e)}")
            raise ValidationError(f"Invalid {self.resource_name} data: {str(e)}")

    def get_pagination_params(self) -> Tuple[int, int]:
        """Get and validate pagination parameters from request."""
        try:
            page = max(1, int(request.args.get('page', 1)))
            per_page = min(
                self.MAX_PAGE_SIZE,
                max(1, int(request.args.get('per_page', self.DEFAULT_PAGE_SIZE)))
            )
            return page, per_page
        except ValueError:
            # If invalid values provided, return defaults
            return 1, self.DEFAULT_PAGE_SIZE

    def get_pagination_metadata(self, total_items: int, page: int, per_page: int) -> Dict[str, Any]:
        """Generate pagination metadata."""
        total_pages = ceil(total_items / per_page)
        base_url = request.base_url
        
        # Ensure page is within valid range
        page = min(max(1, page), max(1, total_pages))
        
        def get_page_url(page_num: int) -> str:
            return f"{base_url}?page={page_num}&per_page={per_page}" if page_num else None

        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page,
            "first_page": get_page_url(1),
            "last_page": get_page_url(total_pages),
            "next_page": get_page_url(page + 1) if page < total_pages else None,
            "prev_page": get_page_url(page - 1) if page > 1 else None
        }

    def get_all(self):
        """Get all items for a resource with pagination."""
        app.logger.info(f"Getting all {self.resource_name}")
        items = JSONFileHandler.load_json_file(self.file_path)
        total_items = len(items)
        
        # Get pagination parameters
        page, per_page = self.get_pagination_params()
        
        # Calculate slice indices
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Slice the items
        paginated_items = items[start_idx:end_idx]
        
        # Prepare response with metadata
        response = {
            "data": paginated_items,
            "metadata": self.get_pagination_metadata(total_items, page, per_page)
        }
        
        return jsonify(response)

    def get_one(self, item_id):
        """Get a specific item by ID."""
        app.logger.info(f"Getting {self.resource_name} with id {item_id}")
        items = JSONFileHandler.load_json_file(self.file_path)
        item = next((i for i in items if str(i.get('id')) == str(item_id)), None)
        if item is None:
            app.logger.warning(f"{self.resource_name.title()} with id {item_id} not found")
            return jsonify({'error': f'{self.resource_name.title()} not found'}), HTTPStatus.NOT_FOUND
        
        response = {
            "data": item,
            "metadata": {
                "total_items": len(items)
            }
        }
        return jsonify(response)

    def create(self):
        """Create a new item."""
        app.logger.info(f"Creating new {self.resource_name}")
        if not request.is_json:
            app.logger.error("Request Content-Type is not application/json")
            return jsonify({'error': 'Content-Type must be application/json'}), HTTPStatus.BAD_REQUEST
        
        try:
            data = request.get_json()
            # Validate the incoming data
            self.validate_data(data, check_required=True)
            
            items = JSONFileHandler.load_json_file(self.file_path)
            new_item = {
                'id': len(items) + 1,
                **data
            }
            items.append(new_item)
            JSONFileHandler.save_json_file(self.file_path, items)
            app.logger.info(f"Created {self.resource_name} with id {new_item['id']}")
            
            response = {
                "data": new_item,
                "metadata": {
                    "total_items": len(items)
                }
            }
            return jsonify(response), HTTPStatus.CREATED
            
        except ValidationError as e:
            return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
        except Exception as e:
            app.logger.error(f"Error creating {self.resource_name}: {str(e)}")
            return jsonify({'error': f'Error creating {self.resource_name}'}), HTTPStatus.INTERNAL_SERVER_ERROR

    def update(self, item_id):
        """Update an existing item."""
        app.logger.info(f"Updating {self.resource_name} with id {item_id}")
        if not request.is_json:
            app.logger.error("Request Content-Type is not application/json")
            return jsonify({'error': 'Content-Type must be application/json'}), HTTPStatus.BAD_REQUEST

        try:
            data = request.get_json()
            # Validate the incoming data, but don't check required fields for updates
            self.validate_data(data, check_required=False)
            
            items = JSONFileHandler.load_json_file(self.file_path)
            
            # Find the item to update
            item_index = next((index for index, item in enumerate(items) 
                            if str(item.get('id')) == str(item_id)), None)
            
            if item_index is None:
                app.logger.warning(f"{self.resource_name.title()} with id {item_id} not found")
                return jsonify({'error': f'{self.resource_name.title()} not found'}), HTTPStatus.NOT_FOUND

            # Update the item while preserving its ID
            updated_item = {
                'id': items[item_index]['id'],
                **data
            }
            items[item_index] = updated_item
            JSONFileHandler.save_json_file(self.file_path, items)
            
            app.logger.info(f"Updated {self.resource_name} with id {item_id}")
            response = {
                "data": updated_item,
                "metadata": {
                    "total_items": len(items)
                }
            }
            return jsonify(response)
            
        except ValidationError as e:
            return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
        except Exception as e:
            app.logger.error(f"Error updating {self.resource_name}: {str(e)}")
            return jsonify({'error': f'Error updating {self.resource_name}'}), HTTPStatus.INTERNAL_SERVER_ERROR

    def delete(self, item_id):
        """Delete an item."""
        app.logger.info(f"Deleting {self.resource_name} with id {item_id}")
        items = JSONFileHandler.load_json_file(self.file_path)
        
        # Find the item to delete
        item_index = next((index for index, item in enumerate(items) 
                          if str(item.get('id')) == str(item_id)), None)
        
        if item_index is None:
            app.logger.warning(f"{self.resource_name.title()} with id {item_id} not found")
            return jsonify({'error': f'{self.resource_name.title()} not found'}), HTTPStatus.NOT_FOUND

        # Remove the item
        deleted_item = items.pop(item_index)
        JSONFileHandler.save_json_file(self.file_path, items)
        
        app.logger.info(f"Deleted {self.resource_name} with id {item_id}")
        response = {
            "data": deleted_item,
            "metadata": {
                "total_items": len(items)
            }
        }
        return jsonify(response)

# Schema management endpoints
@app.route("/schemas", methods=['GET'])
def list_schemas():
    """List all available schemas."""
    schemas = SchemaHandler.list_schemas()
    return jsonify(schemas)

@app.route("/schemas/<resource_name>", methods=['GET'])
def get_schema(resource_name):
    """Get schema for a specific resource."""
    schema = SchemaHandler.get_schema(resource_name)
    if schema is None:
        return jsonify({'error': 'Schema not found'}), HTTPStatus.NOT_FOUND
    return jsonify(schema)

@app.route("/schemas/<resource_name>", methods=['PUT'])
def update_schema(resource_name):
    """Update schema for a specific resource."""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), HTTPStatus.BAD_REQUEST
    
    try:
        schema = request.get_json()
        # Validate that it's a valid JSON Schema
        validate({}, schema)  # Simple validation to ensure it's a valid schema
        SchemaHandler.save_schema(resource_name, schema)
        return jsonify(schema)
    except Exception as e:
        return jsonify({'error': f'Invalid schema: {str(e)}'}), HTTPStatus.BAD_REQUEST

def register_resource_routes():
    """Register routes for each JSON file in the data directory."""
    handlers = JSONFileHandler()
    resources = handlers.get_resource_files()
    app.logger.info(f"Found resources: {list(resources.keys())}")

    for resource_name, file_path in resources.items():
        handler = ResourceHandler(resource_name, file_path)
        
        # Register routes using add_url_rule
        app.add_url_rule(
            f"/{resource_name}",
            f"get_all_{resource_name}",
            handler.get_all,
            methods=['GET']
        )
        
        app.add_url_rule(
            f"/{resource_name}/<item_id>",
            f"get_one_{resource_name}",
            handler.get_one,
            methods=['GET']
        )
        
        app.add_url_rule(
            f"/{resource_name}",
            f"create_{resource_name}",
            handler.create,
            methods=['POST']
        )

        app.add_url_rule(
            f"/{resource_name}/<item_id>",
            f"update_{resource_name}",
            handler.update,
            methods=['PUT']
        )

        app.add_url_rule(
            f"/{resource_name}/<item_id>",
            f"delete_{resource_name}",
            handler.delete,
            methods=['DELETE']
        )
        
        app.logger.info(f"Registered routes for {resource_name}")

@app.route("/")
def hello_world():
    """Root endpoint showing available routes."""
    handlers = JSONFileHandler()
    resources = handlers.get_resource_files()
    endpoints = {
        resource: {
            "GET_all": f"/{resource}?page=1&per_page=10",
            "GET_one": f"/{resource}/<id>",
            "POST": f"/{resource}",
            "PUT": f"/{resource}/<id>",
            "DELETE": f"/{resource}/<id>"
        }
        for resource in resources.keys()
    }
    
    schema_endpoints = {
        "GET_all": "/schemas",
        "GET_one": "/schemas/<resource_name>",
        "PUT": "/schemas/<resource_name>"
    }
    
    response = {
        "message": "REST Server with Dynamic Routes",
        "available_endpoints": endpoints,
        "schema_endpoints": schema_endpoints,
        "documentation": "/info",
        "pagination": {
            "page": "Query parameter for page number (default: 1)",
            "per_page": f"Query parameter for items per page (default: {ResourceHandler.DEFAULT_PAGE_SIZE}, max: {ResourceHandler.MAX_PAGE_SIZE})"
        }
    }
    app.logger.info("Root endpoint accessed")
    return jsonify(response)

@app.route("/info")
def info():
    """Serve the API documentation page."""
    app.logger.info("Documentation page accessed")
    return send_file('info.html')

# Register routes for all JSON files in the data directory
register_resource_routes()

if __name__ == "__main__":
    # Enable more detailed logging
    import logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    
    print("\n=== REST Server Starting ===")
    print("Available endpoints will be shown in the response from: http://localhost:3000")
    print("API documentation available at: http://localhost:3000/info")
    print("Press Ctrl+C to stop the server")
    print("===============================\n")
    
    # Ensure we bind to all network interfaces
    host = "0.0.0.0"  # Listen on all available interfaces
    port = int(os.environ.get("PORT", 3000))
    
    print(f"Server will be accessible at:")
    print(f"- Local: http://localhost:{port}")
    print(f"- Network: http://{host}:{port}")
    print("\nStarting server...")
    
    try:
        app.run(debug=True, host=host, port=port, use_reloader=True)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\nERROR: Port {port} is already in use!")
            print("Possible solutions:")
            print("1. Stop any other running servers")
            print("2. Choose a different port using the PORT environment variable")
            print("\nTo find and stop existing servers:")
            print("ps aux | grep 'python main.py'")
            print("kill <PID>")
        else:
            print(f"\nERROR: {str(e)}")
        exit(1)
