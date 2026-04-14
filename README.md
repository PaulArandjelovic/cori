[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/linting-Ruff-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

# Cori

AI coauthor system that generates personalized cover letters. Built as a two-step pipeline: a dynamic questionnaire tailored to the job posting, followed by cover letter generation informed by the candidate's answers and live company research.

## Setup

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Add your Gemini API key to .env
```

## Running

```bash
uv run uvicorn cori.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `/docs`.

## API

### `POST /api/questionnaire`

Generates a set of questions for the candidate. Four base identity questions are always included; four additional questions are dynamically generated from the job posting using Gemini.

```json
{
  "job_description": "We are looking for a backend engineer...",
  "company_name": "Acme Corp"
}
```

### `POST /api/cover-letter/generate`

Researches the company via Google Search grounding, then generates a personalized cover letter using the candidate's answers and the research context.

```json
{
  "company_name": "Acme Corp",
  "job_title": "Backend Engineer",
  "job_url": "https://example.com/jobs/123",
  "job_description": "We are looking for a backend engineer...",
  "answers": {
    "full_name": "Jane Doe",
    "current_role": "Software Engineer",
    "key_achievement": "Led migration to event-driven architecture..."
  },
  "tone": "formal"
}

```

Returns the cover letter in markdown along with the company research context and sources.

### `GET /healthz`

Health check endpoint.

## Architecture

```
cori/
├── main.py              # FastAPI app, CORS, routing
├── config.py            # Gemini client + settings (from .env)
├── api/                 # Thin route handlers
│   ├── questionnaire.py # POST /api/questionnaire
│   └── generate.py      # POST /api/cover-letter/generate
├── models/              # Pydantic request/response schemas
│   ├── fields.py        # Shared type aliases (CompanyName, JobDescription)
│   ├── questionnaire.py # Question, QuestionnaireRequest/Response
│   ├── cover_letter.py  # GenerateRequest, CoverLetterResponse
│   └── research.py      # ResearchResult, CompanyContext, Source
└── services/            # Business logic (async functions, not classes)
    ├── questionnaire.py # Base + dynamic question generation
    ├── research.py      # Company research via Gemini + Google Search
    └── generator.py     # Cover letter generation
```

### Design decisions

- **Gemini Google Search grounding** for company research instead of a separate search API. This keeps the dependency count low and lets the model decide what's relevant in a single pass. The structured output schema (`ResearchResult`) acts as an implicit filter — only the fields we care about are extracted.
- **Base + dynamic questions** — four fixed identity questions ensure we always collect essentials; four AI-generated questions are tailored to the specific job posting. If Gemini is unavailable, generic fallback questions are used so the flow never breaks.
- **Company context is selectively injected** into the generation prompt. Only populated fields are included, and the prompt instructs the model to reference company details naturally rather than listing them. This avoids overusing irrelevant context.
- **Temperature is tuned per task** — 0.2 for research (factual), 0.3 for question generation (semi-deterministic), 0.7 for cover letter writing (creative).
- **Graceful degradation** throughout. Research and questionnaire services catch API errors and return safe fallbacks rather than crashing.
