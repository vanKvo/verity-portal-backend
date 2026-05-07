from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .infrastructure.api.routes import auth, intake, audit
from .domain.exceptions.compliance import MappingError, ComplianceException

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Automated data reconciliation and compliance engine.",
    version="0.1.0",
)

@app.exception_handler(MappingError)
async def mapping_error_handler(request: Request, exc: MappingError):
    return JSONResponse(
        status_code=400,
        content={"error": "Validation Failed", "message": str(exc)},
    )

@app.exception_handler(ComplianceException)
async def compliance_exception_handler(request: Request, exc: ComplianceException):
    return JSONResponse(
        status_code=400,
        content={"error": "Compliance Audit Error", "message": str(exc)},
    )

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(intake.router)
app.include_router(audit.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
