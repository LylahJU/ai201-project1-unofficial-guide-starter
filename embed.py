"""
Embedding Pipeline

chunks.json
    ↓
SentenceTransformer embeddings
    ↓
ChromaDB vector store
"""

import json
from sentence_transformers import SentenceTransformer
import chromadb

# --------------------------------------------------
# Configuration
# --------------------------------------------------

CHUNKS_FILE = "chunks.json"
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "ucsc_dining"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# --------------------------------------------------
# Load Chunks
# --------------------------------------------------

def load_chunks(filepath):
    """
    Load chunk data from JSON.
    """

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------
# Create Embeddings
# --------------------------------------------------

def create_embeddings(model, texts):
    """
    Generate embeddings for a list of texts.
    """

    return model.encode(
        texts,
        show_progress_bar=True
    )


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    print("\nLoading embedding model...")

    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Model loaded.\n")

    # ----------------------------------------------
    # Load chunks
    # ----------------------------------------------

    chunks = load_chunks(CHUNKS_FILE)

    print(f"Loaded {len(chunks)} chunks.\n")

    texts = [chunk["text"] for chunk in chunks]

    # ----------------------------------------------
    # Generate embeddings
    # ----------------------------------------------

    print("Generating embeddings...")

    embeddings = create_embeddings(model, texts)

    print("Embeddings complete.\n")

    # ----------------------------------------------
    # Connect to ChromaDB
    # ----------------------------------------------

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    # Delete existing collection if rebuilding
    try:
        client.delete_collection(COLLECTION_NAME)
        print("Existing collection deleted.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME
    )

    # ----------------------------------------------
    # Prepare metadata
    # ----------------------------------------------

    ids = []
    metadatas = []

    for i, chunk in enumerate(chunks):

        ids.append(str(i))

        metadatas.append({
            "source": chunk["source"],
            "title": chunk["title"],
            "chunk_id": chunk["chunk_id"]
        })

    # ----------------------------------------------
    # Store in Chroma
    # ----------------------------------------------

    print("Adding vectors to ChromaDB...")

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas
    )

    print("\nDone.")
    print(f"Stored {len(chunks)} chunks.")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Database: {CHROMA_PATH}")


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    main()