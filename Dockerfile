# Stage 1: Build stage (holds compiler tools and Poetry)
FROM public.ecr.aws/lambda/python:3.12 AS builder

# Install poetry and the export plugin for dependency resolution
RUN pip install --no-cache-dir poetry poetry-plugin-export

# Copy dependency specifications
COPY pyproject.toml poetry.lock ./

# Export dependencies to requirements.txt and install them to a target directory
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes \
    && pip install --no-cache-dir --target /dependencies -r requirements.txt

# Stage 2: Clean runtime stage (copied into Lambda)
FROM public.ecr.aws/lambda/python:3.12

# Copy only the compiled dependencies from Stage 1
COPY --from=builder /dependencies ${LAMBDA_TASK_ROOT}

# Copy application source code
COPY src ${LAMBDA_TASK_ROOT}/src

# Expose the Mangum handler entry point
CMD [ "src.verity_portal.lambda_handler.handler" ]
