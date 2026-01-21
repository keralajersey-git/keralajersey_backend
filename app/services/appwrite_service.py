from appwrite.id import ID
from appwrite.query import Query
from app.config import databases, storage, APPWRITE_DATABASE_ID, APPWRITE_COLLECTION_ID, APPWRITE_BUCKET_ID
from app.schemas.product import ProductCreate, ProductUpdate
import json

class AppwriteService:
    @staticmethod
    async def create_product(product: ProductCreate):
        data = product.model_dump()
        # Appwrite likes flat objects for attributes
        # If available_sizes is a list, we might need to store it as a JSON string or Appwrite's array attribute
        # For now, let's assume the collection is configured with an array of strings for available_sizes
        
        response = databases.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_COLLECTION_ID,
            document_id=ID.unique(),
            data=data
        )
        return response

    @staticmethod
    async def get_products():
        response = databases.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_COLLECTION_ID
        )
        return response["documents"]

    @staticmethod
    async def get_product(product_id: str):
        response = databases.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_COLLECTION_ID,
            document_id=product_id
        )
        return response

    @staticmethod
    async def update_product(product_id: str, product_update: ProductUpdate):
        data = product_update.model_dump(exclude_unset=True)
        response = databases.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_COLLECTION_ID,
            document_id=product_id,
            data=data
        )
        return response

    @staticmethod
    async def delete_product(product_id: str):
        response = databases.delete_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_COLLECTION_ID,
            document_id=product_id
        )
        return response

    @staticmethod
    async def upload_image(file_bytes, filename):
        # In literal use, you'd probably use form-data in the route
        # and pass the file contents here
        from appwrite.input_file import InputFile
        
        # This is a placeholder for how you'd upload
        # file = InputFile.from_bytes(file_bytes, filename)
        # response = storage.create_file(bucket_id=APPWRITE_BUCKET_ID, file_id=ID.unique(), file=file)
        # return response['$id']
        pass
