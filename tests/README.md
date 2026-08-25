# Tests & Utility Scripts

This folder contains test scripts and database utility scripts for the OURS TTD project.

## Test Scripts

| File | Purpose |
|------|---------|
| `test_features.py` | Integration tests for queue, chat, transport features |
| `test_chat_api.py` | Tests for the `/api/chat` AI assistant endpoint |
| `test_search.py` | Tests for transport/location search |
| `test_transport_fallback.py` | Tests for transport fallback logic |
| `test_gemini.py` | Tests for Gemini AI connection |

## Utility / Check Scripts

| File | Purpose |
|------|---------|
| `check_queue_api.py` | Quick manual check of queue API response |
| `check_routes.py` | Quick check of transport routes API |
| `find_guest_user.py` | Find/remove guest accounts from database |
| `list_all_users.py` | List all users in the database |
| `reseed_transport.py` | Re-seed transport route data in database |

## Running Tests

Make sure the server is running first:

```bash
uvicorn backend.main:app --reload --port 8001
```

Then from the project root:

```bash
python tests/test_features.py
python tests/test_chat_api.py
```
