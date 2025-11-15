"""
Run this script ONCE to fix Qdrant indexes
python fix_indexes.py
"""
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType
import config

print("🔧 Fixing Qdrant indexes...")

# Connect to Qdrant
qdrant_client = QdrantClient(
    url=config.QDRANT_URL,
    api_key=config.QDRANT_API_KEY
)

# Fix indexes for 'conversations' collection
try:
    print(f"\n📁 Fixing '{config.COLLECTION_NAME}' collection...")
    
    # Create thread_id index
    try:
        qdrant_client.create_payload_index(
            collection_name=config.COLLECTION_NAME,
            field_name="thread_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("  ✅ Created index for 'thread_id'")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("  ℹ️ Index 'thread_id' already exists")
        else:
            print(f"  ⚠️ thread_id index error: {e}")
    
    # Create role index
    try:
        qdrant_client.create_payload_index(
            collection_name=config.COLLECTION_NAME,
            field_name="role",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("  ✅ Created index for 'role'")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("  ℹ️ Index 'role' already exists")
        else:
            print(f"  ⚠️ role index error: {e}")
            
except Exception as e:
    print(f"  ❌ Error with '{config.COLLECTION_NAME}': {e}")


# Fix indexes for 'documents' collection
try:
    print(f"\n📄 Fixing 'documents' collection...")
    
    # Create user_id index (CRITICAL FIX)
    try:
        qdrant_client.create_payload_index(
            collection_name="documents",
            field_name="user_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("  ✅ Created index for 'user_id'")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("  ℹ️ Index 'user_id' already exists")
        else:
            print(f"  ⚠️ user_id index error: {e}")
    
    # Create document_id index
    try:
        qdrant_client.create_payload_index(
            collection_name="documents",
            field_name="document_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("  ✅ Created index for 'document_id'")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("  ℹ️ Index 'document_id' already exists")
        else:
            print(f"  ⚠️ document_id index error: {e}")
            
    # Create filename index
    try:
        qdrant_client.create_payload_index(
            collection_name="documents",
            field_name="filename",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print("  ✅ Created index for 'filename'")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("  ℹ️ Index 'filename' already exists")
        else:
            print(f"  ⚠️ filename index error: {e}")
            
except Exception as e:
    print(f"  ❌ Error with 'documents' collection: {e}")


print("\n✅ Done! All indexes have been created/verified.")
print("You can now restart your Streamlit app.\n")