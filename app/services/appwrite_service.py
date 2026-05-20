from appwrite.id import ID
from appwrite.query import Query
from app.config import databases, storage, APPWRITE_DATABASE_ID, APPWRITE_COLLECTION_ID, APPWRITE_BUCKET_ID, APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID
from app.schemas.product import ProductCreate, ProductUpdate
import json

class AppwriteService:
    @staticmethod
    def _ensure_image_url(image_value):
        if not image_value:
            return image_value
        
        # If it's already a URL, return it
        if image_value.startswith('http'):
            return image_value
            
        # If it's an Appwrite ID (no slashes or dots), construct the URL
        if '/' not in image_value and '.' not in image_value:
            return f"{APPWRITE_ENDPOINT}/storage/buckets/{APPWRITE_BUCKET_ID}/files/{image_value}/view?project={APPWRITE_PROJECT_ID}"
            
        return image_value

    @staticmethod
    def _transform_product(doc):
        # Transform image fields if they are just IDs
        for img_field in ['image1', 'image2', 'image3']:
            val = doc.get(img_field)
            if val:
                doc[img_field] = AppwriteService._ensure_image_url(val)
        return doc

    @staticmethod
    def create_product(product: ProductCreate):
        data = product.model_dump()
        response = databases.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_COLLECTION_ID,
            document_id=ID.unique(),
            data=data
        )
        return AppwriteService._transform_product(response)

    @staticmethod
    def get_products():
        try:
            all_products = []
            limit = 100
            cursor_after = None
            
            while True:
                queries = [Query.limit(limit), Query.order_asc("$id")]
                if cursor_after:
                    queries.append(Query.cursor_after(cursor_after))
                
                print(f"DEBUG: Fetching products with queries: {queries}")
                response = databases.list_documents(
                    database_id=APPWRITE_DATABASE_ID,
                    collection_id=APPWRITE_COLLECTION_ID,
                    queries=queries
                )
                documents = response["documents"]
                print(f"DEBUG: Got {len(documents)} documents")
                all_products.extend(documents)
                
                if len(documents) < limit:
                    break
                    
                cursor_after = documents[-1]["$id"]
                print(f"DEBUG: Using cursor after: {cursor_after}")
            
            products = [AppwriteService._transform_product(doc) for doc in all_products]
            
            # Sort by $createdAt descending (latest first)
            products.sort(key=lambda x: x.get('$createdAt', ''), reverse=True)
            
            print(f"DEBUG: Found {len(products)} products in Appwrite.")
            return products
        except Exception as e:
            print(f"DEBUG: Appwrite error type: {type(e).__name__}")
            print(f"DEBUG: Appwrite error message: {str(e)}")
            import traceback
            print(f"DEBUG: Appwrite error traceback: {traceback.format_exc()}")
            raise e

    @staticmethod
    def get_product(product_id: str):
        response = databases.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_COLLECTION_ID,
            document_id=product_id
        )
        return AppwriteService._transform_product(response)

    @staticmethod
    def update_product(product_id: str, product_update: ProductUpdate):
        data = product_update.model_dump(exclude_unset=True)
        response = databases.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_COLLECTION_ID,
            document_id=product_id,
            data=data
        )
        return AppwriteService._transform_product(response)

    @staticmethod
    def delete_product(product_id: str):
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
