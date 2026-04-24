from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Automated data reconciliation and compliance engine.",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
