---
title: "Local API Endpoint Contract Map"
date: "2026-05-28"
api_version: "v3"
status: "Active"
---

# API Contract: Local Ingestion Service Map

This contract specifies the input and output parameters, authentication schemas, and performance indicators for our local RAG ingestion REST endpoint.

## 1. Endpoint Overview
All local search queries, vector updates, and RAG configuration changes route through this gateway:

*   **Endpoint URI**: `/api/v3/ingestion/indexing/process`
*   **HTTP Method**: `POST`
*   **Content-Type**: `application/json`
*   **Authentication**: `Bearer token`

## 2. API Request Structure
Payload must define target file paths, indexing configurations, and fallback circuit-breaker priorities.

```json
{
  "profile_name": "testing-profile",
  "ingestion_path": "./testing_data",
  "engine_options": {
    "chunk_size": 400,
    "chunk_overlap": 80,
    "force_reload": true
  },
  "cascade_priority": [
    "gemini",
    "groq",
    "ollama"
  ]
}
```

## 3. API Response Structure
A successful status code (`200 OK`) returns a detailed ingestion statistics block matching our Rich output panel parameters:

```json
{
  "status": "success",
  "timestamp": "2026-05-28T14:10:00Z",
  "data": {
    "files_loaded": 1,
    "new_chunks_created": 1,
    "total_indexed_chunks": 1,
    "db_path": "/home/premsaik/.local/share/adviser/testing-profile/chroma_db"
  }
}
```
