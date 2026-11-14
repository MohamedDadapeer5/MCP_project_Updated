#!/usr/bin/env python3
import yaml
from pathlib import Path

# Load knowledge base directly
kb_path = Path('knowledge/healthcare-kb.yaml')
with open(kb_path, 'r') as f:
    kb = yaml.safe_load(f)

print("First document:")
doc = kb[0]
print(f"ID: {doc.get('id')}")
print(f"Title: {doc.get('title')}")
print(f"Content: {doc.get('content')}")
print(f"Content type: {type(doc.get('content'))}")

# Check if tokenization works
import re
content = doc.get('content', '')
tokens = re.findall(r'\w+', content.lower())
print(f"\nTokens from content: {tokens}")
print(f"Contains 'appointment': {'appointment' in tokens}")
