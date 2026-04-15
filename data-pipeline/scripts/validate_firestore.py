"""Validate Firestore Setup — Check data and vector index status.

Usage:
    uv run python scripts/validate_firestore.py
"""

import os
import subprocess
import json
import time
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from sentence_transformers import SentenceTransformer

# Configuration
PROJECT_ID = "scpworld"
COLLECTION_NAME = "scp_documents"
EMBEDDING_MODEL = "BAAI/bge-m3"

def check_index_status():
    """Check the status of Firestore composite indexes using gcloud."""
    print("Checking Firestore Index status...")
    try:
        cmd = f"gcloud firestore indexes composite list --project={PROJECT_ID} --format=json"
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        indexes = json.loads(result.stdout)
        
        vector_index = None
        for idx in indexes:
            # Look for an index on scp_documents that has a vector field config
            if COLLECTION_NAME in idx.get("name", ""):
                # Firestore JSON format for vector index includes vectorConfig
                fields = idx.get("fields", [])
                for f in fields:
                    if f.get("fieldPath") == "embedding" and "vectorConfig" in f:
                        vector_index = idx
                        break
        
        if not vector_index:
            print("Index NOT found for collection 'scp_documents'.")
            print("   Please create it using the following command:")
            print(f"   gcloud firestore indexes composite create --project={PROJECT_ID} --collection-group={COLLECTION_NAME} --query-scope=COLLECTION --field-config=vector-config='{{ \"dimension\": \"1024\", \"flat\": {{}} }}',field-path=embedding")
            return False
        
        state = vector_index.get("state")
        print(f"   Index State: {state}")
        return state == "READY"
    
    except Exception as e:
        print(f"Error checking index status: {e}")
        return False

def validate_data():
    """Check document count in Firestore."""
    print(f"Checking Firestore collection: {COLLECTION_NAME}")
    db = firestore.Client(project=PROJECT_ID)
    docs = db.collection(COLLECTION_NAME).limit(5).get()
    
    count = 0
    # Note: count() aggregation is available in Firestore
    count_query = db.collection(COLLECTION_NAME).count()
    result = count_query.get()
    total_docs = result[0][0].value
    
    print(f"   Total documents: {total_docs}")
    if total_docs > 0:
        print("   Sample document fields:")
        for doc in docs:
            d = doc.to_dict()
            print(f"   - {d.get('item_number', 'unknown')}: {d.get('section_type', 'unknown')} (text len: {len(d.get('text', ''))})")
    
    return total_docs > 0

def test_vector_search():
    """Test Firestore Vector Search (find_nearest)."""
    print("\nTesting Vector Search ('find_nearest')...")
    db = firestore.Client(project=PROJECT_ID)
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    query_text = "How to contain SCP-173?"
    query_vector = model.encode(query_text, normalize_embeddings=True)
    
    collection_ref = db.collection(COLLECTION_NAME)
    
    try:
        # Firestore Vector Search Syntax (Note: requires index READY)
        results = collection_ref.find_nearest(
            vector_field="embedding",
            query_vector=Vector(query_vector.tolist()),
            distance_measure=DistanceMeasure.COSINE,
            limit=3
        ).get()
        
        print(f"   Found {len(results)} nearest neighbors:")
        for doc in results:
            d = doc.to_dict()
            print(f"   - {d.get('item_number', '?')} [Distance: ?]: {d.get('text')[:100]}...")
        return True
    except Exception as e:
        print(f"Vector search failed: {e}")
        print("   (This is expected if the index is still building or not created)")
        return False

def main():
    print("=== Firestore Validation Step ===\n")
    data_ok = validate_data()
    index_ok = check_index_status()
    
    if data_ok and index_ok:
        search_ok = test_vector_search()
        if search_ok:
            print("\nFirestore is FULLY READY for RAG!")
        else:
            print("\nData and Index exist, but search failed. Check dimensions/permissions.")
    else:
        print("\nFirestore is not yet ready. Fix the issues above and try again.")

if __name__ == "__main__":
    main()
