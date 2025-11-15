#!/usr/bin/env python3
"""
Test script to validate Tavily and Embedding functionalities
"""
import requests
import json
import sys
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000"

# Test credentials - use unique email for testing
import random
import string
random_suffix = ''.join(random.choices(string.digits, k=4))

TEST_USER = {
    "email": f"test{random_suffix}@uva.edu",
    "password": "testpass123",
    "full_name": "Test User"
}

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_result(success: bool, message: str, data: Any = None):
    """Print test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"\n{status}: {message}")
    if data:
        print(json.dumps(data, indent=2))

def get_auth_token() -> str:
    """Login and get authentication token"""
    print_section("Authentication")

    # Try to login first (username field should contain email)
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": TEST_USER["email"],  # OAuth2 uses 'username' but expects email
            "password": TEST_USER["password"]
        }
    )

    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        print_result(True, "Logged in successfully")
        return token

    # If login fails, try to register
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json=TEST_USER
    )

    if register_response.status_code == 200:
        print("User registered successfully, now logging in...")
        # Login after registration (username field should contain email)
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": TEST_USER["email"],  # OAuth2 uses 'username' but expects email
                "password": TEST_USER["password"]
            }
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            print_result(True, "Registered and logged in successfully")
            return token

    print_result(False, f"Authentication failed: {register_response.text if register_response.status_code != 200 else login_response.text}")
    sys.exit(1)

def test_tavily_search(token: str):
    """Test Tavily web search functionality"""
    print_section("Testing Tavily Web Search")

    # Test query
    query = "What are the latest developments in artificial intelligence?"

    print(f"\nQuery: {query}")
    print("Sending request to RAG endpoint (which should use Tavily)...")

    try:
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

            # Check if we got web results
            web_results_found = False
            if "reasoning_steps" in result:
                for step in result["reasoning_steps"]:
                    if step.get("node") == "web_search":
                        web_results_found = True
                        print_result(
                            True,
                            f"Tavily search executed successfully! Found {step.get('results_count', 0)} web results",
                            {
                                "action": step.get("action"),
                                "results_count": step.get("results_count"),
                                "timestamp": step.get("timestamp")
                            }
                        )
                        break

            if not web_results_found:
                print_result(False, "No Tavily web search was performed (might have used only local results)")

            # Show sources
            if "sources" in result and result["sources"]:
                web_sources = [s for s in result["sources"] if s.get("type") == "web"]
                if web_sources:
                    print("\nWeb sources found:")
                    for idx, source in enumerate(web_sources[:3], 1):
                        print(f"{idx}. {source.get('title')} - {source.get('url')}")
                    print_result(True, f"Found {len(web_sources)} web sources via Tavily")
                else:
                    print_result(False, "No web sources in the results")

            # Show answer preview
            if "final_answer" in result:
                answer_preview = result["final_answer"][:200] + "..." if len(result["final_answer"]) > 200 else result["final_answer"]
                print(f"\nAnswer preview:\n{answer_preview}")
        else:
            print_result(False, f"Request failed with status {response.status_code}: {response.text}")

    except Exception as e:
        print_result(False, f"Error during Tavily test: {str(e)}")

def test_embeddings(token: str):
    """Test HuggingFace embedding functionality"""
    print_section("Testing Embedding Functionality (HuggingFace SentenceTransformer)")

    print("\nNote: This app uses HuggingFace's 'all-MiniLM-L6-v2' model, not OpenAI embeddings")
    print("The OpenAI keys in .env are not currently integrated.")

    # First, check if there are any documents
    docs_response = requests.get(
        f"{BASE_URL}/documents/",
        headers={"Authorization": f"Bearer {token}"}
    )

    if docs_response.status_code == 200:
        documents = docs_response.json()

        if not documents:
            print_result(False, "No documents found. Upload a document first to test embeddings.")
            print("\nTo test embeddings:")
            print("1. Upload a PDF document via the API or frontend")
            print("2. The document will be automatically chunked and embedded using HuggingFace model")
            print("3. You can then search using semantic similarity")
            return

        print_result(True, f"Found {len(documents)} document(s)")

        # Show document details
        for doc in documents[:3]:
            print(f"\n  - {doc.get('filename')} (Status: {doc.get('status')})")

        # Test semantic search if we have embedded documents
        embedded_docs = [d for d in documents if d.get('status') == 'embedded']

        if embedded_docs:
            print_result(True, f"{len(embedded_docs)} document(s) have embeddings")

            # Perform a search
            search_query = "What is the main topic of the document?"
            print(f"\nTesting semantic search with query: '{search_query}'")

            search_response = requests.post(
                f"{BASE_URL}/search/",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "query": search_query,
                    "max_results": 3,
                    "similarity_threshold": 0.3
                }
            )

            if search_response.status_code == 200:
                results = search_response.json()
                print_result(
                    True,
                    f"Semantic search returned {len(results)} result(s)",
                    {
                        "results_count": len(results),
                        "top_similarity": results[0].get("similarity_score") if results else None
                    }
                )

                if results:
                    print("\nTop result:")
                    print(f"  Document: {results[0].get('document_name')}")
                    print(f"  Similarity: {results[0].get('similarity_score'):.3f}")
                    print(f"  Preview: {results[0].get('chunk_text')[:150]}...")
            else:
                print_result(False, f"Search failed: {search_response.text}")
        else:
            print_result(False, "No documents have been embedded yet")
            print("\nDocuments need to be processed first. Status:")
            for doc in documents[:5]:
                print(f"  - {doc.get('filename')}: {doc.get('status')}")
    else:
        print_result(False, f"Failed to retrieve documents: {docs_response.text}")

def main():
    """Main test execution"""
    print("="*80)
    print("  UVA Research Assistant - Functionality Test")
    print("  Testing: Tavily Web Search & HuggingFace Embeddings")
    print("="*80)

    try:
        # Get authentication token
        token = get_auth_token()

        # Test Tavily
        test_tavily_search(token)

        # Test Embeddings
        test_embeddings(token)

        print_section("Test Summary")
        print("\n1. Tavily: Web search is integrated via the RAG workflow")
        print("2. Embeddings: Using HuggingFace SentenceTransformer (all-MiniLM-L6-v2)")
        print("   - NOT using OpenAI embeddings")
        print("   - OpenAI keys in .env are unused")
        print("\nIf you want to use OpenAI embeddings instead, the code needs to be modified.")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
