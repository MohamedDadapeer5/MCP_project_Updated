#!/usr/bin/env python3
import yaml
from pathlib import Path
import sys

sys.path.insert(0, 'src')

# Load healthcare config
config_path = Path('configs/healthcare.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Resolve knowledge base path
corpus_path = config['knowledge']['corpus_path']
kb_path = config_path.parent / corpus_path
kb_path = kb_path.resolve()
print(f'KB path: {kb_path}')
print(f'KB exists: {kb_path.exists()}')

# Load knowledge base
with open(kb_path, 'r') as f:
    kb = yaml.safe_load(f)

print(f'Documents loaded: {len(kb)}')
for doc in kb[:3]:
    print(f'- {doc.get("id")}: {doc.get("title")}')

# Test search
from fastmcp_server import KnowledgeBase

kb_instance = KnowledgeBase(kb)
print(f'\nTesting search for "appointment":')
results = kb_instance.text_search("appointment", top_k=3)
print(f'Results found: {len(results)}')
for result in results:
    print(f'- {result.get("id")}: {result.get("title")}')
