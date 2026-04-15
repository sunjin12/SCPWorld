"""Upload to Firestore — Generate BGE-M3 embeddings and upload to Firestore.

Usage:
    uv run python scripts/upload_to_firestore.py
"""

import json
import os
import uuid
from pathlib import Path

from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

SCRIPT_DIR = Path(__file__).parent.parent
DATA_DIR = SCRIPT_DIR / "data"

# Configuration
COLLECTION_NAME = "scp_documents"
EMBEDDING_MODEL = "BAAI/bge-m3"
BATCH_SIZE = 100  # Firestore batch limit is 500
VECTOR_DIM = 1024


def setup_firestore():
    """Initialize Firestore client."""
    print("   Connecting to Firestore...")
    db = firestore.Client(project="scpworld")
    return db


def main():
    """Main embedding and upload pipeline for Firestore."""
    input_file = DATA_DIR / "scp_chunks.json"

    if not input_file.exists():
        print("Run preprocess.py first!")
        return

    with open(input_file, encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loading embedding model: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    db = setup_firestore()
    collection_ref = db.collection(COLLECTION_NAME)

    # Process in batches
    print(f"Embedding and uploading {len(chunks)} chunks to Firestore...")
    
    # Firestore allows up to 500 writes per batch
    # We'll use smaller batches to avoid memory/timeout issues with large vectors
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Uploading"):
        batch_chunks = chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch_chunks]

        # Generate embeddings (dense vectors)
        embeddings = model.encode(texts, normalize_embeddings=True)

        # Use Firestore WriteBatch
        write_batch = db.batch()
        
        for chunk, embedding in zip(batch_chunks, embeddings):
            doc_id = uuid.uuid4().hex
            doc_ref = collection_ref.document(doc_id)
            
            # Firestore Vector Search expects a vector field
            # We use the 'vector' field name as it's common
            data = {
                "item_number": chunk["item_number"],
                "object_class": chunk["object_class"],
                "section_type": chunk["section_type"],
                "tags": chunk.get("tags", []),
                "text": chunk["text"],
                "url": chunk["url"],
                "embedding": Vector(embedding.tolist())
            }
            write_batch.set(doc_ref, data)
        
        write_batch.commit()

    print(f"\nSuccessfully uploaded documents to Firestore collection '{COLLECTION_NAME}'")


if __name__ == "__main__":
    main()
