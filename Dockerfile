FROM python:3.12-alpine3.23

RUN apk add --no-cache ttf-dejavu curl

ARG SUPERCRONIC_VERSION=v0.2.29
ARG TARGETARCH
RUN case "${TARGETARCH}" in \
      amd64) SHA1=cd48d45c4b10f3f0bfdd3a57d054cd05ac96812b ;; \
      arm64) SHA1=512f6736450c56555e01b363144c3c9d23abed4c ;; \
      *) echo "Unsupported architecture: ${TARGETARCH}" && exit 1 ;; \
    esac \
    && curl -fsSL "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-${TARGETARCH}" \
       -o /usr/local/bin/supercronic \
    && echo "${SHA1}  /usr/local/bin/supercronic" | sha1sum -c - \
    && chmod +x /usr/local/bin/supercronic

RUN pip install --no-cache-dir pillow ruamel.yaml

COPY entrypoint.sh /entrypoint.sh
COPY src/generate_poster.py /app/generate_poster.py
RUN chmod +x /entrypoint.sh

ENV TZ=UTC
ENV KOMETA_TIME="55 23,5,11,17 * * *"
ENV DATA_PATH=/data
ENV MOVIES_PATH=/data/media/movies
ENV TV_PATH=/data/media/tv

ENTRYPOINT ["/entrypoint.sh"]
