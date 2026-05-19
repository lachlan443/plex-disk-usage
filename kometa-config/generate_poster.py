import os
import subprocess
import time
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from ruamel.yaml import YAML

CONFIG_DIR  = "/config"

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

POSTER_PATH = f"{CONFIG_DIR}/disk_poster.jpg"
YAML_PATH   = f"{CONFIG_DIR}/disk_usage.yml"
FONT        = "/usr/share/fonts/TTF/DejaVuSans.ttf"
FONT_BOLD   = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"

BG     = "#0f0f1a"
WHITE  = "#ffffff"
GRAY   = "#888899"
ACCENT = "#e5a00d"
BAR_BG = "#2a2a3a"

DATA_PATH   = os.environ.get("DATA_PATH",   "/data")
MOVIES_PATH = os.environ.get("MOVIES_PATH", "/data/media/movies")
TV_PATH     = os.environ.get("TV_PATH",     "/data/media/tv")


def df_stats(path):
    result = subprocess.run(["df", path], capture_output=True, text=True)
    parts    = result.stdout.splitlines()[1].split()
    total_kb = int(parts[1])
    used_kb  = int(parts[2])
    used_pct = int(parts[4].rstrip("%"))
    return used_kb * 1024, total_kb * 1024, used_pct


def du_bytes(path):
    result = subprocess.run(["du", "-sb", path], capture_output=True, text=True)
    return int(result.stdout.split()[0])


def get_stats():
    log("Checking disk usage")
    used, total, used_pct = df_stats(DATA_PATH)
    movies = du_bytes(MOVIES_PATH)
    tv     = du_bytes(TV_PATH)
    other  = max(0, used - movies - tv)

    def tb(b):  return b / (1024 ** 4)
    def pct(b): return b / total * 100

    return {
        "total_tb":   tb(total),
        "used_tb":    tb(used),
        "used_pct":   used_pct,
        "movies_tb":  tb(movies),
        "movies_pct": pct(movies),
        "tv_tb":      tb(tv),
        "tv_pct":     pct(tv),
        "other_tb":   tb(other),
        "other_pct":  pct(other),
    }


def generate_poster(used_pct):
    log("Generating poster")
    W, H = 1000, 1500
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    f_pct   = ImageFont.truetype(FONT_BOLD, 220)
    f_title = ImageFont.truetype(FONT,       60)

    draw.text((W // 2, 580), f"{used_pct}%", font=f_pct,   fill=WHITE, anchor="mm")
    draw.text((W // 2, 820), "STORAGE",      font=f_title, fill=GRAY,  anchor="mm")

    bx, by, bw, bh = 100, 920, 800, 18
    draw.rounded_rectangle([bx, by, bx + bw,                        by + bh], radius=9, fill=BAR_BG)
    draw.rounded_rectangle([bx, by, bx + int(bw * used_pct / 100), by + bh], radius=9, fill=ACCENT)

    img.save(POSTER_PATH, "JPEG", quality=90)


def update_yaml(s):
    log("Updating collection YAML")
    now     = datetime.now().strftime("%b %d %Y %H:%M")
    summary = (
        f"{s['used_pct']}% used ({s['used_tb']:.1f} / {s['total_tb']:.1f} TB) | Movies {s['movies_tb']:.1f} TB ({s['movies_pct']:.0f}%) · TV {s['tv_tb']:.1f} TB ({s['tv_pct']:.0f}%) · Other {s['other_tb']:.1f} TB ({s['other_pct']:.0f}%)\n"
        f"Updated: {now}"
    )

    yaml = YAML()
    yaml.preserve_quotes = True
    with open(YAML_PATH, "r") as f:
        data = yaml.load(f)

    data["collections"]["Disk Usage"]["summary"] = summary

    with open(YAML_PATH, "w") as f:
        yaml.dump(data, f)


def next_sleep_secs():
    times_str = os.environ.get("KOMETA_TIME", "00:00, 06:00, 12:00, 18:00")
    now       = datetime.now()
    candidates = []
    for t in times_str.split(","):
        h, m = map(int, t.strip().split(":"))
        base = now.replace(hour=h, minute=m, second=0, microsecond=0)
        candidates += [base, base + timedelta(days=1)]
    # Require next run to be >5 min away so wake_at is always in the future
    next_run = min(r for r in candidates if r > now + timedelta(minutes=5))
    wake_at  = next_run - timedelta(minutes=5)
    return (wake_at - now).total_seconds(), wake_at


while True:
    s = get_stats()
    generate_poster(s["used_pct"])
    update_yaml(s)
    log(
        f"Done: {s['used_pct']}% used ({s['used_tb']:.1f} / {s['total_tb']:.1f} TB) | "
        f"Movies {s['movies_tb']:.1f} TB  TV {s['tv_tb']:.1f} TB  Other {s['other_tb']:.1f} TB"
    )

    secs, wake_at = next_sleep_secs()
    log(f"Sleeping until {wake_at.strftime('%Y-%m-%d %H:%M')} ({secs / 3600:.1f}h)")
    time.sleep(secs)
