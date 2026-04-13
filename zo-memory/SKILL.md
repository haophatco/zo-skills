---
name: zo-memory
description: "Persistent conversation memory for Zo using mem0. Automatically remembers key facts, preferences, and context from conversations so the user never has to repeat themselves. Use when starting a new conversation to load context, and after meaningful exchanges to save new memories."
compatibility: "Created for Zo Computer"
metadata:
  author: hana.zo.computer
  version: "1.0"
---

# Zo Memory — Persistent Conversation Memory

## Overview
This skill gives Zo persistent memory across conversations using mem0 + Ollama (fully local, no external API keys). Memories are stored in a local ChromaDB vector database and processed by a local LLM.

## Architecture
- **LLM**: OpenAI (gpt-4.1-mini) — extracts and deduplicates memories
- **Embeddings**: OpenAI (text-embedding-3-small) — semantic search
- **Vector Store**: ChromaDB (local at ~/.zo-memory/chroma_db_v2)
- **History**: SQLite (at ~/.zo-memory/history_v2.db)

## When to Use

### At the START of a conversation:
Search for relevant memories based on what the user is asking about:
```bash
python3 /home/workspace/Skills/zo-memory/scripts/memory.py search --user hana --query "<topic the user is discussing>"
```

### At the END of a meaningful exchange:
Save important facts, decisions, preferences, or context:
```bash
python3 /home/workspace/Skills/zo-memory/scripts/memory.py add --user hana --text "<summary of key information from the conversation>"
```

### What to save:
- User preferences and working style
- Business decisions and rationale
- Key facts about projects, people, companies
- KPIs, targets, deadlines mentioned
- Feedback on how Zo should behave
- Important context that would be useful in future conversations

### What NOT to save:
- Ephemeral task details (one-off calculations, temp files)
- Information already in workspace files
- Raw data or long text dumps

## Commands

```bash
# Add a memory
python3 scripts/memory.py add --user hana --text "User prefers Vietnamese for business reports"

# Search memories (semantic search)
python3 scripts/memory.py search --user hana --query "report preferences"

# List all memories
python3 scripts/memory.py list --user hana

# Delete a specific memory
python3 scripts/memory.py delete --id <memory_id>

# Check stats
python3 scripts/memory.py stats --user hana
```

## Dependencies
- mem0ai (pip)
- chromadb (pip)  
- Ollama service (user service: ollama, port 11434)
- Models: qwen2.5:3b, nomic-embed-text
