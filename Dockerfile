# retrosynth studio in a container (any OS with Docker):
#   docker build -t retrosynth .
#   docker run --rm -p 127.0.0.1:5177:5177 -v "$PWD/songs:/data/songs" -v "$PWD/output:/data/output" retrosynth
# then open http://localhost:5177
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

# songs and exports live in /data (mount it to keep them)
WORKDIR /data
EXPOSE 5177
# 0.0.0.0 so the published port reaches the server; requests are still only accepted
# for "localhost" host names and with the per-session token.
CMD ["retrosynth", "studio", "--host", "0.0.0.0", "--no-browser"]
