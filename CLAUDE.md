# Cori

AI coauthor system that generates personalized cover letters.

## Stack

- Python 3.12+, FastAPI, Pydantic
- Package manager: uv
- Linter: ruff (line-length 100)

## Project structure

```
cori/                  # main package
├── main.py            # FastAPI app entrypoint
├── api/               # route handlers
├── models/            # Pydantic request/response models
├── services/          # business logic (plain async functions, not classes)
└── core/              # config and settings
```

## Running

```
uv run uvicorn cori.main:app --reload
```

## Conventions

- Services are plain async functions, not classes
- Use `uv add` to manage dependencies
- Keep endpoints thin — business logic goes in `services/`
- No premature abstractions — add infrastructure (DI, shared clients, etc.) when actually needed
