"""
RAG Ingestion and Chunking Pipeline
Topic: Affordable Dining at UCSC

Pipeline:
Documents → Cleaning → Chunking → Embeddings → ChromaDB → Retrieval → Generation
"""

import os
import re
from pathlib import Path
import json

# --------------------------------------------------
# Configuration
# --------------------------------------------------

DOCUMENT_DIR = "documents"

# Approximate token counts using words
# 250 tokens ≈ 180 words
# 50 token overlap ≈ 35 words
CHUNK_SIZE = 180
CHUNK_OVERLAP = 35


# --------------------------------------------------
# Cleaning Function
# --------------------------------------------------

def clean_text(text):
    """
    Remove HTML tags and boilerplate content.
    """

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Common boilerplate patterns
    patterns = [
        r"cookie(s)? policy.*",
        r"accept all cookies.*",
        r"read more",
        r"share this.*",
        r"follow us.*",
        r"facebook",
        r"twitter",
        r"instagram",
        r"linkedin",
        r"subscribe.*newsletter",
        r"skip to main content",
        r"back to top",
    ]

    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove extra blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# --------------------------------------------------
# Load Documents
# --------------------------------------------------

def load_documents(document_dir):
    """
    Load all documents from the documents directory.

    Returns:
        List of dictionaries:
        {
            source,
            title,
            text
        }
    """

    documents = []

    # Recursively search for files under the documents directory
    for filepath in Path(document_dir).rglob("*"):

        # Only process text-based files
        if filepath.suffix.lower() not in [".txt", ".html", ".md"]:
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()

        cleaned_text = clean_text(raw_text)

        filename = filepath.stem.lower()

        # Determine document source
        filename = filepath.stem.lower()

        if filename.startswith("reddit_"):
            source = "Reddit"

        elif filename.startswith("ucsc_"):
            source = "UCSC"

        elif filename.startswith("sclocal_"):
            source = "Santa Cruz Local"

        else:
            source = "Unknown"

        documents.append({
            "source": source,
            "title": filepath.stem,
            "text": cleaned_text
        })

    return documents


# --------------------------------------------------
# Generic Word-Based Chunking
# --------------------------------------------------

def chunk_by_words(text):
    """
    Create approximately 250-token chunks
    using word counts.

    Returns:
        List of chunk strings
    """

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + CHUNK_SIZE

        chunk_text = " ".join(words[start:end])

        chunks.append(chunk_text)

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def chunk_by_paragraphs_semantic(text):
    """
    Group paragraphs into chunks up to CHUNK_SIZE words, using
    CHUNK_OVERLAP words for overlap between consecutive chunks.

    Falls back to `chunk_by_words` when a single paragraph exceeds
    CHUNK_SIZE to avoid losing content.

    Returns a list of chunk strings.
    """

    # Split into paragraphs and ignore empty ones
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks = []

    current_chunk_words = []
    current_len = 0

    for p in paragraphs:

        words = p.split()

        # If a single paragraph is larger than CHUNK_SIZE, flush current
        # chunk (if any) and split the paragraph by words.
        if len(words) > CHUNK_SIZE:

            if current_chunk_words:
                chunks.append(" ".join(current_chunk_words))
                # keep overlap from the flushed chunk
                current_chunk_words = (
                    current_chunk_words[-CHUNK_OVERLAP:]
                    if CHUNK_OVERLAP < len(current_chunk_words)
                    else current_chunk_words[:]
                )
                current_len = len(current_chunk_words)

            # split long paragraph into word-based chunks
            for part in chunk_by_words(" ".join(words)):
                chunks.append(part)

            # reset current chunk
            current_chunk_words = []
            current_len = 0

        else:

            # If adding this paragraph would exceed CHUNK_SIZE, flush
            # current chunk and start a new one with overlap
            if current_len + len(words) > CHUNK_SIZE:

                if current_chunk_words:
                    chunks.append(" ".join(current_chunk_words))

                overlap_words = (
                    current_chunk_words[-CHUNK_OVERLAP:]
                    if CHUNK_OVERLAP < len(current_chunk_words)
                    else current_chunk_words[:]
                )

                current_chunk_words = overlap_words + words
                current_len = len(current_chunk_words)

            else:
                current_chunk_words.extend(words)
                current_len += len(words)

    # append any remaining words
    if current_chunk_words:
        chunks.append(" ".join(current_chunk_words))

    return chunks


# --------------------------------------------------
# Reddit Chunking
# --------------------------------------------------

def chunk_reddit_document(doc):
    """
    Chunk Reddit threads by comment boundaries
    whenever possible.
    """

    chunks = []

    chunk_id = 0

    # Assume comments are separated by blank lines
    comments = re.split(r"\n\s*\n", doc["text"])

    for comment in comments:

        comment = comment.strip()

        # Skip tiny comments
        if len(comment.split()) < 5:
            continue

        word_count = len(comment.split())

        # Keep short comments intact
        if word_count <= CHUNK_SIZE:

            chunks.append({
                "source": doc["source"],
                "title": doc["title"],
                "chunk_id": chunk_id,
                "text": comment
            })

            chunk_id += 1

        # Split long comments
        else:

            split_chunks = chunk_by_words(comment)

            for chunk in split_chunks:

                chunks.append({
                    "source": doc["source"],
                    "title": doc["title"],
                    "chunk_id": chunk_id,
                    "text": chunk
                })

                chunk_id += 1

    return chunks


# --------------------------------------------------
# UCSC Webpage Chunking
# --------------------------------------------------

def chunk_web_document(doc):
    """
    Chunk UCSC webpages by paragraph boundaries,
    then split into approximately 250-token chunks.
    """

    chunks = []

    chunk_id = 0

    # Split into paragraphs
    paragraphs = re.split(r"\n\s*\n", doc["text"])

    # Remove very short paragraphs
    paragraphs = [
        p.strip()
        for p in paragraphs
        if len(p.split()) > 10
    ]

    combined_text = "\n\n".join(paragraphs)

    split_chunks = chunk_by_paragraphs_semantic(combined_text)

    for chunk in split_chunks:

        chunks.append({
            "source": doc["source"],
            "title": doc["title"],
            "chunk_id": chunk_id,
            "text": chunk
        })

        chunk_id += 1

    return chunks


# --------------------------------------------------
# Main Pipeline
# --------------------------------------------------

def main():

    print("Loading documents...\n")

    documents = load_documents(DOCUMENT_DIR)

    print(f"Loaded {len(documents)} documents.\n")

    # --------------------------------------------------
    # Print one cleaned document
    # --------------------------------------------------

    if documents:

        print("=" * 80)
        print("CLEANED DOCUMENT SAMPLE")
        print("=" * 80)

        sample = documents[0]

        print("Title:", sample["title"])
        print("Source:", sample["source"])

        print("\nPreview:\n")
        print(sample["text"][:1000])

        print("\n")

    # --------------------------------------------------
    # Generate chunks
    # --------------------------------------------------

    all_chunks = []

    for doc in documents:

        if doc["source"] == "Reddit":

            doc_chunks = chunk_reddit_document(doc)

        else:

            doc_chunks = chunk_web_document(doc)

        all_chunks.extend(doc_chunks)

    # --------------------------------------------------
    # Save chunks to JSON
    # --------------------------------------------------

    with open("chunks.json", "w", encoding="utf-8") as f:
        json.dump(
            all_chunks,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Saved {len(all_chunks)} chunks to chunks.json")

    # --------------------------------------------------
    # Print representative chunks
    # --------------------------------------------------

    print("=" * 80)
    print("FIVE REPRESENTATIVE CHUNKS")
    print("=" * 80)

    for chunk in all_chunks[:5]:

        print("\n")
        print(f"Source: {chunk['source']}")
        print(f"Title: {chunk['title']}")
        print(f"Chunk ID: {chunk['chunk_id']}")

        print("\nChunk Text:")
        print(chunk["text"][:500])

        print("\n" + "-" * 80)

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    print("\n")
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"Total cleaned documents: {len(documents)}")
    print(f"Total chunks generated: {len(all_chunks)}")


# --------------------------------------------------
# Run Pipeline
# --------------------------------------------------

if __name__ == "__main__":
    main()