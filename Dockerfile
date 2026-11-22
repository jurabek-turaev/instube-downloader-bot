FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# yt-dlp needs a JavaScript runtime (deno) to solve YouTube's player
# challenges; without it YouTube formats are missing or return 403.
COPY --from=denoland/deno:bin-2.9.8 /deno /usr/local/bin/deno

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock* ./

RUN uv sync --no-cache

COPY . .

RUN mkdir -p downloads

CMD [ ".venv/bin/python", "main.py" ]