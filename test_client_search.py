#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, 'clients')
from gemini_client import QABotMCPClient

async def test():
    try:
        client = QABotMCPClient()
    except RuntimeError as e:
        print(f"Error: {e}")
        return
    
    if not await client.initialize():
        print("Failed to connect to server")
        return
    
    # Select healthcare industry
    if await client.select_industry('healthcare'):
        # Test search directly
        print("\n=== Testing search directly ===")
        search_result = await client._search_knowledge("book an appointment")
        if search_result.get('results'):
            print(f"Found {len(search_result['results'])} results:")
            for result in search_result['results'][:2]:
                print(f"- {result.get('id')}: {result.get('title')}")
        else:
            print("No results found")

asyncio.run(test())
