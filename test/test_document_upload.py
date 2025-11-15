#!/usr/bin/env python3
"""
Test document upload and embedding generation
"""
import requests
import time
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

BASE_URL = "http://localhost:8000"

def create_test_pdf():
    """Create a simple test PDF with some content"""
    filename = "test_research_paper.pdf"

    c = canvas.Canvas(filename, pagesize=letter)

    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "AI and Machine Learning Research")
    c.setFont("Helvetica", 12)
    c.drawString(100, 720, "A Comprehensive Overview")

    c.setFont("Helvetica", 11)
    y = 680

    content_page1 = [
        "Abstract:",
        "",
        "Artificial Intelligence (AI) and Machine Learning (ML) have revolutionized",
        "modern technology. This paper explores key concepts in AI including neural",
        "networks, deep learning, natural language processing, and computer vision.",
        "",
        "Introduction:",
        "",
        "Machine learning is a subset of artificial intelligence that enables computers",
        "to learn from data without being explicitly programmed. Deep learning, a subset",
        "of machine learning, uses neural networks with multiple layers to process",
        "complex patterns in large datasets.",
        "",
        "The University of Virginia has been at the forefront of AI research, with",
        "faculty and students contributing to breakthroughs in natural language",
        "processing and computer vision applications.",
    ]

    for line in content_page1:
        c.drawString(100, y, line)
        y -= 20
        if y < 100:
            c.showPage()
            y = 750

    # Page 2
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, "Key Concepts in Neural Networks")
    c.setFont("Helvetica", 11)

    y = 720
    content_page2 = [
        "",
        "Neural networks are computational models inspired by biological neural networks.",
        "They consist of interconnected nodes (neurons) organized in layers:",
        "",
        "1. Input Layer: Receives the raw data",
        "2. Hidden Layers: Process and transform the data",
        "3. Output Layer: Produces the final prediction",
        "",
        "Training Process:",
        "",
        "Neural networks learn through a process called backpropagation, which adjusts",
        "the weights between neurons to minimize prediction errors. This involves:",
        "- Forward pass: Computing predictions",
        "- Loss calculation: Measuring prediction error",
        "- Backward pass: Computing gradients",
        "- Weight update: Adjusting parameters",
    ]

    for line in content_page2:
        c.drawString(100, y, line)
        y -= 20

    c.save()
    return filename

def register_and_login():
    """Register a new user and get auth token"""
    import random
    import string

    random_suffix = ''.join(random.choices(string.digits, k=4))
    user_email = f"embedtest{random_suffix}@uva.edu"

    # Register
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": user_email,
            "password": "testpass123",
            "full_name": "Embedding Test User"
        }
    )

    if register_response.status_code != 200:
        print(f"Registration failed: {register_response.text}")
        return None

    # Login
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": user_email,
            "password": "testpass123"
        }
    )

    if login_response.status_code == 200:
        print(f"✓ Successfully authenticated as {user_email}")
        return login_response.json()["access_token"]
    else:
        print(f"Login failed: {login_response.text}")
        return None

def upload_document(token, filename):
    """Upload a PDF document"""
    print(f"\nUploading document: {filename}")

    with open(filename, 'rb') as f:
        files = {'file': (filename, f, 'application/pdf')}
        data = {'document_type': 'research_paper'}  # Required field
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.post(
            f"{BASE_URL}/documents/upload",
            files=files,
            data=data,
            headers=headers
        )

    if response.status_code == 200:
        doc_data = response.json()
        print(f"✓ Document uploaded successfully")
        print(f"  - Document ID: {doc_data.get('id')}")
        print(f"  - Status: {doc_data.get('status')}")
        print(f"  - Chunks: {doc_data.get('chunk_count', 'N/A')}")
        return doc_data
    else:
        print(f"✗ Upload failed: {response.text}")
        return None

def process_document(token, doc_id):
    """Trigger document processing (chunking and embedding)"""
    print(f"\nTriggering document processing for ID {doc_id}...")

    response = requests.post(
        f"{BASE_URL}/documents/{doc_id}/process",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        print(f"✓ Processing started: {response.json().get('message')}")
        return True
    else:
        print(f"✗ Processing failed: {response.text}")
        return False

def generate_embeddings(token, doc_id):
    """Trigger embedding generation"""
    print(f"\nTriggering embedding generation for ID {doc_id}...")

    response = requests.post(
        f"{BASE_URL}/embeddings/generate/{doc_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        print(f"✓ Embedding generation started: {response.json().get('message')}")
        return True
    else:
        print(f"✗ Embedding generation failed: {response.text}")
        return False

def wait_for_embeddings(token, doc_id, max_wait=60):
    """Wait for embeddings to be generated"""
    print(f"\nWaiting for embeddings to be generated (max {max_wait}s)...")

    start_time = time.time()

    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{BASE_URL}/documents/",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            documents = response.json()
            doc = next((d for d in documents if d['id'] == doc_id), None)

            if doc:
                status = doc.get('status')
                print(f"  Status: {status}")

                if status == 'embedded':
                    print(f"✓ Embeddings generated successfully!")
                    return True
                elif status == 'failed':
                    print(f"✗ Embedding generation failed")
                    return False

        time.sleep(2)

    print(f"✗ Timeout waiting for embeddings")
    return False

def test_semantic_search(token):
    """Test semantic search functionality"""
    print("\n" + "="*80)
    print("Testing Semantic Search")
    print("="*80)

    test_queries = [
        "What is machine learning?",
        "Tell me about neural networks",
        "What research is UVA doing in AI?"
    ]

    for query in test_queries:
        print(f"\n📝 Query: {query}")

        response = requests.post(
            f"{BASE_URL}/search/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "query": query,
                "max_results": 3,
                "similarity_threshold": 0.3
            }
        )

        if response.status_code == 200:
            results = response.json()

            if results:
                print(f"✓ Found {len(results)} result(s)")

                for idx, result in enumerate(results, 1):
                    print(f"\n  Result {idx}:")
                    print(f"    Document: {result.get('document_name')}")
                    print(f"    Page: {result.get('page_number', 'N/A')}")
                    print(f"    Similarity: {result.get('similarity_score', 0):.3f}")
                    snippet = result.get('chunk_text', '')[:150]
                    print(f"    Text: {snippet}...")
            else:
                print(f"✗ No results found (similarity threshold might be too high)")
        else:
            print(f"✗ Search failed: {response.text}")

def test_rag_with_document(token):
    """Test RAG query with uploaded document"""
    print("\n" + "="*80)
    print("Testing RAG with Uploaded Document")
    print("="*80)

    query = "Explain the training process of neural networks based on the document"
    print(f"\n📝 Query: {query}")

    response = requests.post(
        f"{BASE_URL}/rag/ask",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": query,
            "max_iterations": 1,
            "enable_detailed_reasoning": True
        },
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()

        print(f"\n✓ RAG Response received")
        print(f"  Confidence: {result.get('confidence_score', 0):.2f}")

        # Check for local document usage
        if 'reasoning_steps' in result:
            for step in result['reasoning_steps']:
                if step.get('node') == 'local_search':
                    results_count = step.get('results_count', 0)
                    print(f"  Local docs found: {results_count}")
                    break

        # Show answer
        answer = result.get('final_answer', '')
        print(f"\n📄 Answer:\n{answer[:500]}...")

        # Show sources
        if 'sources' in result:
            doc_sources = [s for s in result['sources'] if s.get('type') == 'document']
            if doc_sources:
                print(f"\n📚 Document sources used: {len(doc_sources)}")
    else:
        print(f"✗ RAG query failed: {response.text}")

def main():
    """Main test execution"""
    print("="*80)
    print("  HuggingFace Embeddings Test")
    print("  Testing document upload and embedding generation")
    print("="*80)

    # Create test PDF
    print("\n1. Creating test PDF...")
    pdf_filename = create_test_pdf()
    print(f"✓ Created: {pdf_filename}")

    # Authenticate
    print("\n2. Authenticating...")
    token = register_and_login()
    if not token:
        print("✗ Authentication failed, exiting")
        return

    # Upload document
    print("\n3. Uploading document...")
    doc_data = upload_document(token, pdf_filename)
    if not doc_data:
        print("✗ Upload failed, exiting")
        return

    doc_id = doc_data.get('id')

    # Process document
    print("\n4. Processing document (chunking)...")
    if not process_document(token, doc_id):
        print("✗ Failed to start processing")
        return False

    # Generate embeddings
    print("\n5. Generating embeddings...")
    if not generate_embeddings(token, doc_id):
        print("✗ Failed to start embedding generation")
        return False

    # Wait for embeddings
    print("\n6. Waiting for embeddings to complete...")
    success = wait_for_embeddings(token, doc_id)

    if not success:
        print("\n⚠️  Embeddings generation failed or timed out")
        print("This might indicate an issue with the HuggingFace model download")
        print("\nRecommending switch to OpenAI embeddings...")
        return False

    # Test semantic search
    print("\n7. Testing semantic search...")
    test_semantic_search(token)

    # Test RAG with document
    print("\n8. Testing RAG with document...")
    test_rag_with_document(token)

    # Cleanup
    if os.path.exists(pdf_filename):
        os.remove(pdf_filename)
        print(f"\n✓ Cleaned up test file: {pdf_filename}")

    print("\n" + "="*80)
    print("  Test Complete!")
    print("  HuggingFace embeddings are working correctly ✓")
    print("="*80)

    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n⚠️  Will proceed with OpenAI embeddings integration...")
            exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
