from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cori.api import generate, questionnaire

app = FastAPI(title="Cori", description="AI coauthor for personalized cover letters")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")
api_router.include_router(questionnaire.router, tags=["questionnaire"])
api_router.include_router(generate.router, tags=["cover-letter"])
app.include_router(api_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("cori.main:app", host="0.0.0.0", port=8000, reload=True)
