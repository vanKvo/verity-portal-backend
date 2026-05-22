from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.verity_portal.core.config import get_settings
from src.verity_portal.identity.router import router as identity_router
from src.verity_portal.intake.router import router as intake_router
from src.verity_portal.audit.router import router as audit_router
from src.verity_portal.itar.router import router as itar_router
from src.verity_portal.data_hub.router import router as data_hub_router
from src.verity_portal.core.exceptions import MappingError
from src.verity_portal.audit.exceptions import ComplianceError

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

@app.exception_handler(ComplianceError)
async def compliance_exception_handler(request: Request, exc: ComplianceError):
    return JSONResponse(
        status_code=400,
        content={"error": "Compliance Audit Error", "message": str(exc)},
    )

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(identity_router)
app.include_router(intake_router)
app.include_router(audit_router)
app.include_router(itar_router)
app.include_router(data_hub_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.verity_portal.main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
