## Change Management Assistant — Copilot Instructions

Purpose: give AI coding agents the minimal, high-value knowledge to be productive in this repo.

- Project entry: `app.py` is the single, authoritative app file (Flask + RAG + Analytics). Read it first.
- Key folders: `docs/` (PDF SOPs for RAG), `templates/` (UI: `index.html`, `analytics.html`), `static/` (JS/CSS), and root CSV logs (`query_logs.csv`, `feedback_logs.csv`, `escalation_logs.csv`).

- Environment & run
  - Required env: `GOOGLE_API_KEY` (checked at startup). Optional ServiceNow creds: `SERVICENOW_INSTANCE`, `SERVICENOW_USER`, `SERVICENOW_PASSWORD`.
  - Local run: `python app.py` (Flask host 0.0.0.0:5000). The app calls `initialize_rag_chain()` at startup — this loads PDFs from `docs/` and instantiates embeddings (first run may download models).
  - Install: `pip install -r requirements.txt` (see `README.md`). `.env` is used for keys.

- Patterns & conventions to follow
  - Single-file server: most logic is in `app.py`. Keep changes small and local unless migrating to modules.
  - Mock vs real integrations: many ServiceNow helpers (e.g., `get_servicenow_stats`, `get_ticket_details`, `get_pending_approvals`) use mock data when required env vars are missing or when ticket IDs start with `MOCK-`. Respect these guards when editing or adding tests.
  - Intent parsing: simple keyword heuristics and regex are used (example ticket regex: `r"\b(cr|chg|mock)[-]?(\d+)\b"`). Preserve intent-routing behavior or update all related branches consistently.
  - Low-confidence handling: responses containing phrases like "i don't know" are marked Unanswered in `query_logs.csv`. Avoid silent changes that remove these triggers.

- Data flows and integration points
  - RAG: `initialize_rag_chain()` loads PDFs via `PyPDFDirectoryLoader` → chunking (`RecursiveCharacterTextSplitter`) → `Chroma` vector store → `llm` (Google Gemini). Add docs to `docs/` to change knowledge base.
  - ServiceNow: HTTP calls use basic auth to endpoints like `/api/now/stats/change_request` and `/api/now/table/change_request`. If ServiceNow env vars are missing, functions return mock JSON for UI charts.
  - Logging & analytics: interactions, feedback, and escalations write CSV files in the repo root. Analytics page (`/analytics`) reads these CSVs.
  - Frontend: `static/script.js` drives chat interactions calling `/ask`, `/feedback`, `/escalate` endpoints. Keep JSON shapes stable (chart responses have `type`, `text`, `chart_type`, `chart_data`).

- Testing / debugging tips
  - Local quick tests: to exercise ServiceNow flows without credentials, use `MOCK-` ticket IDs (e.g., `MOCK-1024`) or remove ServiceNow env vars to force mock data.
  - RAG tests: add 1–2 small PDFs to `docs/` and restart. Watch console for "Processed N document chunks." If no docs found, RAG initialization is skipped.
  - Logs: inspect `query_logs.csv` and `escalation_logs.csv` for reproduction artifacts. Analytics reads these files directly.

- Safe edits guidance for AI agents
  - Do not commit credentials or `.env`. The code relies on the presence/absence of env vars — preserve that branching.
  - When changing intent heuristics, update `ask_question()` routing and any helper functions together. Add unit-like smoke checks (small script or test) that exercise each intent.
  - Prefer non-invasive refactors: split `app.py` into modules only with tests and a migration plan (update `README` and imports).

- Useful file examples
  - `app.py`: intent parsing, ServiceNow fallbacks, RAG initialization, and analytics rendering.
  - `README.md`: run/install guidance and feature overview.
  - `templates/analytics.html` and `static/script.js`: expected JSON shapes for chart and chat responses.

If anything above is unclear or you want instructions to be more or less detailed (examples, tests to add, or a refactor plan), tell me which section to expand and I will update this file.
