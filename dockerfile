FROM python:3.11.5-bookworm

# Install pipenv
RUN set -eux; \
	apt-get update; \
	apt-get install -y --no-install-recommends \
		pipenv \
	; \
	rm -rf /var/lib/apt/lists/*

# Configure workdir
RUN mkdir /app
WORKDIR /app

# Prepare Python runtime environment
COPY Pipfile.lock Pipfile.lock
RUN set -eux; \
    pipenv sync; \
    pipenv --clear

# Setup application files
COPY . .

# Pre-load model data
RUN pipenv run python -m ner_seg --help

ENTRYPOINT [ "pipenv", "run", "python", "-m", "ner_seg", "-i", "/input" ]
CMD [ "--help" ]
