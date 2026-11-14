#!/usr/bin/env python3
import httpx
import json

# Test the search endpoint
response = httpx.post('http://localhost:8000/search', json={'industry': 'healthcare', 'query': 'appointment'})
data = response.json()
print('Search results for "appointment":')
if 'results' in data:
    for i, result in enumerate(data['results'][:3], 1):
        title = result.get('title', 'Unknown')
        doc_id = result.get('id', 'No ID')
        print(f'{i}. {doc_id}: {title}')
else:
    print(json.dumps(data, indent=2))
