# Plex Disk Usage Collection

Displays live server storage stats as a collection inside Plex using [Kometa](https://kometa.wiki), visible to all users without needing access to any external dashboard.

## What it looks like

![Plex library view](disk_poster.png)

In your Plex Movies and TV libraries, a pinned collection called **Disk Usage** appears at the top. Opening the collection shows a breakdown in the description:

```
73% used (10.1 / 14.4 TB) | Movies 3.1 TB (22%) · TV 5.5 TB (38%) · Other 1.4 TB (10%)
Updated: May 15 2026 18:00
```

## How it works

A sidecar container runs alongside Kometa. It reads `KOMETA_TIME` from the environment, sleeps until 5 minutes before each scheduled run, then updates the collection's cover image and description. Kometa then runs as normal and pushes the changes to Plex.

## Repository structure

```
kometa-disk-usage/
├── kometa-config/
│   ├── generate_poster.py   # sidecar script. runs inside the sidecar container
│   ├── disk_usage.yml       # Kometa collection definition
│   └── disk_poster.jpg      # generated poster example
├── compose.yaml             # sidecar service. merge into your existing compose file
└── disk_poster.png          # Plex library screenshot
```

---

## Setup

### Prerequisites

- Docker
- Kometa's config must be a **bind mount** (not a named volume) so the sidecar can share the same directory:
  ```yaml
  volumes:
    - /path/to/kometa/config:/config  # bind mount, not a named volume
  ```
- Your media must be on a single mount point so `df` can report a single usage figure

### 1. Copy the Kometa config files

Copy `generate_poster.py` and `disk_usage.yml` from `kometa-config/` into the directory you have bind mounted as `/config` inside your Kometa container.

### 2. Register the collection with Kometa

In your Kometa `config.yml`, add `disk_usage.yml` as a collection file for each library you want it to appear in:

```yaml
libraries:
  Movies:
    collection_files:
      - file: /config/disk_usage.yml
      # ... your other collection files

  TV:
    collection_files:
      - file: /config/disk_usage.yml
      # ... your other collection files
```

### 3. Add the sidecar to your compose file

Add the `disk-stats` service alongside your existing `kometa` service:

```yaml
  disk-stats:
    image: python:alpine
    container_name: kometa-sidecar-disk-stats
    environment:
      - TZ=${TZ}
      - KOMETA_TIME=${KOMETA_TIME}
      - DATA_PATH=/data                        # root mount point for total usage
      - MOVIES_PATH=/data/media/movies         # path to your movies folder
      - TV_PATH=/data/media/tv                 # path to your TV folder
    volumes:
      - /path/to/kometa/config:/config    # same bind mount as your Kometa container
      - /data:/data:ro                    # your media location
    command: >
      sh -c "apk add --no-cache ttf-dejavu &&
             pip install pillow ruamel.yaml --quiet --no-cache-dir &&
             python3 /config/generate_poster.py"
    restart: unless-stopped
```

### 4. Start the sidecar

```bash
docker compose up -d disk-stats
```

```bash
docker logs kometa-sidecar-disk-stats
```

```
[disk-stats] 73% used | Movies 3.1TB · TV 5.5TB · Other 1.4TB
[disk-stats] Next update at 23:55 (5.4h)
```

### 5. Run Kometa (optional)

If you don't want to wait for Kometa's next scheduled run, you can trigger a manual collections-only run to get the collection into Plex immediately:

```bash
docker exec -it -e KOMETA_RUN=True kometa python3 kometa.py --run --collections-only
```

---

## Configuration

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `DATA_PATH` | `/data` | Root mount point. used for total disk usage via `df` |
| `MOVIES_PATH` | `/data/media/movies` | Path to movies folder for size breakdown |
| `TV_PATH` | `/data/media/tv` | Path to TV folder for size breakdown |
| `KOMETA_TIME` | `00:00, 06:00, 12:00, 18:00` | Kometa's run schedule. sidecar updates 5 min before each run |
