#!/usr/bin/env python3
"""Builds card.svg from config.json. Standard library only.

Run from anywhere:  python3 scripts/build.py
In config.json, set "repos" and/or "commits" to "auto" to pull live numbers
from the GitHub API (needs internet; uses GITHUB_TOKEN if present).
"""
import json, os, sys, datetime, urllib.request
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "scripts", "assets")
cfg = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
ACC = cfg.get("accent", "#33ff66")

# ---------- live numbers ----------
def api(path):
    req = urllib.request.Request("https://api.github.com" + path, headers={"User-Agent": "profile-card"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def resolve(key, fetch, fallback):
    v = cfg.get(key, fallback)
    if v != "auto":
        return v
    try:
        return fetch()
    except Exception as e:
        print(f"[warn] could not fetch {key}: {e}", file=sys.stderr)
        return cfg.get(key + "_fallback", fallback if fallback != "auto" else "?")

user = cfg["github_user"]
repos = resolve("repos", lambda: api(f"/users/{user}")["public_repos"], 51)
commits = resolve("commits", lambda: api(f"/search/commits?q=author:{user}&per_page=1")["total_count"], 661)

# ---------- uptime ----------
sy, sm, sd = map(int, cfg["start_date"].split("-"))
now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)  # Africa/Lagos
y, m, d = now.year - sy, now.month - sm, now.day - sd
if d < 0:
    m -= 1
    prev_month_days = (datetime.date(now.year, now.month, 1) - datetime.timedelta(days=1)).day
    d += prev_month_days
if m < 0:
    y -= 1
    m += 12
uptime = f"{y}y {m}m {d}d"

subs = {"uptime": uptime, "repos": repos, "commits": commits}
def fill(s):
    for k, v in subs.items():
        s = s.replace("{" + k + "}", str(v))
    return s

# ---------- assets ----------
rd = lambda n: open(os.path.join(ASSETS, n), encoding="utf-8").read()
font_r, font_b = rd("font-regular.b64").strip(), rd("font-bold.b64").strip()
portrait = rd("portrait.txt").split("\n")
wanted = json.loads(rd("wanted.json"))

# ---------- geometry (matches the design artboard) ----------
W, H = 880, 560
DIM, FG, LINE, PINK = "#4f7f5d", "#b6f5c6", "#14261b", "#ff5a7a"
LH, GAP, HEAD_H, HEAD_MB = 16.5, 12, 18.75, 12
TOP, BOT = 40, 524                     # middle band
L_KEY, L_VAL = 17, 85                  # left column x
R_KEY, R_VAL = 674, 732                # right column x
out = []
add = out.append

def txt(x, y, s, cls="", anchor=None, extra=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    c = f' class="{cls}"' if cls else ""
    add(f'<text x="{x:g}" y="{y:.2f}"{c}{a}{extra}>{escape(s)}</text>')

def block(label, rows, top, kx, vx):
    """Draws a heading + key/value grid, returns nothing. rows: [(key, value)] with '|' = line break."""
    txt(kx, top + 13.9, label, "h")
    y = top + HEAD_H + HEAD_MB
    for k, v in rows:
        kl, vl = fill(k).split("|"), fill(v).split("|")
        for i, line in enumerate(kl):
            txt(kx, y + i * LH + 12.2, line, "k")
        for i, line in enumerate(vl):
            if line == "at large":
                txt(vx, y + i * LH + 12.2, line, "a")
            else:
                txt(vx, y + i * LH + 12.2, line, "v")
        y += max(len(kl), len(vl)) * LH + GAP

def block_height(rows):
    hs = [max(len(fill(k).split("|")), len(fill(v).split("|"))) * LH for k, v in rows]
    return HEAD_H + HEAD_MB + sum(hs) + GAP * (len(rows) - 1)

# ---------- svg ----------
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Big Ben, bandit.sol: wanted dossier">')
add("<style>")
add(f"@font-face{{font-family:'JBM';font-weight:400;src:url(data:font/woff2;base64,{font_r}) format('woff2')}}")
add(f"@font-face{{font-family:'JBM';font-weight:700;src:url(data:font/woff2;base64,{font_b}) format('woff2')}}")
add("text{font-family:'JBM','JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace;white-space:pre}")
add(f".k{{font-size:11px;fill:{DIM}}} .v{{font-size:11px;fill:{FG}}} .a{{font-size:11px;fill:{ACC}}}")
add(f".h{{font-size:12.5px;font-weight:700;fill:{ACC}}} .bar{{font-size:12px;fill:{DIM}}} .art{{font-size:7.2px;fill:{ACC}}}")
add("</style>")
add(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#000"/>')

# WANTED watermark (vector outline, no font needed)
sc = 270 / wanted["upm"]
ww = wanted["width"] * sc
add(f'<g transform="translate(440 280) rotate(-17) translate({-(ww + 0.06 * 270) / 2:.2f} 81) scale({sc:.5f})" '
    f'opacity="0.06" fill="{ACC}" stroke="{ACC}" stroke-width="{5 / sc:.2f}" stroke-linejoin="round">'
    f'<path d="{wanted["d"]}"/></g>')

# top bar
txt(19, 24.3, "root@bandit", "bar", extra=f' fill="{ACC}" style="fill:{ACC}"')
txt(19 + 11 * 7.2, 24.3, ":~# sudo ./dossier --subject big-ben", "bar")
txt(861, 24.3, "pid 1337 · encrypted", "bar", anchor="end")
add(f'<rect x="1" y="39" width="{W-2}" height="1" fill="{LINE}"/>')

# left + right columns
case = [tuple(r) for r in cfg["case_file"]]
contact = [tuple(r) for r in cfg["contact"]]
skills = [tuple(r) for r in cfg["skills"]]
metrics = [tuple(r) for r in cfg["metrics"]]
bottom = BOT - 46
block("[ case file ]", case, TOP + 22, L_KEY, L_VAL)
block("[ contact ]", contact, bottom - block_height(contact), L_KEY, L_VAL)
block("[ skills ]", skills, TOP + 22, R_KEY, R_VAL)
block("[ metrics ]", metrics, bottom - block_height(metrics), R_KEY, R_VAL)

# portrait (each line is pinned to exact width so it never drifts with the font)
CH, LHP = 7.2 * 0.6, 7.2
mw = max(len(l) for l in portrait)
px = 241 + (398 - (int(mw * CH) + 4)) / 2
for i, line in enumerate(portrait):
    s = line.lstrip(" ")
    if not s.strip():
        continue
    s = s.rstrip()
    x = px + (len(line) - len(s)) * CH
    y = TOP + 14 + i * LHP + 6.2
    add(f'<text class="art" x="{x:.2f}" y="{y:.2f}" textLength="{len(s) * CH:.2f}" lengthAdjust="spacing">{escape(s)}</text>')

# footer
add(f'<rect x="1" y="{BOT}" width="{W-2}" height="1" fill="{LINE}"/>')
fy = BOT + 1 + 8 + 13.3
add(f'<text class="bar" x="19" y="{fy:.2f}"><tspan style="fill:{ACC}">[ ok ]</tspan> target acquired  <tspan style="fill:{ACC}">[ ok ]</tspan> mask on  <tspan style="fill:{PINK}">[ !! ]</tspan> at large</text>')
for i, c in enumerate(["#c8c8c8", "#c8c800", "#00c8c8", "#00c800", "#c800c8", "#c80000", "#0000c8"]):
    add(f'<rect x="{749 + i * 16}" y="{BOT + 1 + 8 + 5}" width="16" height="8" fill="{c}" opacity="0.75"/>')

add(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="none" stroke="{LINE}"/>')
add("</svg>")

with open(os.path.join(ROOT, "card.svg"), "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
print(f"card.svg written · uptime {uptime} · repos {repos} · commits {commits}")
