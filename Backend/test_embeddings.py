"""TASK-013 test: generate embedding for 'test'."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from agent.embeddings import get_embedding, embedding_to_blob, blob_to_embedding, cosine_similarity


async def main():
    print("Testing get_embedding('test')...")
    vec = await get_embedding("test")
    print(f"  type: {type(vec)}")
    print(f"  len:  {len(vec)}")
    print(f"  first 5 values: {vec[:5]}")
    assert isinstance(vec, list), "Should be list"
    assert all(isinstance(v, float) for v in vec[:10]), "Should be list[float]"
    print("  ✅ returns list[float]")

    # Test blob round-trip
    blob = embedding_to_blob(vec)
    vec2 = blob_to_embedding(blob)
    assert len(vec2) == len(vec), "blob round-trip length mismatch"
    print(f"  ✅ blob round-trip OK ({len(blob)} bytes)")

    # Test cosine similarity with itself == 1.0
    sim = cosine_similarity(vec, vec)
    assert abs(sim - 1.0) < 1e-4, f"self-similarity should be ~1.0, got {sim}"
    print(f"  ✅ cosine_similarity(v, v) ≈ {sim:.6f}")

    print("\nAll tests PASSED")


asyncio.run(main())
