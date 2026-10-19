"""Genera el afiche animado para Facebook (curso de performance con k6 + Prometheus + Grafana).

    python promo/generar_promo.py

Salidas (en promo/):
  promo_facebook.mp4   1080x1350 (4:5), 30 fps, 16 s, en bucle   <- el recomendado para Facebook
  promo_facebook.gif   540x675, 15 fps (alternativa liviana)
  promo_portada.png    tarjeta final con fecha y precio
  promo_carga.png      cuadro en plena prueba (imagen alternativa)
Necesita: Pillow, numpy, imageio, imageio-ffmpeg.

La simulación es coherente: 5 VUs ejecutan iteraciones reales (request -> API -> BD o servicio
externo -> respuesta -> think time) y el panel tipo Grafana se calcula a partir de esos requests.
"""
import math
import os
import random

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, DUR = 1080, 1350, 30, 16.0
S = 2                                   # supersampling para bordes suaves
FONTS = r"C:\Windows\Fonts"

# ----------------------------------------------------------------- textos
BRAND = "PRO TEST QA ACADEMY"
TITLE = ["Performance Testing", "de APIs"]
SUBTITLE = "k6 + Prometheus + Grafana · 100 % open source"
PIPE = ["Script k6", "Prometheus", "Grafana", "Alertas", "Análisis"]
CTA_TOP = "Más allá de ejecutar una prueba de carga:"
CTA_TOP2 = "medir · analizar · alertar · decidir"
CTA_TITLE = ["Taller: Performance Testing", "con k6"]
CTA_LINES = ["k6 · Prometheus · Grafana · análisis e informes",
             "10 horas · 2 semanas y media · virtual en vivo por Zoom"]
CTA_DATE = "3 de noviembre"
CTA_PRICE = "100 USD"
CTA_SLOTS = "¡Cupos limitados!"
CTA_CONTACT = "Escríbenos por mensaje para inscribirte"

# ----------------------------------------------------------------- paletas
BG = (13, 15, 21); PANEL = (25, 30, 40); PANEL2 = (34, 41, 54); LINE = (52, 60, 76)
TEXT = (245, 247, 251); MUTED = (160, 169, 186)
ORANGE = (243, 164, 59); GREEN = (87, 199, 133); RED = (239, 101, 112); BLUE = (89, 169, 230); PURPLE = (169, 130, 226)
# Grafana (tema oscuro)
G_BG = (17, 18, 23); G_PANEL = (24, 27, 31); G_BORDER = (44, 50, 53); G_TEXT = (204, 204, 220); G_MUT = (142, 142, 160)
G_GREEN = (115, 191, 105); G_YEL = (250, 222, 42); G_RED = (242, 73, 92); G_BLUE = (87, 148, 242); G_ORANGE = (255, 152, 48)
VU_COL = [(87, 148, 242), (115, 191, 105), (255, 152, 48), (184, 119, 217), (242, 201, 76)]


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), int(size * S))


F = {
    "brand": font("segoeuib.ttf", 26), "title": font("segoeuib.ttf", 68), "sub": font("segoeui.ttf", 28),
    "lbl": font("segoeuib.ttf", 22), "small": font("segoeui.ttf", 19), "tiny": font("segoeui.ttf", 15),
    "mono": font("consolab.ttf", 20), "monoS": font("consola.ttf", 16), "monoT": font("consolab.ttf", 13),
    "gT": font("segoeuib.ttf", 16), "gS": font("segoeui.ttf", 14), "gBig": font("segoeuib.ttf", 38),
    "chip": font("segoeuib.ttf", 19), "cta": font("segoeuib.ttf", 56), "ctaS": font("segoeui.ttf", 27),
    "ctaB": font("segoeuib.ttf", 33), "price": font("segoeuib.ttf", 62), "ins": font("segoeuib.ttf", 17), "insS": font("segoeui.ttf", 16),
}


def P(*v):
    return tuple(int(round(x * S)) for x in v)


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ms_txt(v):
    return f"{v / 1000:.2f} s".replace(".", ",") if v >= 1000 else f"{v:.0f} ms"


# ----------------------------------------------------------------- escenario
VU_X = 112
VU_Y = [362 + i * 77 for i in range(5)]
VU_DEV = ["phone", "web", "phone", "web", "phone"]
API = (540, 500)
DB = (905, 410)
EXT = (905, 610)
RUN_END = 11.6                          # después de esto, ningún VU empieza una iteración nueva
SLOW = (6.6, 9.8)                       # el servicio externo se degrada en este intervalo
LEG = 0.34                              # segundos por tramo en la animación

random.seed(11)
REQS = []                               # cada request simulado
VU_SPAN = []
for i in range(5):
    t = 1.0 + i * 0.85                  # rampa: un VU nuevo cada 0,85 s
    start = t
    it = 0
    while t < RUN_END:
        ep = "GET" if (it + i) % 2 == 0 else "POST"
        tgt = "db" if ep == "GET" else "ext"
        slow = tgt == "ext" and SLOW[0] < t < SLOW[1]
        proc = (0.07 + random.random() * 0.06) if tgt == "db" else ((0.55 + random.random() * 0.4) if slow else (0.10 + random.random() * 0.06))
        err = slow and random.random() < 0.22                # timeout de la pasarela
        times = [t, t + LEG, t + 2 * LEG, t + 2 * LEG + proc, t + 3 * LEG + proc, t + 4 * LEG + proc]
        ms = (150 + random.random() * 70 + proc * 600) if tgt == "db" else (230 + random.random() * 80 + proc * 1100)
        REQS.append({"vu": i, "ep": ep, "tgt": tgt, "times": times, "end": times[-1], "ms": ms, "err": err})
        t = times[-1] + 0.32 + random.random() * 0.12       # think time (sleep)
        it += 1
    VU_SPAN.append((start, t))


def active_vus(t):
    return sum(1 for s, e in VU_SPAN if s <= t < e)


def packet(r, t):
    tm = r["times"]
    if not tm[0] <= t < tm[-1]:
        return None
    y0 = VU_Y[r["vu"]]
    cli = (VU_X + 58, y0)
    api_in = (API[0] - 105, API[1] - 40 + r["vu"] * 20)
    api_out = (API[0] + 105, API[1] - 30 + r["vu"] * 15)
    tg = (DB[0] - 72, DB[1]) if r["tgt"] == "db" else (EXT[0] - 88, EXT[1])
    segs = [(tm[0], tm[1], cli, api_in, "req"), (tm[1], tm[2], api_out, tg, "req"),
            (tm[2], tm[3], tg, tg, "wait"), (tm[3], tm[4], tg, api_out, "res"), (tm[4], tm[5], api_in, cli, "res")]
    for a, b, p0, p1, kind in segs:
        if a <= t < b:
            f = ease((t - a) / max(1e-6, b - a))
            if kind == "wait":
                ang = t * 9 + r["vu"]
                return p0[0] + math.cos(ang) * 6, p0[1] + math.sin(ang) * 6, kind
            return p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f, kind
    return None


# ----------------------------------------------------------------- métricas (a partir de los requests)
def window(t, span=3.0):
    return [r for r in REQS if t - span < r["end"] <= t]


def p95(vals):
    if not vals:
        return None
    v = sorted(vals)
    return v[min(len(v) - 1, int(math.ceil(0.95 * len(v))) - 1)]


SAMPLES = []
last = {"GET": None, "POST": None, "all": None}
for k in range(0, int(DUR * 4) + 1):
    t = k / 4
    w = window(t)
    vals = {"GET": [r["ms"] for r in w if r["ep"] == "GET"], "POST": [r["ms"] for r in w if r["ep"] == "POST"], "all": [r["ms"] for r in w]}
    for key in last:
        pv = p95(vals[key])
        if pv is not None:
            last[key] = pv
    errs = sum(1 for r in w if r["err"])
    SAMPLES.append({"t": t, "vus": active_vus(t), "rps": len(w) / 3.0, "p95": last["all"], "get": last["GET"],
                    "post": last["POST"], "err": (errs / len(w) * 100) if w else 0.0, "has": bool(w)})


def sample(t):
    return SAMPLES[min(len(SAMPLES) - 1, int(t * 4))]


ALERT_T = next((s["t"] for s in SAMPLES if s["post"] and s["post"] > 800), 8.0)

# ----------------------------------------------------------------- fondo fijo
BASE = None
GLOW = None


def device(d, kind, x, y, col):
    if kind == "phone":
        d.rounded_rectangle(P(x - 15, y - 26, x + 15, y + 26), radius=6 * S, fill=PANEL2, outline=col, width=2 * S)
        d.rounded_rectangle(P(x - 11, y - 20, x + 11, y + 17), radius=2 * S, fill=(20, 34, 52))
        d.ellipse(P(x - 2, y + 19, x + 2, y + 23), fill=col)
    else:
        d.rounded_rectangle(P(x - 26, y - 20, x + 26, y + 12), radius=4 * S, fill=PANEL2, outline=col, width=2 * S)
        d.rectangle(P(x - 21, y - 15, x + 21, y + 7), fill=(20, 34, 52))
        d.polygon(P(x - 33, y + 14, x + 33, y + 14, x + 28, y + 21, x - 28, y + 21), fill=col)


def background():
    img = Image.new("RGB", P(W, H), BG)
    d = ImageDraw.Draw(img)
    for y in range(0, H, 6):
        d.rectangle(P(0, y, W, y + 6), fill=mix((22, 28, 44), BG, min(1, y / 760)))
    for x in range(0, W, 54):
        d.line(P(x, 290, x, 700), fill=(22, 27, 37), width=S)
    for y in range(290, 700, 54):
        d.line(P(0, y, W, y), fill=(22, 27, 37), width=S)
    # cabecera
    d.text(P(60, 44), BRAND, font=F["brand"], fill=ORANGE)
    d.text(P(60, 80), TITLE[0], font=F["title"], fill=TEXT)
    d.text(P(60, 154), TITLE[1], font=F["title"], fill=TEXT)
    d.text(P(62, 240), SUBTITLE, font=F["sub"], fill=MUTED)
    # cables
    for i, y in enumerate(VU_Y):
        d.line(P(VU_X + 58, y, API[0] - 105, API[1] - 40 + i * 20), fill=LINE, width=2 * S)
    d.line(P(API[0] + 105, API[1] - 30, DB[0] - 72, DB[1]), fill=LINE, width=3 * S)
    d.line(P(API[0] + 105, API[1] + 30, EXT[0] - 88, EXT[1]), fill=LINE, width=3 * S)
    # VUs
    for i, y in enumerate(VU_Y):
        device(d, VU_DEV[i], VU_X, y, VU_COL[i])
        d.text(P(VU_X - 50, y), f"VU{i + 1}", font=F["mono"], fill=VU_COL[i], anchor="rm")
    # API
    ax, ay = API
    d.rounded_rectangle(P(ax - 105, ay - 92, ax + 105, ay + 92), radius=20 * S, fill=PANEL, outline=ORANGE, width=4 * S)
    d.text(P(ax, ay - 50), "API REST", font=F["lbl"], fill=TEXT, anchor="mm")
    d.text(P(ax - 78, ay - 6), "GET", font=F["monoS"], fill=G_GREEN, anchor="lm")
    d.text(P(ax - 22, ay - 6), "/clientes", font=F["monoS"], fill=MUTED, anchor="lm")
    d.text(P(ax - 78, ay + 22), "POST", font=F["monoS"], fill=G_ORANGE, anchor="lm")
    d.text(P(ax - 22, ay + 22), "/pagos", font=F["monoS"], fill=MUTED, anchor="lm")
    # base de datos
    bx, by = DB
    d.rectangle(P(bx - 60, by - 38, bx + 60, by + 38), fill=PANEL2)
    d.ellipse(P(bx - 60, by + 21, bx + 60, by + 55), fill=PANEL2, outline=PURPLE, width=3 * S)
    d.rectangle(P(bx - 57, by - 38, bx + 57, by + 38), fill=PANEL2)
    d.line(P(bx - 60, by - 38, bx - 60, by + 38), fill=PURPLE, width=3 * S)
    d.line(P(bx + 60, by - 38, bx + 60, by + 38), fill=PURPLE, width=3 * S)
    d.ellipse(P(bx - 60, by - 55, bx + 60, by - 21), fill=(48, 40, 70), outline=PURPLE, width=3 * S)
    d.text(P(bx, by + 6), "SQL", font=F["mono"], fill=PURPLE, anchor="mm")
    d.text(P(bx, by + 80), "Base de datos", font=F["small"], fill=MUTED, anchor="mm")
    # servicio externo
    ex, ey = EXT
    for (cx, cy, r) in [(-40, 8, 33), (0, -12, 43), (42, 6, 33), (0, 18, 35)]:
        d.ellipse(P(ex + cx - r, ey + cy - r, ex + cx + r, ey + cy + r), fill=(30, 52, 70), outline=BLUE, width=3 * S)
    for (cx, cy, r) in [(-40, 8, 30), (0, -12, 40), (42, 6, 30), (0, 18, 32)]:
        d.ellipse(P(ex + cx - r, ey + cy - r, ex + cx + r, ey + cy + r), fill=(30, 52, 70))
    d.text(P(ex, ey + 4), "API", font=F["mono"], fill=BLUE, anchor="mm")
    d.text(P(ex, ey + 74), "Pasarela de pagos (externa)", font=F["small"], fill=MUTED, anchor="mm")
    # Grafana: marco, barra superior y paneles vacíos
    gx0, gy0, gx1, gy1 = 30, 792, W - 30, 1262
    d.rounded_rectangle(P(gx0, gy0, gx1, gy1), radius=14 * S, fill=G_BG, outline=G_BORDER, width=2 * S)
    for k, c in enumerate([(244, 104, 0), (250, 160, 0), (255, 200, 40)]):           # logo simple
        d.rounded_rectangle(P(48 + k * 8, 822 - k * 6, 54 + k * 8, 834), radius=2 * S, fill=c)
    d.text(P(84, 816), "Dashboards", font=F["gS"], fill=G_MUT)
    d.text(P(170, 816), "›", font=F["gS"], fill=G_MUT)
    d.text(P(184, 815), "k6 Load Testing · API Pagos", font=F["gT"], fill=G_TEXT)
    d.rounded_rectangle(P(gx1 - 236, 808, gx1 - 64, 834), radius=4 * S, fill=G_PANEL, outline=G_BORDER, width=S)
    d.text(P(gx1 - 150, 821), "Last 15 seconds", font=F["gS"], fill=G_TEXT, anchor="mm")
    d.rounded_rectangle(P(gx1 - 56, 808, gx1 - 22, 834), radius=4 * S, fill=G_PANEL, outline=G_BORDER, width=S)
    d.arc(P(gx1 - 46, 814, gx1 - 32, 828), start=40, end=320, fill=G_TEXT, width=2 * S)       # ícono refrescar
    for i, ttl in enumerate(["Active VUs", "Requests / s", "p95 latency", "Error rate"]):
        x0 = 44 + i * 252
        d.rounded_rectangle(P(x0, 846, x0 + 240, 948), radius=6 * S, fill=G_PANEL, outline=G_BORDER, width=S)
        d.text(P(x0 + 10, 852), ttl, font=F["gT"], fill=G_TEXT)
    d.rounded_rectangle(P(44, 958, gx1 - 14, 1250), radius=6 * S, fill=G_PANEL, outline=G_BORDER, width=S)
    d.text(P(54, 964), "http_req_duration · p95 por endpoint", font=F["gT"], fill=G_TEXT)
    return img


# ----------------------------------------------------------------- Grafana (dinámico)
CH = (104, 994, 1030, 1190)             # área del gráfico de líneas
YMAX = 1400


def gy(v):
    return CH[3] - (CH[3] - CH[1]) * min(v, YMAX) / YMAX


def gx(t):
    return CH[0] + (CH[2] - CH[0]) * t / 15.0


def stat_color(kind, v):
    if kind == "p95":
        return G_GREEN if v < 600 else (G_YEL if v < 800 else G_RED)
    if kind == "err":
        return G_GREEN if v < 1 else (G_YEL if v < 5 else G_RED)
    return G_BLUE if kind == "vus" else G_GREEN


def grafana(img, t):
    s = sample(t)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    hist = [x for x in SAMPLES if x["t"] <= t]
    # paneles Stat
    vals = [("vus", s["vus"], f"{s['vus']}"), ("rps", s["rps"], f"{s['rps']:.1f}".replace(".", ",")),
            ("p95", s["p95"] or 0, ms_txt(s["p95"]) if s["p95"] else "—"), ("err", s["err"], f"{s['err']:.1f} %".replace(".", ","))]
    for i, (key, v, txt) in enumerate(vals):
        x0 = 44 + i * 252
        c = stat_color(key, v)
        if key in ("p95", "err") and c == G_RED:              # fondo rojo como en Grafana al superar el umbral
            d.rounded_rectangle(P(x0 + 1, 847, x0 + 239, 947), radius=6 * S, fill=(*G_RED, 46))
        series = [x[key] or 0 for x in hist]                   # mini gráfico (sparkline)
        if len(series) > 1:
            mx = {"vus": 5, "rps": 6, "p95": YMAX, "err": 30}[key]
            pts = [(x0 + 4 + 232 * (j / 60), 944 - 24 * min(1, val / mx)) for j, val in enumerate(series[-61:])]
            d.polygon([c2 for pt in [P(pts[0][0], 944)] + [P(*p) for p in pts] + [P(pts[-1][0], 944)] for c2 in pt], fill=(*c, 40))
            d.line([c2 for p in pts for c2 in P(*p)], fill=(*c, 200), width=2 * S)
        d.text(P(x0 + 120, 892), txt, font=F["gBig"], fill=c, anchor="mm")
        if key == "vus":
            d.text(P(x0 + 230, 856), "de 5", font=F["gS"], fill=G_MUT, anchor="ra")
        if key == "p95":
            d.text(P(x0 + 230, 856), "umbral 800 ms", font=F["gS"], fill=G_MUT, anchor="ra")
    # ejes del time series
    for v in (0, 400, 800, 1200):
        y = gy(v)
        d.line(P(CH[0], y, CH[2], y), fill=(*G_BORDER, 255), width=S)
        d.text(P(CH[0] - 8, y), ms_txt(v) if v else "0", font=F["gS"], fill=G_MUT, anchor="rm")
    for k in range(0, 16, 3):
        d.text(P(gx(k), CH[3] + 14), f"10:00:{k:02d}", font=F["gS"], fill=G_MUT, anchor="mm")
    # umbral y región de alerta
    d.rectangle(P(CH[0], gy(YMAX), CH[2], gy(800)), fill=(*G_RED, 18))
    for xx in range(int(CH[0]), int(CH[2]), 14):
        d.line(P(xx, gy(800), xx + 7, gy(800)), fill=(*G_RED, 220), width=2 * S)
    if t >= ALERT_T:
        recover = next((x["t"] for x in SAMPLES if x["t"] > ALERT_T and x["post"] and x["post"] < 800), DUR)
        a0, a1 = gx(ALERT_T), gx(min(t, recover))
        d.rectangle(P(a0, CH[1], max(a0 + 2, a1), CH[3]), fill=(*G_RED, 30))
        d.line(P(a0, CH[1], a0, CH[3]), fill=(*G_RED, 255), width=2 * S)
    # series
    for key, c in (("post", G_ORANGE), ("get", G_GREEN)):
        pts = [(gx(x["t"]), gy(x[key])) for x in hist if x[key] is not None and x["t"] >= 1]
        if len(pts) > 1:
            d.polygon([c2 for pt in [P(pts[0][0], CH[3])] + [P(*p) for p in pts] + [P(pts[-1][0], CH[3])] for c2 in pt], fill=(*c, 34))
            d.line([c2 for p in pts for c2 in P(*p)], fill=(*c, 255), width=3 * S, joint="curve")
    # leyenda con Mean / Max
    for j, (key, lbl, c) in enumerate((("get", "GET /clientes", G_GREEN), ("post", "POST /pagos", G_ORANGE))):
        vs = [x[key] for x in hist if x[key] is not None and x["t"] >= 1]
        x0 = 104 + j * 470
        d.rectangle(P(x0, 1234, x0 + 16, 1238), fill=(*c, 255))
        d.text(P(x0 + 24, 1236), lbl, font=F["gS"], fill=G_TEXT, anchor="lm")
        if vs:
            d.text(P(x0 + 150, 1236), f"Mean {ms_txt(sum(vs) / len(vs))}   Max {ms_txt(max(vs))}", font=F["gS"], fill=G_MUT, anchor="lm")
    # alerta en la barra superior
    if t >= ALERT_T:
        pulse = 0.6 + 0.4 * math.sin(t * 8)
        d.rounded_rectangle(P(W - 440, 808, W - 276, 834), radius=4 * S, fill=(*G_RED, int(160 + 90 * pulse)))
        d.ellipse(P(W - 428, 816, W - 418, 826), fill=(255, 255, 255, 255))
        d.text(P(W - 350, 821), "1 alerta activa", font=F["gS"], fill=(255, 255, 255, 255), anchor="mm")
    out = img.convert("RGBA")
    out.alpha_composite(lay)
    return out.convert("RGB")


def insights(img, t):
    """Anotaciones de análisis: alerta y diagnóstico de la causa."""
    if t < ALERT_T + 0.2 or t > 12.4:
        return img
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * ease((t - ALERT_T - 0.2) / 0.4) * (ease((12.4 - t) / 0.4)))
    x0, y0 = 116, 1000                                         # 1. alerta
    d.rounded_rectangle(P(x0, y0, x0 + 470, y0 + 62), radius=8 * S, fill=(40, 16, 22, a), outline=(*G_RED, a), width=2 * S)
    d.text(P(x0 + 14, y0 + 18), "ALERTA · p95 de POST /pagos > 800 ms", font=F["ins"], fill=(255, 200, 205, a), anchor="lm")
    d.text(P(x0 + 14, y0 + 44), "Threshold de k6 incumplido: http_req_duration p(95)<800", font=F["insS"], fill=(230, 180, 185, a), anchor="lm")
    if t > ALERT_T + 1.4:                                      # 2. diagnóstico
        b = int(a * ease((t - ALERT_T - 1.4) / 0.4))
        x1, y1 = 232, 616
        d.rounded_rectangle(P(x1, y1, x1 + 536, y1 + 62), radius=8 * S, fill=(16, 32, 46, b), outline=(*G_BLUE, b), width=2 * S)
        d.text(P(x1 + 14, y1 + 18), "ANÁLISIS · el cuello de botella es la pasarela externa", font=F["ins"], fill=(200, 225, 255, b), anchor="lm")
        d.text(P(x1 + 14, y1 + 44), "GET /clientes (API + BD) sigue estable en ~250 ms", font=F["insS"], fill=(180, 205, 235, b), anchor="lm")
        ex, ey = EXT
        rr = 74 + 6 * math.sin(t * 7)
        d.ellipse(P(ex - rr, ey - rr * 0.8, ex + rr, ey + rr * 0.8), outline=(*G_RED, b), width=4 * S)
    out = img.convert("RGBA")
    out.alpha_composite(lay)
    return out.convert("RGB")


def pipeline(d, t):
    """Cadena k6 -> Prometheus -> Grafana -> Alertas -> Análisis (se enciende por etapas)."""
    on_at = [1.0, 1.8, 2.6, ALERT_T, ALERT_T + 1.4]
    cols = [PURPLE, (230, 82, 44), G_ORANGE, G_RED, G_BLUE]
    widths = [d.textlength(p, font=F["chip"]) / S + 34 for p in PIPE]
    x = (W - (sum(widths) + 30 * (len(PIPE) - 1))) / 2
    for i, (p, w) in enumerate(zip(PIPE, widths)):
        on = t >= on_at[i]
        c = cols[i] if on else LINE
        d.rounded_rectangle(P(x, 718, x + w, 760), radius=21 * S, fill=mix(c, BG, 0.78) if on else PANEL, outline=c, width=2 * S)
        d.text(P(x + w / 2, 739), p, font=F["chip"], fill=TEXT if on else MUTED, anchor="mm")
        if i < len(PIPE) - 1:
            d.text(P(x + w + 15, 739), "→", font=F["chip"], fill=TEXT if t >= on_at[i + 1] else LINE, anchor="mm")
        x += w + 30


def vu_badge(d, t):
    n = active_vus(t)
    d.rounded_rectangle(P(40, 286, 236, 318), radius=16 * S, fill=(40, 30, 60), outline=PURPLE, width=2 * S)
    d.text(P(138, 302), f"k6 · {n}/5 VUs", font=F["mono"], fill=TEXT, anchor="mm")
    for i, (s, e) in enumerate(VU_SPAN):                       # luz de VU activo
        y = VU_Y[i]
        d.ellipse(P(VU_X + 30, y - 30, VU_X + 40, y - 20), fill=G_GREEN if s <= t < e else (60, 66, 80))


def cta(img, t):
    k = ease((t - 12.4) / 0.7)
    if k <= 0:
        return img
    fade = ease((DUR - t) / 0.45) if t > DUR - 0.45 else 1.0
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle(P(0, 0, W, H), fill=(8, 10, 15, int(205 * k * fade)))
    top = 236 + (1 - k) * 260
    a = int(255 * fade)
    d.rounded_rectangle(P(64, top, W - 64, top + 880), radius=30 * S, fill=(25, 30, 40, a), outline=ORANGE + (a,), width=4 * S)
    d.text(P(W / 2, top + 54), CTA_TOP, font=F["ctaS"], fill=MUTED + (a,), anchor="mm")
    d.text(P(W / 2, top + 98), CTA_TOP2, font=F["ctaB"], fill=ORANGE + (a,), anchor="mm")
    d.text(P(W / 2, top + 180), CTA_TITLE[0], font=F["cta"], fill=TEXT + (a,), anchor="mm")
    d.text(P(W / 2, top + 246), CTA_TITLE[1], font=F["cta"], fill=TEXT + (a,), anchor="mm")
    d.text(P(W / 2, top + 320), CTA_LINES[0], font=F["ctaS"], fill=MUTED + (a,), anchor="mm")
    d.text(P(W / 2, top + 362), CTA_LINES[1], font=F["ctaS"], fill=MUTED + (a,), anchor="mm")
    for j, (lbl, val, fnt, col) in enumerate((("INICIO", CTA_DATE, F["ctaB"], TEXT), ("INVERSIÓN", CTA_PRICE, F["price"], GREEN))):
        bx0 = 130 if j == 0 else W / 2 + 15
        bx1 = W / 2 - 15 if j == 0 else W - 130
        d.rounded_rectangle(P(bx0, top + 410, bx1, top + 530), radius=18 * S, fill=(34, 41, 54, a))
        d.text(P((bx0 + bx1) / 2, top + 446), lbl, font=F["ctaS"], fill=MUTED + (a,), anchor="mm")
        d.text(P((bx0 + bx1) / 2, top + 494), val, font=fnt, fill=col + (a,), anchor="mm")
    pulse = 1 + 0.05 * math.sin(t * 9)
    bw, bh = 330 * pulse, 64 * pulse
    cy = top + 600
    d.rounded_rectangle(P(W / 2 - bw / 2, cy - bh / 2, W / 2 + bw / 2, cy + bh / 2), radius=32 * S, fill=RED + (a,))
    d.text(P(W / 2, cy), CTA_SLOTS, font=F["ctaB"], fill=(255, 255, 255, a), anchor="mm")
    d.text(P(W / 2, top + 690), CTA_CONTACT, font=F["ctaS"], fill=TEXT + (a,), anchor="mm")
    chips = (("k6", PURPLE), ("Prometheus", (230, 82, 44)), ("Grafana", G_ORANGE))
    x = W / 2 - (sum(d.textlength(tl, font=F["chip"]) / S + 34 for tl, _ in chips) + 14 * 2) / 2
    for tool, c in chips:
        w = d.textlength(tool, font=F["chip"]) / S + 34
        d.rounded_rectangle(P(x, top + 740, x + w, top + 780), radius=20 * S, fill=(34, 41, 54, a), outline=c + (a,), width=2 * S)
        d.text(P(x + w / 2, top + 760), tool, font=F["chip"], fill=TEXT + (a,), anchor="mm")
        x += w + 14
    d.text(P(W / 2, top + 828), BRAND, font=F["brand"], fill=ORANGE + (a,), anchor="mm")
    out = img.convert("RGBA")
    out.alpha_composite(ov)
    return out.convert("RGB")


def frame(t):
    img = BASE.copy()
    n = active_vus(t)
    if n:
        slow = SLOW[0] < t < SLOW[1]
        col = np.array(G_RED if (slow and t > ALERT_T) else ORANGE, dtype=np.float32) * 0.22 * (n / 5)
        img = Image.fromarray(np.clip(np.asarray(img, dtype=np.float32) + GLOW[..., None] * col, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for r in REQS:
        pos = packet(r, t)
        if not pos:
            continue
        x, y, kind = pos
        c = VU_COL[r["vu"]]
        ring = (G_RED if r["err"] else G_GREEN) if kind == "res" else (G_YEL if kind == "wait" else c)
        d.ellipse(P(x - 13, y - 13, x + 13, y + 13), fill=c, outline=ring, width=3 * S)
        d.text(P(x, y + 1), str(r["vu"] + 1), font=F["monoT"], fill=(15, 15, 20), anchor="mm")
    vu_badge(d, t)
    pipeline(d, t)
    img = grafana(img, t)
    img = insights(img, t)
    img = cta(img, t)
    if t < 0.6:
        img = Image.blend(Image.new("RGB", img.size, BG), img, ease(t / 0.6))
    return img.resize((W, H), Image.LANCZOS)


def setup():
    global BASE, GLOW
    BASE = background()
    g = Image.new("L", BASE.size, 0)
    ImageDraw.Draw(g).ellipse(P(API[0] - 170, API[1] - 170, API[0] + 170, API[1] + 170), fill=255)
    GLOW = np.asarray(g.filter(ImageFilter.GaussianBlur(40 * S)), dtype=np.float32) / 255


def main():
    setup()
    n = int(DUR * FPS)
    w = imageio.get_writer(os.path.join(OUT, "promo_facebook.mp4"), fps=FPS, codec="libx264", quality=8,
                           pixelformat="yuv420p", macro_block_size=1)
    gif = []
    for i in range(n):
        t = i / FPS
        f = frame(t)
        w.append_data(np.asarray(f))
        if i % 2 == 0:
            gif.append(f.resize((W // 2, H // 2), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE, colors=128))
        if i == int(14.6 * FPS):
            f.save(os.path.join(OUT, "promo_portada.png"))
        if i % 60 == 0:
            print(f"  cuadro {i}/{n}")
    w.close()
    gif[0].save(os.path.join(OUT, "promo_facebook.gif"), save_all=True, append_images=gif[1:],
                duration=int(1000 / (FPS / 2)), loop=0, optimize=True)
    frame(ALERT_T + 2.3).save(os.path.join(OUT, "promo_carga.png"))
    for f in ("promo_facebook.mp4", "promo_facebook.gif", "promo_portada.png", "promo_carga.png"):
        print(f"  ✓ {f}: {os.path.getsize(os.path.join(OUT, f)) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
