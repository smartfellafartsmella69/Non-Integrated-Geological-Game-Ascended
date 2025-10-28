# pixel_rpg_ui_sprites.py
# ----------------------------------------------------------
# Pixelated UI demo (Pages 1–1.5) with image backgrounds and
# character sprite images supplied by the user.
# Controls: A/W/S/D + SPACE only
# ----------------------------------------------------------

import os
import sys
from dataclasses import dataclass

try:
    import pygame
except Exception:
    print("This script requires pygame. Install with: pip install pygame")
    raise

# ----------------------
# Configuration: drop your images beside this file
# Rename your assets to match these filenames OR edit here.
# ----------------------
ASSETS = {
    "bg_title":      "bg_title.png",      # title screen background
    "bg_settings":   "bg_settings.png",   # settings page background
    "bg_credits":    "bg_credits.png",    # credits page background
    "bg_char":       "bg_char.png",       # character select background
    "bg_name":       "bg_name.png",       # name entry background
    "rock":          "rock.png",          # small rock icon (used as slider knob + settings pebble)
    "char1":         "char1.png",         # character sprite (PNG with transparency)
    "char2":         "char2.png",
    "char3":         "char3.png",
}

# Tip: If you only have one global background, just duplicate it 5x or
# point all bg_* keys to the same filename.


# ----------------------
# Basic setup / constants
# ----------------------
pygame.init()
BASE_W, BASE_H = 400, 225        # low-resolution backbuffer (keeps things pixelated)
SCALE = 3                        # window scale
WIN = pygame.display.set_mode((BASE_W*SCALE, BASE_H*SCALE))
pygame.display.set_caption("Pixel RPG UI (Images)")

# Colors (simple palette)
WHITE = (245, 245, 245)
BLACK = (15, 15, 15)
UI_BROWN = (125, 77, 52)
UI_BROWN_DARK = (80, 46, 33)
UI_PANEL = (118, 83, 63)
ACCENT = (255, 255, 255)

# Fonts (monospace for retro look)
def px_font(size, bold=True):
    return pygame.font.SysFont("Consolas", size, bold=bold)

TITLE_FONT = px_font(28)
H1 = px_font(16)
H2 = px_font(12)
SMALL = px_font(10, bold=False)

# States
TITLE, SETTINGS, CREDITS, CHAR_SELECT, NAME_SELECT, NEXT_PAGE = range(6)
clock = pygame.time.Clock()

# ----------------------
# Image loading helpers
# ----------------------
def try_load_image(name_key):
    """Load an image if present; return None if missing."""
    fn = ASSETS[name_key]
    if os.path.exists(fn):
        img = pygame.image.load(fn).convert_alpha()
        return img
    return None

def fit_to_base(img):
    """Scale an image to fill BASE_W x BASE_H (preserve pixel look; integer scaling)."""
    if img is None:
        return None
    iw, ih = img.get_width(), img.get_height()
    sx = BASE_W / iw
    sy = BASE_H / ih
    s = max(sx, sy)
    s = max(1, int(s + 0.5))
    scaled = pygame.transform.scale(img, (int(iw * s), int(ih * s)))
    surf = pygame.Surface((BASE_W, BASE_H), pygame.SRCALPHA)
    x = (scaled.get_width() - BASE_W) // 2
    y = (scaled.get_height() - BASE_H) // 2
    surf.blit(scaled, (-x, -y))
    return surf

def fit_height(img, target_h):
    """Scale image to a target height keeping aspect ratio (pixel-preserving)."""
    iw, ih = img.get_width(), img.get_height()
    s = target_h / ih
    s = max(1, int(s + 0.5))
    new = pygame.transform.scale(img, (int(iw * s), int(ih * s)))
    return new

# Load backgrounds (graceful fallback: if missing, use flat color)
BG = {
    "title":    fit_to_base(try_load_image("bg_title")),
    "settings": fit_to_base(try_load_image("bg_settings")),
    "credits":  fit_to_base(try_load_image("bg_credits")),
    "char":     fit_to_base(try_load_image("bg_char")),
    "name":     fit_to_base(try_load_image("bg_name")),
}
ROCK = try_load_image("rock")

# Characters (allow missing; if missing we show placeholder boxes)
CHAR_IMGS = []
for key in ("char1", "char2", "char3"):
    img = try_load_image(key)
    if img is not None:
        CHAR_IMGS.append(img)
    else:
        CHAR_IMGS.append(None)

# ----------------------
# Credits content (editable)
# ----------------------
CREDITS_LEFT = [
    "(Game Name) is a pixelated RPG adventure where you and",
    "your friends are transported into the world of Materials",
    "Science, exploring concepts like stress and strain through",
    "interactive challenges. Using the knowledge you gain, you'll",
    "overcome obstacles such as crushing walls and collapsing",
    "paths, all while enjoying fun, retro-style gameplay inspired",
    "by Pokemon Deluge RPG.",
]
CREDITS_RIGHT = [
    "PROGRAMMERS & RESEARCHER",
    "  Sumampong",
    "  Aguanta",
    "  Mahusay",
    "",
    "VOICE ACTORS",
    "  Dabon .......... Mean Girl",
    "  Bungcaras ...... Jock",
    "  Esolana ........ Nerd",
    "  Rennier ........ Class Clown",
    "  Gines .......... Seismologist",
    "",
    "GRAPHICS",
    "  All Members",
]

# ----------------------
# UI components
# ----------------------
@dataclass
class Button:
    rect: pygame.Rect
    label: str
    long: bool = False

    def draw(self, surf, focused=False):
        pygame.draw.rect(surf, UI_BROWN, self.rect, border_radius=10)
        pygame.draw.rect(surf, UI_BROWN_DARK, self.rect, 6, border_radius=10)
        txt = H1.render(self.label, True, WHITE)
        surf.blit(txt, txt.get_rect(center=self.rect.center))
        if focused:
            pygame.draw.rect(surf, WHITE, self.rect.inflate(6,6), 2, border_radius=12)

@dataclass
class Slider:
    rect: pygame.Rect
    label: str
    value: float = 0.5

    def adjust(self, delta: float):
        self.value = max(0.0, min(1.0, self.value + delta))

    def draw(self, surf, focused=False):
        # Label
        surf.blit(H1.render(self.label + ":", True, WHITE), (self.rect.x, self.rect.y - 26))
        # Track
        track = pygame.Rect(self.rect.x, self.rect.y, self.rect.w, 18)
        pygame.draw.rect(surf, UI_BROWN_DARK, track, border_radius=12)
        inner = pygame.Rect(track.x+6, track.y+4, track.w-12, track.h-8)
        pygame.draw.rect(surf, WHITE, inner, border_radius=12)
        # Knob (rock image or oval)
        knob_x = int(inner.x + self.value * (inner.w - 20))
        knob = pygame.Rect(knob_x, inner.y-4, 28, inner.h+8)
        if ROCK:
            rock_scaled = fit_height(ROCK, inner.h+6)
            surf.blit(rock_scaled, rock_scaled.get_rect(center=knob.center))
        else:
            pygame.draw.ellipse(surf, (200,200,200), knob)
            pygame.draw.ellipse(surf, BLACK, knob, 2)
        if focused:
            pygame.draw.rect(surf, WHITE, inner.inflate(6,6), 1, border_radius=14)

# ----------------------
# Widgets and state
# ----------------------
start_btn = Button(pygame.Rect(60, 110, 280, 30), "START", long=True)
credits_btn = Button(pygame.Rect(85, 146, 230, 26), "CREDITS", long=False)
settings_rock_rect = pygame.Rect(18, 14, 26, 22)  # top-left pebble

title_focus_index = 0  # 0=start,1=credits,2=settings
vol_slider = Slider(pygame.Rect(56, 90, 288, 18), "VOLUME", 0.7)
bri_slider = Slider(pygame.Rect(56, 140, 288, 18), "BRIGHTNESS", 0.6)
settings_focus_index = 0

selected_char = 0
typed_name = ""

# ----------------------
# Drawing helpers
# ----------------------
def draw_bg(surf, name):
    if BG[name] is None:
        surf.fill((60, 60, 60))
    else:
        surf.blit(BG[name], (0,0))

def draw_controls_hint(surf):
    hint = SMALL.render("W/S/A/D: NAV   SPACE: SELECT", True, WHITE)
    surf.blit(hint, (BASE_W - hint.get_width() - 10, BASE_H - 18))

def draw_title(surf):
    draw_bg(surf, "title")
    t = TITLE_FONT.render("GAME", True, WHITE)
    surf.blit(t, t.get_rect(center=(BASE_W//2, 62)))
    start_btn.draw(surf, focused=(title_focus_index==0))
    credits_btn.draw(surf, focused=(title_focus_index==1))
    if ROCK:
        r = fit_height(ROCK, settings_rock_rect.h)
        surf.blit(r, r.get_rect(center=settings_rock_rect.center))
    else:
        pygame.draw.ellipse(surf, (170,170,170), settings_rock_rect)
        pygame.draw.ellipse(surf, BLACK, settings_rock_rect, 2)
    if title_focus_index==2:
        pygame.draw.rect(surf, WHITE, settings_rock_rect.inflate(8,8), 2, border_radius=8)
    draw_controls_hint(surf)

def draw_settings(surf):
    draw_bg(surf, "settings")
    panel = pygame.Rect(26, 56, BASE_W-52, 120)
    pygame.draw.rect(surf, UI_PANEL, panel, border_radius=16)
    pygame.draw.rect(surf, UI_BROWN_DARK, panel, 6, border_radius=16)
    head = H1.render("SETTINGS", True, WHITE)
    head_box = pygame.Rect(0, 20, 190, 28)
    head_box.centerx = BASE_W//2
    pygame.draw.rect(surf, UI_BROWN, head_box, border_radius=12)
    pygame.draw.rect(surf, UI_BROWN_DARK, head_box, 4, border_radius=12)
    surf.blit(head, head.get_rect(center=head_box.center))
    vol_slider.draw(surf, focused=(settings_focus_index==0))
    bri_slider.draw(surf, focused=(settings_focus_index==1))
    surf.blit(SMALL.render("W/S: SELECT SLIDER   A/D: ADJUST   SPACE: BACK", True, WHITE),
              (BASE_W//2-150, BASE_H-20))

def draw_credits(surf):
    draw_bg(surf, "credits")
    head = H1.render("CREDITS", True, WHITE)
    head_box = pygame.Rect(0, 20, 190, 28)
    head_box.centerx = BASE_W//2
    pygame.draw.rect(surf, UI_BROWN, head_box, border_radius=12)
    pygame.draw.rect(surf, UI_BROWN_DARK, head_box, 4, border_radius=12)
    surf.blit(head, head.get_rect(center=head_box.center))
    left = pygame.Rect(20, 60, BASE_W//2-25, 120)
    right = pygame.Rect(BASE_W//2+5, 60, BASE_W//2-25, 120)
    for rect in (left, right):
        pygame.draw.rect(surf, UI_PANEL, rect, border_radius=12)
        pygame.draw.rect(surf, UI_BROWN_DARK, rect, 4, border_radius=12)
    y = left.y + 10
    for line in CREDITS_LEFT:
        surf.blit(SMALL.render(line, True, WHITE), (left.x+10, y))
        y += 14
    y = right.y + 8
    for line in CREDITS_RIGHT:
        surf.blit(SMALL.render(line, True, WHITE), (right.x+10, y))
        y += 14
    sub = H2.render("SUBMITTED TO: SIR SEAN POLICARPIO", True, WHITE)
    surf.blit(sub, (BASE_W//2 - sub.get_width()//2, BASE_H - 22))
    surf.blit(SMALL.render("SPACE: BACK", True, WHITE), (10, BASE_H-20))

def draw_char_card(surf, img, centerx, selected=False):
    card = pygame.Rect(0, 0, 84, 132)
    card.centerx = centerx
    card.centery = BASE_H//2 + 12
    pygame.draw.rect(surf, (10,10,10), card, border_radius=6)
    if img is None:
        pygame.draw.rect(surf, (80,80,80), card.inflate(-8,-8), 2, border_radius=6)
    else:
        sprite = fit_height(img, 110)
        surf.blit(sprite, sprite.get_rect(center=card.center))
    if selected:
        pygame.draw.rect(surf, WHITE, card.inflate(6,6), 2, border_radius=8)

def draw_char_select(surf, selected_index):
    draw_bg(surf, "char")
    head_box = pygame.Rect(0, 16, 300, 28)
    head_box.centerx = BASE_W//2
    pygame.draw.rect(surf, UI_BROWN, head_box, border_radius=12)
    pygame.draw.rect(surf, UI_BROWN_DARK, head_box, 4, border_radius=12)
    lab = H1.render("CHOOSE YOUR CHARACTER", True, WHITE)
    surf.blit(lab, lab.get_rect(center=head_box.center))
    centers = [BASE_W//2-90, BASE_W//2, BASE_W//2+90]
    for i, cx in enumerate(centers):
        draw_char_card(surf, CHAR_IMGS[i], cx, selected=(i==selected_index))
    foot = H2.render("A/D: SWITCH     SPACE: ENTER", True, WHITE)
    surf.blit(foot, foot.get_rect(center=(BASE_W//2, BASE_H-18)))

def draw_name_page(surf, selected_index, typed):
    draw_bg(surf, "name")
    draw_char_card(surf, CHAR_IMGS[selected_index], BASE_W//2, selected=False)
    box = pygame.Rect(26, BASE_H-72, BASE_W-52, 28)
    pygame.draw.rect(surf, UI_BROWN, box, border_radius=14)
    pygame.draw.rect(surf, UI_BROWN_DARK, box, 6, border_radius=14)
    prompt = H1.render("ENTER  NAME:", True, WHITE)
    surf.blit(prompt, (box.x+12, box.y+4))
    name_txt = H1.render(typed, True, WHITE)
    surf.blit(name_txt, (box.x + 170, box.y+4))
    hint = H2.render("PRESS  SPACE  TO  ENTER", True, WHITE)
    surf.blit(hint, hint.get_rect(center=(BASE_W//2, BASE_H-18)))

def draw_next_placeholder(surf):
    surf.fill((20,20,20))
    t = H1.render("NEXT PAGE PLACEHOLDER", True, WHITE)
    surf.blit(t, t.get_rect(center=(BASE_W//2, BASE_H//2)))

# ----------------------
# Main loop
# ----------------------
def main():
    global title_focus_index, settings_focus_index, selected_char, typed_name
    state = TITLE
    running = True
    base = pygame.Surface((BASE_W, BASE_H))

    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if state == TITLE:
                    if event.key in (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d):
                        delta = -1 if event.key in (pygame.K_a, pygame.K_w) else 1
                        title_focus_index = (title_focus_index + delta) % 3
                    if event.key == pygame.K_SPACE:
                        if title_focus_index == 0:
                            state = CHAR_SELECT
                        elif title_focus_index == 1:
                            state = CREDITS
                        elif title_focus_index == 2:
                            state = SETTINGS

                elif state == SETTINGS:
                    if event.key in (pygame.K_w, pygame.K_s):
                        settings_focus_index = (settings_focus_index + (-1 if event.key==pygame.K_w else 1)) % 2
                    if event.key in (pygame.K_a, pygame.K_d):
                        delta = -0.05 if event.key==pygame.K_a else 0.05
                        (vol_slider if settings_focus_index==0 else bri_slider).adjust(delta)
                    if event.key == pygame.K_SPACE:
                        state = TITLE

                elif state == CREDITS:
                    if event.key == pygame.K_SPACE:
                        state = TITLE

                elif state == CHAR_SELECT:
                    if event.key == pygame.K_a:
                        selected_char = (selected_char - 1) % 3
                    if event.key == pygame.K_d:
                        selected_char = (selected_char + 1) % 3
                    if event.key == pygame.K_SPACE:
                        state = NAME_SELECT

                elif state == NAME_SELECT:
                    if event.key == pygame.K_SPACE:
                        state = NEXT_PAGE
                    elif event.key == pygame.K_BACKSPACE:
                        typed_name = typed_name[:-1]
                    else:
                        ch = event.unicode
                        if ch.isprintable() and ch != "":
                            if len(typed_name) < 16:
                                typed_name += ch

        if state == TITLE:
            draw_title(base)
        elif state == SETTINGS:
            draw_settings(base)
        elif state == CREDITS:
            draw_credits(base)
        elif state == CHAR_SELECT:
            draw_char_select(base, selected_char)
        elif state == NAME_SELECT:
            draw_name_page(base, selected_char, typed_name)
        else:
            draw_next_placeholder(base)

        pygame.transform.scale(base, WIN.get_size(), WIN)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

