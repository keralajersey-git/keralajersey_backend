import os
import sys
from dotenv import load_dotenv

# Add the project root to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import (
    databases, 
    APPWRITE_DATABASE_ID, 
    APPWRITE_COLLECTION_ID
)

def setup_collection():
    print(f"Creating attributes for collection: {APPWRITE_COLLECTION_ID}")
    
    attributes = [
        {"key": "title", "type": "string", "size": 255, "required": True},
        {"key": "description", "type": "string", "size": 1000, "required": True},
        {"key": "image1", "type": "string", "size": 255, "required": True},
        {"key": "image2", "type": "string", "size": 255, "required": False},
        {"key": "image3", "type": "string", "size": 255, "required": False},
        {"key": "available_sizes", "type": "string", "size": 50, "required": True, "array": True},
        {"key": "stock", "type": "boolean", "required": True, "default": True},
        {"key": "stock_left", "type": "integer", "required": False},
        {"key": "price", "type": "double", "required": True},
        {"key": "free_delivery", "type": "boolean", "required": True, "default": False},
    ]

    for attr in attributes:
        try:
            key = attr["key"]
            print(f"Adding attribute: {key}...")
            
            if attr["type"] == "string":
                databases.create_string_attribute(
                    APPWRITE_DATABASE_ID, 
                    APPWRITE_COLLECTION_ID, 
                    key, 
                    attr["size"], 
                    attr["required"],
                    array=attr.get("array", False)
                )
            elif attr["type"] == "boolean":
                databases.create_boolean_attribute(
                    APPWRITE_DATABASE_ID, 
                    APPWRITE_COLLECTION_ID, 
                    key, 
                    attr["required"],
                    default=attr.get("default")
                )
            elif attr["type"] == "integer":
                databases.create_integer_attribute(
                    APPWRITE_DATABASE_ID, 
                    APPWRITE_COLLECTION_ID, 
                    key, 
                    attr["required"]
                )
            elif attr["type"] == "double":
                databases.create_float_attribute(
                    APPWRITE_DATABASE_ID, 
                    APPWRITE_COLLECTION_ID, 
                    key, 
                    attr["required"]
                )
            print(f"DONE: {key} created.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"INFO: {key} already exists, skipping.")
            else:
                print(f"ERROR: creating {key}: {str(e)}")

if __name__ == "__main__":
    setup_collection()
    print("\nInitialization complete! Go to Appwrite Console to check your attributes.")
