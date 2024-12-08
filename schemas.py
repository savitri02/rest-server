"""JSON schemas for resource validation."""

# Common fields that appear in all resources
id_schema = {
    "type": "integer",
    "minimum": 1
}

name_schema = {
    "type": "string",
    "minLength": 1
}

# Schema for users
users_schema = {
    "type": "object",
    "properties": {
        "id": id_schema,
        "name": name_schema,
        "email": {
            "type": "string",
            "format": "email",
            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        }
    },
    "required": ["name", "email"],
    "additionalProperties": False
}

# Schema for locations
locations_schema = {
    "type": "object",
    "properties": {
        "id": id_schema,
        "name": name_schema,
        "address": {
            "type": "string",
            "minLength": 1
        }
    },
    "required": ["name", "address"],
    "additionalProperties": False
}

# Schema for devices
devices_schema = {
    "type": "object",
    "properties": {
        "id": id_schema,
        "name": name_schema,
        "type": {
            "type": "string",
            "minLength": 1
        },
        "location_id": {
            "type": "integer",
            "minimum": 1
        },
        "user_id": {
            "type": ["integer", "null"],
            "minimum": 1
        }
    },
    "required": ["name", "type", "location_id"],
    "additionalProperties": False
}

# Schema for consumption
consumption_schema = {
    "type": "object",
    "properties": {
        "id": id_schema,
        "name": name_schema,
        "type": {
            "type": "string",
            "minLength": 1
        },
        "location_id": {
            "type": "integer",
            "minimum": 1
        },
        "user_id": {
            "type": ["integer", "null"],
            "minimum": 1
        }
    },
    "required": ["name", "type", "location_id"],
    "additionalProperties": False
}

# Map resource names to their schemas
SCHEMA_MAP = {
    "users": users_schema,
    "locations": locations_schema,
    "devices": devices_schema,
    "consumption": consumption_schema
}
