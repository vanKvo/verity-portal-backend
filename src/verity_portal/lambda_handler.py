"""AWS Lambda handler entrypoint using Mangum.

Wraps the FastAPI application to translate AWS API Gateway HTTP events
into standard ASGI HTTP transactions.
"""
from mangum import Mangum
from src.verity_portal.main import app

handler = Mangum(app, lifespan="off")
