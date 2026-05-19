FROM python:3.12-alpine3.23

RUN apk add --no-cache ttf-dejavu curl

ARG SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64
ARG SUPERCRONIC_SHA1SUM=cd48d45c4b10f3f0bfdd3a57d054cd05ac96812b
RUN curl -fsSLO "$SUPERCRONIC_URL" \
    && echo "${SUPERCRONIC_SHA1SUM}  supercronic-linux-amd64" | sha1sum -c - \
    && chmod +x supercronic-linux-amd64 \
    && mv supercronic-linux-amd64 /usr/local/bin/supercronic

RUN pip install --no-cache-dir pillow ruamel.yaml

COPY entrypoint.sh /entrypoint.sh
COPY kometa-config/generate_poster.py /app/generate_poster.py
RUN chmod +x /entrypoint.sh

ENV TZ=UTC
ENV KOMETA_TIME="55 23,5,11,17 * * *"
ENV DATA_PATH=/data
ENV MOVIES_PATH=/data/media/movies
ENV TV_PATH=/data/media/tv

ENTRYPOINT ["/entrypoint.sh"]
