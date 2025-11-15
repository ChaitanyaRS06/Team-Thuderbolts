#!/usr/bin/env python3
"""
Test script for Tavily API and Sentence Transformers embeddings
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_tavily_api():
    """Test Tavily web search API"""
    print("\n=== Testing Tavily API ===")
    try:
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key or api_key == "your_tavily_api_key_here":
            print("❌ TAVILY_API_KEY not set in .env file")
            return False

        client = TavilyClient(api_key=api_key)
        response = client.search("what is AI?", max_results=2)

        if response and 'results' in response:
            print(f"✅ Tavily API working! Found {len(response['results'])} results")
            for idx, result in enumerate(response['results'][:2], 1):
                print(f"  {idx}. {result['title']}")
            return True
        else:
            print("❌ Tavily API returned unexpected format")
            return False
    except Exception as e:
        print(f"❌ Tavily API error: {str(e)}")
        return False

async def test_sentence_transformers():
    """Test Sentence Transformers embeddings"""
    print("\n=== Testing Sentence Transformers (Local Embeddings) ===")
    try:
        from sentence_transformers import SentenceTransformer

        print("Loading model 'all-MiniLM-L6-v2' (first time will download ~80MB)...")
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Test embedding generation
        test_texts = [
            "This is a test sentence.",
            "AI and machine learning are transforming research."
        ]

        embeddings = model.encode(test_texts)

        print(f"✅ Embedding generation working!")
        print(f"  - Model: all-MiniLM-L6-v2")
        print(f"  - Embedding dimension: {len(embeddings[0])}")
        print(f"  - Generated {len(embeddings)} embeddings")
        return True
    except Exception as e:
        print(f"❌ Sentence Transformers error: {str(e)}")
        return False

async def test_anthropic_api():
    """Test Anthropic Claude API"""
    print("\n=== Testing Anthropic Claude API ===")
    try:
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your_anthropic_api_key_here":
            print("❌ ANTHROPIC_API_KEY not set in .env file")
            return False

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Say hello in one sentence."}
            ]
        )

        if message and message.content:
            print(f"✅ Anthropic API working!")
            print(f"  Response: {message.content[0].text}")
            return True
        else:
            print("❌ Anthropic API returned unexpected format")
            return False
    except Exception as e:
        print(f"❌ Anthropic API error: {str(e)}")
        return False

async def main():
    print("=" * 60)
    print("API & Service Tests for UVA AI Research Assistant")
    print("=" * 60)

    results = {
        "Sentence Transformers": await test_sentence_transformers(),
        "Tavily API": await test_tavily_api(),
        "Anthropic API": await test_anthropic_api()
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}: {'PASS' if status else 'FAIL'}")

    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - System ready to use!")
    else:
        print("❌ SOME TESTS FAILED - Check .env file and API keys")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
