# pixel_rpg_ui.py
# ----------------------------------------------------------
# Pixelated UI demo inspired by Pokemon Deluge RPG (Pages 1–1.5)
# Controls: A/W/S/D + SPACE only
# ----------------------------------------------------------

import sys
from dataclasses import dataclass

try:
    import pygame
except Exception as e:
    print("This script requires pygame. Install with: pip install pygame")
    raise

# ----------------------
# Basic setup / constants
# ----------------------
pygame.init()
BASE_W, BASE_H = 400, 225        # low-resolution backbuffer (keeps things pixelated)
SCALE = 3                        # window scale
WIN = pygame.display.set_mode((BASE_W*SCALE, BASE_H*SCALE))
pygame.display.set_caption("Pixel RPG UI Demo")

# Colors (simple palette)
WHITE = (245, 245, 245)
BLACK = (15, 15, 15)
GRAY = (100, 100, 100)
DARKGRAY = (55, 55, 55)
ACCENT = (120, 200, 255)    # selection highlight
STONE = (170, 170, 170)

# Fonts (bitmap-ish; use monospace for chunky look)
def px_font(size):
    return pygame.font.SysFont("Courier New", size, bold=True)

TITLE_FONT = px_font(24)
H1 = px_font(14)
H2 = px_font(10)
SMALL = px_font(8)

# Game State identifiers
TITLE, SETTINGS, CREDITS, CHAR_SELECT, NAME_SELECT, NEXT_PAGE = range(6)

clock = pygame.time.Clock()

# ----------------------
# Utility helpers
# ----------------------
def draw_scaled(surface):
    """Scale our base surface to the main window to preserve chunky pixels."""
    pygame.transform.scale(surface, WIN.get_size(), WIN)

def draw_rounded_rect(surf, color, rect, radius=6):
    pygame.draw.rect(surf, color, rect, border_radius=radius)

@dataclass
class Button:
    """Simple button purely for drawing + keyboard focus highlight.
    We don't use mouse clicks to respect control constraints."""
    rect: pygame.Rect
    label: str
    long: bool = False  # styling flag (not functionally used)

    def draw(self, surf, focused=False):
        col = ACCENT if focused else WHITE
        draw_rounded_rect(surf, col, self.rect, radius=6)
        pygame.draw.rect(surf, BLACK, self.rect, 2, border_radius=6)
        txt = H1.render(self.label, True, BLACK)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

@dataclass
class Slider:
    """Keyboard-driven slider. Use A/D to change, W/S to switch focus."""
    rect: pygame.Rect
    label: str
    value: float = 0.5  # normalized 0..1

    def adjust(self, delta: float):
        self.value = max(0.0, min(1.0, self.value + delta))

    def draw(self, surf, focused=False):
        # label
        lbl = H1.render(f"{self.label}:", True, WHITE)
        surf.blit(lbl, (self.rect.x, self.rect.y - 14))
        # track
        pygame.draw.rect(surf, DARKGRAY, self.rect, 0, border_radius=3)
        pygame.draw.rect(surf, BLACK, self.rect, 1, border_radius=3)
        # handle position
        hx = int(self.rect.x + self.value * self.rect.w)
        pygame.draw.rect(surf, ACCENT, (self.rect.x, self.rect.y, hx - self.rect.x, self.rect.h), 0, border_radius=3)
        pygame.draw.rect(surf, BLACK, (hx-2, self.rect.y-2, 4, self.rect.h+4))  # small knob
        # percent text
        vtxt = H2.render(str(int(self.value*100)), True, WHITE)
        surf.blit(vtxt, (self.rect.right + 6, self.rect.y - 2))
        if focused:
            # caret to indicate keyboard focus
            pygame.draw.polygon(surf, ACCENT, [(self.rect.centerx, self.rect.bottom+4),
                                               (self.rect.centerx-4, self.rect.bottom),
                                               (self.rect.centerx+4, self.rect.bottom)])

# ----------------------
# Credits page text (EASILY EDITABLE)
# Change this list to modify the credit page without touching layout code.
# ----------------------
CREDITS_TEXT = [
    "SUBMITTED TO: SIR SEAN POLICARPIO",
    "",
    "Blablablabla about stress and strain.",
    "We wanted it to be interactive while",
    "still providing learning and enjoyment.",
    "",
    "MEMBERS:",
    "SUMAMPONG - PROGRAMMER",
    "AGUANTA - PROGRAMMER",
    "MAHUSAY - RESEARCHER",
    "DABON - ETC. ETC.",
]

# ----------------------
# Character data (simple shapes, but distinct colors)
# ----------------------
CHARS = [
    {"name": "Sprout", "body": (90, 200, 90)},
    {"name": "Ember", "body": (210, 90, 60)},
    {"name": "Aqua", "body": (70, 120, 220)},
]

selected_char = 0
typed_name = ""

# ----------------------
# Title Page widgets
# ----------------------
start_btn = Button(pygame.Rect(60, 90, 280, 26), "START", long=True)
credits_btn = Button(pygame.Rect(85, 122, 230, 22), "CREDITS", long=False)
# "rock" settings icon: a rounded pebble in top-right
settings_rect = pygame.Rect(BASE_W-36, 10, 26, 20)
title_focus_index = 0  # 0=start,1=credits,2=settings

# Settings sliders
vol_slider = Slider(pygame.Rect(80, 110, 240, 10), "VOLUME", value=0.7)
bri_slider = Slider(pygame.Rect(80, 140, 240, 10), "BRIGHTNESS", value=0.6)
settings_focus_index = 0  # 0=vol,1=bri

# ----------------------
# Drawing helpers
# ----------------------
def draw_controls_hint(surf):
    """Draw the boxes for A,W,S,D and a long rectangle for SPACE plus the word CONTROLS."""
    label = H2.render("CONTROLS", True, WHITE)
    surf.blit(label, (BASE_W-110, 70))
    key_rects = {
        "W": (BASE_W-84, 86),
        "A": (BASE_W-100, 100),
        "S": (BASE_W-84, 100),
        "D": (BASE_W-68, 100),
    }
    for k, (x, y) in key_rects.items():
        r = pygame.Rect(x, y, 14, 12)
        draw_rounded_rect(surf, WHITE, r, 3)
        pygame.draw.rect(surf, BLACK, r, 1, border_radius=3)
        t = SMALL.render(k, True, BLACK)
        surf.blit(t, t.get_rect(center=r.center))
    space_rect = pygame.Rect(BASE_W-120, 122, 90, 12)
    draw_rounded_rect(surf, WHITE, space_rect, 3)
    pygame.draw.rect(surf, BLACK, space_rect, 1, border_radius=3)
    t = SMALL.render("SPACE", True, BLACK)
    surf.blit(t, t.get_rect(center=space_rect.center))

def draw_title_page(surf):
    # background card
    draw_rounded_rect(surf, DARKGRAY, pygame.Rect(8, 8, BASE_W-16, BASE_H-16), 10)
    pygame.draw.rect(surf, BLACK, pygame.Rect(8, 8, BASE_W-16, BASE_H-16), 2, border_radius=10)
    # title
    txt = TITLE_FONT.render("GAME TITLE", True, WHITE)
    surf.blit(txt, txt.get_rect(midtop=(BASE_W//2, 34)))
    # draw buttons & focus
    start_btn.draw(surf, focused=(title_focus_index==0))
    credits_btn.draw(surf, focused=(title_focus_index==1))
    # rock settings icon
    pygame.draw.ellipse(surf, STONE, settings_rect)
    pygame.draw.ellipse(surf, BLACK, settings_rect, 2)
    gear_label = SMALL.render("⚙", True, BLACK)
    surf.blit(gear_label, gear_label.get_rect(center=settings_rect.center))
    if title_focus_index==2:
        pygame.draw.rect(surf, ACCENT, settings_rect.inflate(6,6), 2, border_radius=8)
    draw_controls_hint(surf)

def draw_settings_page(surf):
    draw_rounded_rect(surf, DARKGRAY, pygame.Rect(8, 8, BASE_W-16, BASE_H-16), 10)
    pygame.draw.rect(surf, BLACK, pygame.Rect(8, 8, BASE_W-16, BASE_H-16), 2, border_radius=10)
    vol_slider.draw(surf, focused=(settings_focus_index==0))
    bri_slider.draw(surf, focused=(settings_focus_index==1))
    h = SMALL.render("W/S: select slider   A/D: adjust   SPACE: back", True, WHITE)
    surf.blit(h, (BASE_W//2 - h.get_width()//2, BASE_H-22))

def draw_credits_page(surf):
    draw_rounded_rect(surf, DARKGRAY, pygame.Rect(8, 8, BASE_W-16, BASE_H-16), 10)
    pygame.draw.rect(surf, BLACK, pygame.Rect(8, 8, BASE_W-16, BASE_H-16), 2, border_radius=10)
    y = 30
    for line in CREDITS_TEXT:
        t = H2.render(line, True, WHITE)
        surf.blit(t, (24, y))
        y += 14
    h = SMALL.render("PRESS SPACE TO GO BACK", True, WHITE)
    surf.blit(h, (BASE_W//2 - h.get_width()//2, BASE_H-22))

def draw_character(sprite_color, pos, surf):
    """Simple 8-bit-ish person: head and body rectangles."""
    x, y = pos
    pygame.draw.rect(surf, sprite_color, (x, y+12, 20, 28))
    pygame.draw.rect(surf, BLACK, (x, y+12, 20, 28), 2)
    pygame.draw.ellipse(surf, WHITE, (x+4, y, 12, 12))
    pygame.draw.ellipse(surf, BLACK, (x+4, y, 12, 12), 2)

def draw_char_select_page(surf):
    draw_rounded_rect(surf, DARKGRAY, pygame.Rect(8, 8, BASE_W-16, BASE_H-16), 10)
    pygame.draw.rect(surf, BLACK, pygame.Rect(8, 8, BASE_W-16, BASE_H-16), 2, border_radius=10)
    centers = [BASE_W//2-60, BASE_W//2, BASE_W//2+60]
    for i, cx in enumerate(centers):
        col = CHARS[i]["body"]
        draw_character(col, (cx-10, 70), surf)
        if i == selected_char:
            pygame.draw.rect(surf, ACCENT, (cx-16, 64, 32, 48), 2)
    msg = H1.render("CHOOSE YOUR CHARACTER", True, WHITE)
    surf.blit(msg, msg.get_rect(midtop=(BASE_W//2, 30)))
    hint = SMALL.render("A/D: switch    SPACE: enter", True, WHITE)
    surf.blit(hint, hint.get_rect(midtop=(BASE_W//2, 54)))

def draw_name_page(surf):
    draw_rounded_rect(surf, DARKGRAY, pygame.Rect(8, 8, BASE_W-16, BASE_H-16), 10)
    pygame.draw.rect(surf, BLACK, pygame.Rect(8, 8, BASE_W-16, BASE_H-16), 2, border_radius=10)
    # show selected character big in center
    draw_character(CHARS[selected_char]["body"], (BASE_W//2-10, 58), surf)
    # input box
    box = pygame.Rect(60, 130, BASE_W-120, 20)
    draw_rounded_rect(surf, WHITE, box, 6)
    pygame.draw.rect(surf, BLACK, box, 2, border_radius=6)
    prompt = H2.render("ENTER NAME: ", True, BLACK)
    surf.blit(prompt, (box.x+6, box.y+3))
    name_text = H2.render(typed_name, True, BLACK)
    surf.blit(name_text, (box.x + prompt.get_width() + 6, box.y+3))
    hint = SMALL.render("PRESS SPACE TO ENTER", True, WHITE)
    surf.blit(hint, hint.get_rect(midtop=(BASE_W//2, box.bottom + 8)))

def draw_next_placeholder(surf):
    surf.fill(DARKGRAY)
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

        # ---- INPUT ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if state == TITLE:
                    if event.key in (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d):
                        # 3 focus items in a loop; any dir moves +/-1
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
                        if settings_focus_index==0:
                            vol_slider.adjust(delta)
                        else:
                            bri_slider.adjust(delta)
                    if event.key == pygame.K_SPACE:
                        state = TITLE

                elif state == CREDITS:
                    if event.key == pygame.K_SPACE:
                        state = TITLE

                elif state == CHAR_SELECT:
                    if event.key == pygame.K_a:
                        selected_char = (selected_char - 1) % len(CHARS)
                    if event.key == pygame.K_d:
                        selected_char = (selected_char + 1) % len(CHARS)
                    if event.key == pygame.K_SPACE:
                        state = NAME_SELECT

                elif state == NAME_SELECT:
                    if event.key == pygame.K_SPACE:
                        state = NEXT_PAGE
                    else:
                        # build name using printable characters; handle backspace
                        if event.key == pygame.K_BACKSPACE:
                            typed_name = typed_name[:-1]
                        else:
                            ch = event.unicode
                            if ch.isprintable() and ch != "":
                                # limit length to fit the box
                                if len(typed_name) < 16:
                                    typed_name += ch

        # ---- RENDER ----
        base.fill((30, 30, 30))

        if state == TITLE:
            draw_title_page(base)
        elif state == SETTINGS:
            draw_settings_page(base)
        elif state == CREDITS:
            draw_credits_page(base)
        elif state == CHAR_SELECT:
            draw_char_select_page(base)
        elif state == NAME_SELECT:
            draw_name_page(base)
        else:
            draw_next_placeholder(base)

        # scale and present
        pygame.transform.scale(base, WIN.get_size(), WIN)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
