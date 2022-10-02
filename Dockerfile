# syntax=docker/dockerfile:1
FROM python:3.10-slim@sha256:502f6626d909ab4ce182d85fcaeb5f73cf93fcb4e4a5456e83380f7b146b12d3
# FROM python:3.11-rc-slim -- no lxml wheel yet

ENV PYTHONUNBUFFERED=1

RUN ["python", "-m", "pip", "install", "--upgrade", "pip"]

# Copy and install requirements separately to let Docker cache layers
COPY requirements.txt /code/requirements.txt

WORKDIR /code

RUN ["pip", "install", "-r", "requirements.txt"]

ENTRYPOINT ["./test_paths.py"]
CMD ["--help"]
