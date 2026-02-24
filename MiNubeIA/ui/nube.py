"""
ui/nube.py — Ventana flotante de Nuvia con transparencia REAL.
Renderiza la nube kawaii matching the CSS Kawaii Pro design exactly.
Escalado a un tamaño más compacto (0.8x).
Partículas modo 'brillitos' (sparkles) pequeños y dinámicos.
"""

import math
import time
import random
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk

_TRANSPARENT = "#FF00FF"
_TRANS_RGB = (255, 0, 255)

# ── Configuración de Escala (0.8x) ──
_SCALE = 0.8
_W, _H = int(260 * _SCALE), int(220 * _SCALE)

# Tintes de estado
_TINT_LISTENING = (100, 200, 255, 45)
_TINT_THINKING  = (180, 100, 255, 45)
_TINT_SPEAKING  = (255, 180, 100, 45)

# ── Coordenadas Base (antes del escalado) ──
_SCX_B, _SCY_B = 130, 110
_CL_B, _CT_B, _CR_B, _CB_B = 70, 70, 190, 150

# Coordenadas Escaladas
_SCX, _SCY = _SCX_B * _SCALE, _SCY_B * _SCALE
_CL, _CT, _CR, _CB = _CL_B * _SCALE, _CT_B * _SCALE, _CR_B * _SCALE, _CB_B * _SCALE
_CW, _CH = (_CR_B - _CL_B) * _SCALE, (_CB_B - _CT_B) * _SCALE

# ── Sparkle Particle Config (posiciones de origen) ──
_SPARKLE_POSITIONS = [
    {"x": 30*_SCALE,  "y": 70*_SCALE,  "sx": -35*_SCALE, "sy": -40*_SCALE},
    {"x": 20*_SCALE,  "y": 90*_SCALE,  "sx": -40*_SCALE, "sy": -25*_SCALE},
    {"x": 35*_SCALE,  "y": 110*_SCALE, "sx": -28*_SCALE, "sy": -50*_SCALE},
    {"x": 15*_SCALE,  "y": 80*_SCALE,  "sx": -50*_SCALE, "sy": -35*_SCALE},
    {"x": 190*_SCALE, "y": 70*_SCALE,  "sx": 35*_SCALE,  "sy": -40*_SCALE},
    {"x": 200*_SCALE, "y": 90*_SCALE,  "sx": 42*_SCALE,  "sy": -28*_SCALE},
    {"x": 185*_SCALE, "y": 110*_SCALE, "sx": 30*_SCALE,  "sy": -55*_SCALE},
    {"x": 205*_SCALE, "y": 80*_SCALE,  "sx": 48*_SCALE,  "sy": -30*_SCALE},
    {"x": 100*_SCALE, "y": 30*_SCALE,  "sx": -10*_SCALE, "sy": -55*_SCALE},
    {"x": 130*_SCALE, "y": 25*_SCALE,  "sx": 8*_SCALE,   "sy": -58*_SCALE},
    {"x": 115*_SCALE, "y": 35*_SCALE,  "sx": 0*_SCALE,   "sy": -60*_SCALE},
    {"x": 90*_SCALE,  "y": 165*_SCALE, "sx": -15*_SCALE, "sy": 40*_SCALE},
    {"x": 130*_SCALE, "y": 168*_SCALE, "sx": 15*_SCALE,  "sy": 42*_SCALE},
]


def _gradient_ellipse(draw, bbox, c_in, c_out, steps=12):
    x0, y0, x1, y1 = bbox
    cx, cy = (x0+x1)/2, (y0+y1)/2
    rx, ry = (x1-x0)/2, (y1-y0)/2
    for i in range(steps, 0, -1):
        t = i / steps
        c = tuple(int(c_in[j]*(1-t) + c_out[j]*t) for j in range(4))
        draw.ellipse((int(cx-rx*t), int(cy-ry*t), int(cx+rx*t), int(cy+ry*t)), fill=c)


def _render_cloud(tint=None, mouth_open=False, blink_frame=False, sparkles_data=None):
    img = Image.new("RGBA", (_W, _H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ═══════════════════════════════════════
    # AURA
    # ═══════════════════════════════════════
    aura_y = _CB + (30 * _SCALE)
    _gradient_ellipse(draw,
        (_SCX - 80*_SCALE, aura_y - 30*_SCALE, _SCX + 80*_SCALE, aura_y + 30*_SCALE),
        (140, 100, 255, 120), (140, 100, 255, 0), steps=12)

    # ═══════════════════════════════════════
    # DYNAMIC SPARKLES
    # ═══════════════════════════════════════
    if sparkles_data:
        for p in sparkles_data:
            sx, sy = p['x'], p['y']
            size = p['size'] * p['scale']
            alpha = int(255 * p['opacity'])
            if alpha > 10:
                draw.ellipse((sx - size, sy - size, sx + size, sy + size), fill=(255, 255, 255, alpha))
                draw.line((sx - size*2.5, sy, sx + size*2.5, sy), fill=(255, 255, 255, int(alpha*0.6)), width=1)
                draw.line((sx, sy - size*2.5, sx, sy + size*2.5), fill=(255, 255, 255, int(alpha*0.6)), width=1)

    draw = ImageDraw.Draw(img)

    # ═══════════════════════════════════════
    # CLOUD GLOW
    # ═══════════════════════════════════════
    for i in range(8, 0, -1):
        a = int(6 * (8 - i))
        pad = (12 + i * 2) * _SCALE
        draw.rounded_rectangle(
            (_CL - pad, _CT - pad, _CR + pad, _CB + pad),
            radius=int(50*_SCALE + pad//2),
            fill=(160, 130, 255, a)
        )

    # ═══════════════════════════════════════
    # CLOUD BODY
    # ═══════════════════════════════════════
    body_mask = Image.new("L", (_W, _H), 0)
    bm_draw = ImageDraw.Draw(body_mask)
    bm_draw.rounded_rectangle((_CL, _CT, _CR, _CT + 60*_SCALE), radius=int(50*_SCALE), fill=255)
    bm_draw.rounded_rectangle((_CL, _CT + 20*_SCALE, _CR, _CB), radius=int(38*_SCALE), fill=255)
    
    body_img = Image.new("RGBA", (_W, _H), (170, 190, 240, 240))
    img.paste(body_img, mask=body_mask)
    draw = ImageDraw.Draw(img)
    
    draw.rounded_rectangle((_CL+5*_SCALE, _CT+3*_SCALE, _CR-5*_SCALE, _CB-8*_SCALE), radius=int(35*_SCALE), fill=(200, 220, 255, 200))
    draw.rounded_rectangle((_CL+8*_SCALE, _CT+2*_SCALE, _CL+80*_SCALE, _CT+40*_SCALE), radius=int(25*_SCALE), fill=(255, 255, 255, 140))
    draw.rounded_rectangle((_CL+10*_SCALE, _CB-18*_SCALE, _CR-10*_SCALE, _CB-2*_SCALE), radius=int(15*_SCALE), fill=(160, 120, 210, 45))

    # ═══════════════════════════════════════
    # BUMPS
    # ═══════════════════════════════════════
    bumps = [
        (_CL + 18*_SCALE, _CT - 26*_SCALE, 52*_SCALE, 48*_SCALE),
        (_CL + 58*_SCALE, _CT - 16*_SCALE, 38*_SCALE, 36*_SCALE),
        (_CR - 14*_SCALE - 28*_SCALE, _CT - 10*_SCALE, 28*_SCALE, 26*_SCALE),
    ]
    for bx, by, bw, bh in bumps:
        _gradient_ellipse(draw, (bx, by, bx + bw, by + bh),
            (255, 255, 255, 250), (200, 220, 255, 220), steps=10)
        draw = ImageDraw.Draw(img)
        hx, hy = bx + bw*0.35, by + bh*0.35
        draw.ellipse((hx-4*_SCALE, hy-4*_SCALE, hx+4*_SCALE, hy+4*_SCALE), fill=(255, 255, 255, 120))

    # ═══════════════════════════════════════
    # STATIC SPARKLES (dentro de la nube)
    # ═══════════════════════════════════════
    for sx, sy, ss, sc in [
        (_CL + 12*_SCALE, _CT + 18*_SCALE, 5*_SCALE, (155, 228, 255, 255)),
        (_CL + 8*_SCALE,  _CT + 30*_SCALE, 4*_SCALE, (255, 183, 245, 255)),
        (_CL + 22*_SCALE, _CT + 50*_SCALE, 4*_SCALE, (183, 228, 255, 255)),
        (_CR - 18*_SCALE - 3*_SCALE, _CT + 14*_SCALE, 3*_SCALE, (212, 183, 255, 255)),
        (_CR - 12*_SCALE - 5*_SCALE, _CT + 52*_SCALE, 5*_SCALE, (123, 191, 255, 255)),
    ]:
        draw.ellipse((sx, sy, sx + ss, sy + ss), fill=sc)

    # ═══════════════════════════════════════
    # CHEEKS
    # ═══════════════════════════════════════
    cheek_y = _CB - (20*_SCALE) - (11*_SCALE)/2
    cw_h, ch_h = 20*_SCALE, 11*_SCALE
    draw.ellipse((_CL + 13*_SCALE, cheek_y - ch_h/2, _CL + 13*_SCALE + cw_h, cheek_y + ch_h/2), fill=(255, 140, 170, 130))
    draw.ellipse((_CR - 13*_SCALE - cw_h, cheek_y - ch_h/2, _CR - 13*_SCALE, cheek_y + ch_h/2), fill=(255, 140, 170, 130))

    # ═══════════════════════════════════════
    # EYES
    # ═══════════════════════════════════════
    eye_y = _CB - (28*_SCALE) - (6*_SCALE)
    er = 6*_SCALE
    if blink_frame:
        for ex in (_CL + 27*_SCALE + er, _CR - 27*_SCALE - er):
            draw.rectangle((ex - er, eye_y - 1, ex + er, eye_y + 1), fill=(26, 10, 10, 255))
    else:
        for ex in (_CL + 27*_SCALE + er, _CR - 27*_SCALE - er):
            draw.ellipse((ex - er, eye_y - er, ex + er, eye_y + er), fill=(26, 10, 10, 255))
            draw.ellipse((ex - 3*_SCALE, eye_y - 4*_SCALE, ex - 1*_SCALE, eye_y - 1*_SCALE), fill=(255, 255, 255, 200))
            draw.ellipse((ex + 1*_SCALE, eye_y + 1*_SCALE, ex + 3*_SCALE, eye_y + 3*_SCALE), fill=(255, 255, 255, 100))

    # ═══════════════════════════════════════
    # SMILE (Very subtle animation)
    # ═══════════════════════════════════════
    smile_y = _CB - (16*_SCALE) - (4.5*_SCALE)
    sw, sh = 10*_SCALE, 5*_SCALE
    
    if mouth_open:
        # Boca abierta "un poquito" para que se vea real
        # Solo bajamos ligeramente la comisura inferior
        draw.arc((_SCX-sw, smile_y-sh*0.8, _SCX+sw, smile_y+sh*1.4), start=10, end=170, fill=(26, 10, 10, 255), width=int(2.5*_SCALE))
    else:
        # Sonrisa normal (arco cerrado)
        draw.arc((_SCX-sw, smile_y-sh, _SCX+sw, smile_y+sh), start=5, end=175, fill=(26, 10, 10, 255), width=int(2.5*_SCALE))

    if tint:
        overlay = Image.new("RGBA", (_W, _H), tint)
        alpha = img.getchannel("A")
        img = Image.alpha_composite(img, overlay)
        img.putalpha(alpha)

    return img


def _to_tk(pil_img):
    result = Image.new("RGB", pil_img.size, _TRANS_RGB)
    white = Image.new("RGB", pil_img.size, (255, 255, 255))
    white.paste(pil_img, mask=pil_img.getchannel("A"))
    mask = pil_img.getchannel("A").point(lambda a: 255 if a >= 10 else 0)
    result.paste(white, mask=mask)
    return ImageTk.PhotoImage(result)


class CloudWindow:
    def __init__(self):
        self.root = None
        self._state = "idle"
        self.STATES = ["idle", "listening", "thinking", "speaking"]
        self._talking = False
        self._drag_x = 0
        self._drag_y = 0
        self._step = 0
        self._base_y = 80
        self._base_x = None
        self._photo = None
        self._canvas = None
        self._blink_counter = 0
        self._particles = []
        for p in _SPARKLE_POSITIONS:
            self._particles.append({
                "base_x": p["x"], "base_y": p["y"],
                "target_dx": p["sx"], "target_dy": p["sy"],
                "size": random.uniform(1.8, 3.5) * _SCALE,
                "duration": random.uniform(2.5, 4.5),
                "start_time": time.time() + random.uniform(0, 3.0)
            })

    def create(self):
        self.root = tk.Tk()
        self.root.title("Nuvia")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.0)
        self.root.configure(bg=_TRANSPARENT)
        self.root.wm_attributes("-transparentcolor", _TRANSPARENT)
        self._canvas = tk.Canvas(self.root, width=_W, height=_H, bg=_TRANSPARENT, highlightthickness=0)
        self._canvas.pack()
        sw = self.root.winfo_screenwidth()
        self._base_x = sw - _W - 30
        self.root.geometry(f"{_W}x{_H}+{self._base_x}+{self._base_y}")
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._fade_in()
        self._animate()

    def start(self):
        if self.root: self.root.mainloop()

    def _fade_in(self, alpha=0.0):
        alpha = min(alpha + 0.05, 1.0)
        self.root.wm_attributes("-alpha", alpha)
        if alpha < 1.0: self.root.after(30, self._fade_in, alpha)

    def _on_press(self, e):
        self._drag_x = e.x_root - self.root.winfo_x()
        self._drag_y = e.y_root - self.root.winfo_y()

    def _on_drag(self, e):
        x, y = e.x_root - self._drag_x, e.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")
        self._base_x, self._base_y = x, y

    def _animate(self):
        self._step += 1
        now = time.time()
        current_p_data = []
        for p in self._particles:
            elapsed = now - p["start_time"]
            if elapsed < 0: continue
            progress = (elapsed % p["duration"]) / p["duration"]
            opacity = (progress / 0.1) if progress < 0.1 else (1.0 - progress)
            px = p["base_x"] + (p["target_dx"] * progress)
            py = p["base_y"] + (p["target_dy"] * progress)
            current_p_data.append({"x": px, "y": py, "opacity": opacity, "scale": 1.0 + progress, "size": p["size"]})
        
        dy = int(8 * math.sin(self._step * 0.055))
        if self._base_x is not None: self.root.geometry(f"+{self._base_x}+{self._base_y + dy}")
        self._blink_counter += 1
        blink = 118 <= self._blink_counter <= 123
        if self._blink_counter > 128: self._blink_counter = 0
        
        # Animación de boca: más aleatoria y sutil para no exagerar
        mouth = False
        if self._talking:
            # Variar la apertura de la boca con el tiempo para que no sea un toggle rígido
            mouth = (self._step % 10 < 5) and (random.random() > 0.2)
            
        tint = _TINT_LISTENING if self._state == "listening" else _TINT_THINKING if self._state == "thinking" else _TINT_SPEAKING if self._state == "speaking" else None
        
        cloud = _render_cloud(tint=tint, mouth_open=mouth, blink_frame=blink, sparkles_data=current_p_data)
        self._photo = _to_tk(cloud)
        self._canvas.delete("all")
        self._canvas.create_image(0, 0, anchor="nw", image=self._photo)
        self.root.after(40, self._animate)

    def set_state(self, state):
        if state in self.STATES: self._state = state
    def start_mouth(self): self._talking = True
    def stop_mouth(self): self._talking = False
    def close(self):
        if self.root: self.root.destroy()
