#!/usr/bin/env python3
import yaml
from pathlib import Path
import sys

sys.path.insert(0, 'src')
from fastmcp_server import KnowledgeBase

# Load knowledge base
kb_path = Path('knowledge/healthcare-kb.yaml')
with open(kb_path, 'r') as f:
    kb = yaml.safe_load(f)

kb_instance = KnowledgeBase(kb)

# Debug: show all documents
print("All documents:")
for i, doc in enumerate(kb):
    print(f"{i}: {doc.get('id')} - {doc.get('title')}")
    print(f"   Content: {doc.get('content')[:80]}...")
    print()

# Debug: show index for "appointment"
query = "appointment"
query_tokens = kb_instance._tokenize(query)
print(f"Query tokens: {query_tokens}")
print()

# Check which documents contain these tokens
for token in query_tokens:
    if token in kb_instance.index:
        doc_ids = kb_instance.index[token]
        print(f"Token '{token}' found in documents: {doc_ids}")
        for doc_id in doc_ids:
            print(f"  - {kb[doc_id].get('id')}: {kb[doc_id].get('title')}")
    else:
        print(f"Token '{token}' NOT found in index")

print("\nSearch results for 'appointment':")
results = kb_instance.text_search("appointment", top_k=5)
for result in results:
    print(f"- {result.get('id')}: {result.get('title')}")
