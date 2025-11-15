#!/usr/bin/env python3
"""
Comparison test between HuggingFace and OpenAI embeddings
Tests both providers and compares search quality
"""
import requests
import json
import time
from reportlab.pdfgen import canvas

BASE_URL = "http://localhost:8000"

def create_test_pdf():
    """Create a test PDF about AI/ML"""
    filename = "embedding_test_paper.pdf"
    c = canvas.Canvas(filename)

    content = [
        "Gradient Descent Optimization in Neural Networks",
        "",
        "Gradient descent is a fundamental optimization algorithm used to train neural networks.",
        "The algorithm iteratively adjusts weights to minimize the loss function through backpropagation.",
        "",
        "Variants include Stochastic Gradient Descent (SGD), Adam, RMSprop, and momentum-based methods.",
        "Learning rate scheduling is crucial for convergence and avoiding local minima.",
        "",
        "The University of Virginia conducts research on adaptive learning rates and optimization theory.",
    ]

    y = 750
    for line in content:
        c.drawString(100, y, line)
        y -= 20

    c.save()
    return filename

def authenticate():
    """Register and login"""
    import random
    import string

    random_suffix = ''.join(random.choices(string.digits, k=4))
    user = {
        "email": f"compare{random_suffix}@uva.edu",
        "password": "testpass123",
        "full_name": "Comparison Test"
    }

    # Register
    requests.post(f"{BASE_URL}/auth/register", json=user)

    # Login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": user["email"], "password": user["password"]}
    )

    if response.status_code == 200:
        print(f"✓ Authenticated as {user['email']}")
        return response.json()["access_token"]
    return None

def upload_and_process(token, filename):
    """Upload and process document"""
    print(f"\nUploading {filename}...")

    with open(filename, 'rb') as f:
        files = {'file': (filename, f, 'application/pdf')}
        data = {'document_type': 'research_paper'}

        response = requests.post(
            f"{BASE_URL}/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {token}"}
        )

    if response.status_code != 200:
        print(f"✗ Upload failed: {response.text}")
        return None

    doc_id = response.json()["id"]
    print(f"✓ Uploaded document ID: {doc_id}")

    # Process
    print("Processing document...")
    requests.post(
        f"{BASE_URL}/documents/{doc_id}/process",
        headers={"Authorization": f"Bearer {token}"}
    )

    return doc_id

def generate_embeddings_with_provider(token, doc_id, provider):
    """Generate embeddings with specific provider"""
    print(f"\nGenerating embeddings with {provider.upper()}...")

    response = requests.post(
        f"{BASE_URL}/embeddings/generate/{doc_id}?provider={provider}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ {result['message']}")
        print(f"  Provider: {result['provider']}")
        print(f"  Model: {result['model']}")

        # Wait for completion
        time.sleep(2)
        return True
    else:
        print(f"✗ Failed: {response.text}")
        return False

def test_search_quality(token, provider):
    """Test search quality with different queries"""
    print(f"\n{'='*80}")
    print(f"Testing Search Quality: {provider.upper()}")
    print(f"{'='*80}")

    test_queries = [
        "What is gradient descent?",
        "Explain optimization algorithms",
        "Tell me about learning rate",
        "What research is UVA doing?",
        "How does backpropagation work?",
    ]

    results_summary = []

    for query in test_queries:
        print(f"\n📝 Query: {query}")

        response = requests.post(
            f"{BASE_URL}/search/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "query": query,
                "max_results": 3,
                "similarity_threshold": 0.2
            }
        )

        if response.status_code == 200:
            results = response.json()

            if results:
                top_score = results[0].get('similarity_score', 0)
                avg_score = sum(r.get('similarity_score', 0) for r in results) / len(results)

                print(f"  ✓ Found {len(results)} results")
                print(f"  Top similarity: {top_score:.3f}")
                print(f"  Avg similarity: {avg_score:.3f}")

                results_summary.append({
                    "query": query,
                    "count": len(results),
                    "top_score": top_score,
                    "avg_score": avg_score
                })
            else:
                print(f"  ✗ No results found")
                results_summary.append({
                    "query": query,
                    "count": 0,
                    "top_score": 0,
                    "avg_score": 0
                })
        else:
            print(f"  ✗ Search failed: {response.text}")

    return results_summary

def compare_results(hf_results, openai_results):
    """Compare results from both providers"""
    print(f"\n{'='*80}")
    print("COMPARISON SUMMARY")
    print(f"{'='*80}\n")

    print(f"{'Query':<40} {'HF Score':<12} {'OpenAI Score':<12} {'Winner'}")
    print("-" * 80)

    hf_wins = 0
    openai_wins = 0

    for hf, oa in zip(hf_results, openai_results):
        query = hf['query'][:37] + "..." if len(hf['query']) > 40 else hf['query']
        hf_score = hf['top_score']
        oa_score = oa['top_score']

        winner = "HuggingFace" if hf_score > oa_score else "OpenAI" if oa_score > hf_score else "Tie"

        if hf_score > oa_score:
            hf_wins += 1
        elif oa_score > hf_score:
            openai_wins += 1

        print(f"{query:<40} {hf_score:<12.3f} {oa_score:<12.3f} {winner}")

    print("-" * 80)
    print(f"\nOverall Winner: {'HuggingFace' if hf_wins > openai_wins else 'OpenAI' if openai_wins > hf_wins else 'Tie'}")
    print(f"HuggingFace wins: {hf_wins}")
    print(f"OpenAI wins: {openai_wins}")

    # Calculate averages
    hf_avg = sum(r['top_score'] for r in hf_results) / len(hf_results) if hf_results else 0
    oa_avg = sum(r['top_score'] for r in openai_results) / len(openai_results) if openai_results else 0

    print(f"\nAverage Top Score:")
    print(f"  HuggingFace: {hf_avg:.3f}")
    print(f"  OpenAI: {oa_avg:.3f}")
    print(f"  Difference: {abs(oa_avg - hf_avg):.3f} ({((oa_avg - hf_avg) / hf_avg * 100):.1f}%)")

def main():
    """Main comparison test"""
    print("="*80)
    print("  Embedding Provider Comparison Test")
    print("  HuggingFace vs OpenAI")
    print("="*80)

    # Create test document
    print("\n1. Creating test document...")
    filename = create_test_pdf()

    # Authenticate
    print("\n2. Authenticating...")
    token = authenticate()
    if not token:
        print("✗ Authentication failed")
        return

    # Upload and process document
    print("\n3. Uploading and processing document...")
    doc_id = upload_and_process(token, filename)
    if not doc_id:
        return

    # Test HuggingFace
    print("\n" + "="*80)
    print("TESTING HUGGINGFACE EMBEDDINGS")
    print("="*80)

    if generate_embeddings_with_provider(token, doc_id, "huggingface"):
        hf_results = test_search_quality(token, "huggingface")
    else:
        print("✗ HuggingFace embedding generation failed")
        return

    # Test OpenAI
    print("\n" + "="*80)
    print("TESTING OPENAI EMBEDDINGS")
    print("="*80)

    if generate_embeddings_with_provider(token, doc_id, "openai"):
        openai_results = test_search_quality(token, "openai")
    else:
        print("✗ OpenAI embedding generation failed")
        return

    # Compare results
    compare_results(hf_results, openai_results)

    # Cleanup
    import os
    if os.path.exists(filename):
        os.remove(filename)

    print("\n" + "="*80)
    print("  Test Complete!")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
