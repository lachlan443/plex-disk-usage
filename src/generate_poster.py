import os
import subprocess
import sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from ruamel.yaml import YAML


def log(level, msg):
    print(f"[{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}] [{level}] {msg}", flush=True)

def info(msg):  log("INFO",  msg)
def error(msg): log("ERROR", msg)


CONFIG_DIR  = "/config"
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
    if result.returncode != 0:
        raise RuntimeError(f"df failed for {path}: {result.stderr.strip()}")
    parts    = result.stdout.splitlines()[1].split()
    total_kb = int(parts[1])
    used_kb  = int(parts[2])
    used_pct = int(parts[4].rstrip("%"))
    return used_kb * 1024, total_kb * 1024, used_pct


def du_bytes(path):
    result = subprocess.run(["du", "-sb", path], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"du failed for {path}: {result.stderr.strip()}")
    return int(result.stdout.split()[0])


def get_stats():
    info("Checking disk usage")
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
    info("Generating poster")
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
    info("Updating collection YAML")
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


try:
    s = get_stats()
    generate_poster(s["used_pct"])
    update_yaml(s)
    info(
        f"Done: {s['used_pct']}% used ({s['used_tb']:.1f} / {s['total_tb']:.1f} TB) | "
        f"Movies {s['movies_tb']:.1f} TB  TV {s['tv_tb']:.1f} TB  Other {s['other_tb']:.1f} TB"
    )
except Exception as e:
    error(str(e))
    sys.exit(1)
