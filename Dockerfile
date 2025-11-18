FROM python:3.13-slim

LABEL maintainer="Marline khavele khavelemarline@gmail.com"

# Install build dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    curl \
    && apt-get clean

# Install Poetry 
RUN curl -sSL https://install.python-poetry.org | python3 -
# Ensure Poetry is added to PATH
ENV PATH="/root/.local/bin:$PATH"

# Verify that Poetry is installed
RUN poetry --version

# Set working directory
WORKDIR /app/

# Copy necessary project files
COPY ./pyproject.toml ./poetry.lock* ./Makefile /app/

# Install dependencies via Poetry
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

# Copy the source code into the container
COPY ./src /app/

# Set Python path (optional)
ENV PYTHONPATH=/app

# Set the command to run the application (with default settings)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "app.main:app"]   