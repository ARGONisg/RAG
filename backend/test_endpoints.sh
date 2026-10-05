#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────────────
# test_endpoints.sh — Quick smoke tests for the RAG backend
#
# Prerequisites:
#   1.  pip install -r requirements.txt
#   2.  The backend is running: uvicorn main:app --reload  (from /backend)
#
# Usage:
#   chmod +x test_endpoints.sh
#   ./test_endpoints.sh
# ────────────────────────────────────────────────────────────────────────────

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
DIVIDER="════════════════════════════════════════════════════════════════"

# ── Colors ─────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RESET='\033[0m'

echo -e "${CYAN}${DIVIDER}${RESET}"
echo -e "${CYAN}  RAG Backend — Endpoint Smoke Tests${RESET}"
echo -e "${CYAN}${DIVIDER}${RESET}"
echo ""

# ── 1. Health Check ────────────────────────────────────────────────────────
echo -e "${GREEN}▶ 1. Health Check (GET /health)${RESET}"
curl -s "${BASE_URL}/health" | python3 -m json.tool
echo ""

# ── 2. Document Upload ────────────────────────────────────────────────────
echo -e "${GREEN}▶ 2. Document Upload (POST /api/v1/documents/upload)${RESET}"

# Create a tiny dummy PDF (minimal valid PDF structure)
DUMMY_PDF="/tmp/test_upload.pdf"
printf '%%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%%%EOF' > "${DUMMY_PDF}"

curl -s -X POST "${BASE_URL}/api/v1/documents/upload" \
  -F "file=@${DUMMY_PDF};type=application/pdf" \
  | python3 -m json.tool
echo ""

# ── 3. Chat SSE Stream (no history) ───────────────────────────────────────
echo -e "${GREEN}▶ 3. Chat Stream — Fresh query (POST /api/v1/chat)${RESET}"
echo "   Streaming SSE events:"
echo ""

curl -s -N -X POST "${BASE_URL}/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the policy on leave?",
    "session_id": "test-session-001",
    "history": []
  }'
echo ""
echo ""

# ── 4. Chat SSE Stream (with history) ─────────────────────────────────────
echo -e "${GREEN}▶ 4. Chat Stream — Follow-up with history (POST /api/v1/chat)${RESET}"
echo "   Streaming SSE events:"
echo ""

curl -s -N -X POST "${BASE_URL}/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "And what about sick leave?",
    "session_id": "test-session-001",
    "history": [
      {"role": "user", "content": "What is the policy on leave?"},
      {"role": "assistant", "content": "Employees are entitled to 24 days of paid annual leave per calendar year."}
    ]
  }'
echo ""
echo ""

# ── 5. Rejected file type ─────────────────────────────────────────────────
echo -e "${GREEN}▶ 5. Upload rejection — non-PDF file${RESET}"
echo "test" > /tmp/test_upload.txt
curl -s -X POST "${BASE_URL}/api/v1/documents/upload" \
  -F "file=@/tmp/test_upload.txt;type=text/plain" \
  | python3 -m json.tool
echo ""

echo -e "${CYAN}${DIVIDER}${RESET}"
echo -e "${CYAN}  All tests complete.${RESET}"
echo -e "${CYAN}${DIVIDER}${RESET}"
