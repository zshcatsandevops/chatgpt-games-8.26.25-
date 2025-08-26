
import sys
import math
import random
from array import array

import pygame

# -----------------------------
# Config
# -----------------------------
WIDTH, HEIGHT = 600, 400
FPS = 60
TITLE = "Breakout — Neon catsama's version 1.0x (mouse controls, 60 FPS, no files)"
BRICK_ROWS = 6
BRICK_COLS = 10
BRICK_MARGIN = 4
PADDLE_W, PADDLE_H = 90, 12
BALL_RADIUS = 7
START_LIVES = 3

# Audio config (must match mixer.init below)
AUDIO_RATE = 44100
AUDIO_SIZE = -16   # signed 16-bit
AUDIO_CHANNELS = 1
AUDIO_BUFFER = 256

# Visual toggles
ENABLE_TRAIL = True
ENABLE_PARTICLES = True
ENABLE_SHAKE = True
ENABLE_GLOW = True


# -----------------------------
# Helpers
# -----------------------------
def clamp(x, a, b):
    return a if x < a else b if x > b else x


def vec_length(x, y):
    return math.hypot(x, y)


def lerp(a, b, t):
    return a + (b - a) * t


# -----------------------------
# Procedural audio (no files)
# -----------------------------
def make_tone(freq=440.0, duration=0.08, volume=0.35, wave="sine"):
    """
    Generate a pygame Sound in-memory (no files), mono 16-bit at AUDIO_RATE.
    A short fade-in/out envelope is applied to avoid clicks.
    """
    n_samples = int(duration * AUDIO_RATE)
    # Attack/decay envelope (first/last 8 ms)
    fade = int(0.008 * AUDIO_RATE)
    samples = array('h')
    two_pi_f = 2.0 * math.pi * freq
    for i in range(n_samples):
        t = i / AUDIO_RATE
        if wave == "sine":
            s = math.sin(two_pi_f * t)
        elif wave == "square":
            s = 1.0 if math.sin(two_pi_f * t) >= 0 else -1.0
        elif wave == "tri":
            # Triangle via arcsin(sin)
            s = (2.0 / math.pi) * math.asin(math.sin(two_pi_f * t))
        else:
            s = math.sin(two_pi_f * t)

        # Gentle harmonic spice to feel a bit "next-gen"
        s *= 0.82
        s += 0.18 * math.sin(2 * two_pi_f * t)

        # Envelope
        env = 1.0
        if i < fade:
            env = i / fade
        elif i > n_samples - fade:
            env = (n_samples - i) / fade
        val = int(max(-1.0, min(1.0, s * env * volume)) * 32767)
        samples.append(val)

    # Pygame can build a Sound from a raw PCM buffer
    return pygame.mixer.Sound(buffer=samples.tobytes())


def load_sounds():
    return {
        "paddle": make_tone(880, 0.05, 0.35, "tri"),
        "brick": make_tone(660, 0.06, 0.32, "sine"),
        "wall": make_tone(520, 0.04, 0.28, "square"),
        "lost": make_tone(180, 0.35, 0.30, "sine"),
        "win": make_tone(1040, 0.25, 0.35, "tri"),
        "launch": make_tone(740, 0.05, 0.30, "sine"),
    }


# -----------------------------
# Visuals
# -----------------------------
def make_gradient(size, top_color, bottom_color):
    """Vertical gradient surface."""
    w, h = size
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(lerp(top_color[0], bottom_color[0], t))
        g = int(lerp(top_color[1], bottom_color[1], t))
        b = int(lerp(top_color[2], bottom_color[2], t))
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
    return surf


def radial_glow(radius, color):
    """Create a radial glow surface with per-pixel alpha."""
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    r, g, b = color
    for i in range(radius, 0, -1):
        alpha = int(255 * (i / radius) ** 2)
        pygame.draw.circle(surf, (r, g, b, int(alpha * 0.4)), (radius, radius), i)
    return surf


def draw_text(surface, text, pos, size=20, color=(240, 245, 255), alpha=255):
    font = pygame.font.SysFont("arial", size, bold=True)
    x, y = pos
    shadow = font.render(text, True, (20, 30, 40))
    surface.blit(shadow, (x + 1, y + 2))
    label = font.render(text, True, color)
    if alpha != 255:
        label.set_alpha(alpha)
    surface.blit(label, pos)


# -----------------------------
# Game objects
# -----------------------------
class Paddle:
    def __init__(self, y):
        self.w = PADDLE_W
        self.h = PADDLE_H
        self.x = WIDTH / 2 - self.w / 2
        self.y = y
        self.speed = 1400.0  # for potential keyboard control, unused here

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update_mouse(self):
        mx, _ = pygame.mouse.get_pos()
        self.x = clamp(mx - self.w / 2, 0, WIDTH - self.w)

    def draw(self, surface, glow=None):
        # Base
        pygame.draw.rect(surface, (220, 240, 255), self.rect, border_radius=6)
        pygame.draw.rect(surface, (80, 180, 255), self.rect.inflate(0, -6), border_radius=6)
        # Glow
        if glow is not None and ENABLE_GLOW:
            gx = self.rect.centerx - glow.get_width() // 2
            gy = self.rect.centery - glow.get_height() // 2
            surface.blit(glow, (gx, gy), special_flags=pygame.BLEND_ADD)


class Ball:
    def __init__(self):
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.r = BALL_RADIUS
        angle = random.uniform(-math.pi / 4, math.pi / 4) - math.pi / 2
        speed = 260.0
        self.vx = speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        self.trail = []
        self.stuck = True  # start on paddle

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.r), int(self.y - self.r), self.r * 2, self.r * 2)

    def speed(self):
        return math.hypot(self.vx, self.vy)

    def set_speed(self, s):
        curr = self.speed()
        if curr == 0:
            self.vx, self.vy = 0, -s
        else:
            k = s / curr
            self.vx *= k
            self.vy *= k

    def update(self, dt):
        # Trail
        if ENABLE_TRAIL:
            self.trail.append((self.x, self.y))
            if len(self.trail) > 14:
                self.trail.pop(0)
        # Move
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface, glow=None):
        # Trail
        if ENABLE_TRAIL:
            for i, (tx, ty) in enumerate(self.trail):
                a = int(255 * (i / max(1, len(self.trail))) * 0.25)
                pygame.draw.circle(surface, (200, 230, 255, a), (int(tx), int(ty)), self.r)

        # Core
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surface, (60, 180, 255), (int(self.x), int(self.y)), max(1, self.r - 2))
        # Glow
        if glow is not None and ENABLE_GLOW:
            gx = int(self.x - glow.get_width() // 2)
            gy = int(self.y - glow.get_height() // 2)
            surface.blit(glow, (gx, gy), special_flags=pygame.BLEND_ADD)


class Brick:
    def __init__(self, rect, color):
        self.rect = rect
        self.color = color
        self.alive = True

    def draw(self, surface, glow=None):
        if not self.alive:
            return
        pygame.draw.rect(surface, (230, 240, 255), self.rect, border_radius=6)
        inner = self.rect.inflate(-6, -6)
        pygame.draw.rect(surface, self.color, inner, border_radius=6)
        if glow is not None and ENABLE_GLOW:
            gx = self.rect.centerx - glow.get_width() // 2
            gy = self.rect.centery - glow.get_height() // 2
            surface.blit(glow, (gx, gy), special_flags=pygame.BLEND_ADD)


class Particle:
    def __init__(self, x, y, color):
        ang = random.uniform(0, 2 * math.pi)
        speed = random.uniform(40, 200)
        self.vx = math.cos(ang) * speed
        self.vy = math.sin(ang) * speed
        self.x = x
        self.y = y
        self.life = random.uniform(0.25, 0.6)
        self.color = color

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 300 * dt * 0.2  # tiny gravity
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0:
            return
        a = int(255 * clamp(self.life / 0.6, 0, 1))
        pygame.draw.circle(surface, (*self.color, a), (int(self.x), int(self.y)), 2)


# -----------------------------
# Level building
# -----------------------------
def build_level(rows, cols, top=50, bottom=HEIGHT // 2):
    bricks = []
    # Colors: neon gradient per row
    palette = [
        (255, 80, 150),
        (255, 120, 90),
        (255, 190, 60),
        (120, 220, 90),
        (90, 200, 255),
        (140, 120, 255),
    ]
    margin_x = 20
    total_w = WIDTH - margin_x * 2
    brick_w = (total_w - (cols - 1) * BRICK_MARGIN) // cols
    brick_h = 20
    y = top
    for r in range(rows):
        x = margin_x
        color = palette[r % len(palette)]
        for c in range(cols):
            rect = pygame.Rect(x, y, brick_w, brick_h)
            bricks.append(Brick(rect, color))
            x += brick_w + BRICK_MARGIN
        y += brick_h + BRICK_MARGIN
    return bricks


# -----------------------------
# Collision utilities
# -----------------------------
def reflect_velocity_over_normal(vx, vy, nx, ny):
    # v' = v - 2*(v·n)*n
    dot = vx * nx + vy * ny
    rx = vx - 2 * dot * nx
    ry = vy - 2 * dot * ny
    return rx, ry


def circle_rect_collision(cx, cy, r, rect):
    # Find closest point on rect to circle center
    closest_x = clamp(cx, rect.left, rect.right)
    closest_y = clamp(cy, rect.top, rect.bottom)
    dx = cx - closest_x
    dy = cy - closest_y
    dist2 = dx * dx + dy * dy
    if dist2 <= r * r:
        dist = math.sqrt(dist2) if dist2 > 0 else 0.0001
        nx, ny = dx / dist, dy / dist
        penetration = r - dist
        return True, nx, ny, penetration
    return False, 0, 0, 0


# -----------------------------
# Main game
# -----------------------------
def main():
    # Init pygame
    pygame.mixer.pre_init(AUDIO_RATE, AUDIO_SIZE, AUDIO_CHANNELS, AUDIO_BUFFER)
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Audio
    try:
        pygame.mixer.init(AUDIO_RATE, AUDIO_SIZE, AUDIO_CHANNELS, AUDIO_BUFFER)
        sounds = load_sounds()
    except pygame.error:
        sounds = {k: None for k in ["paddle", "brick", "wall", "lost", "win", "launch"]}

    # Background + glow
    bg = make_gradient((WIDTH, HEIGHT), (8, 14, 28), (12, 22, 36))
    paddle_glow = radial_glow(48, (90, 200, 255))
    ball_glow = radial_glow(36, (120, 220, 255))
    brick_glow = radial_glow(40, (255, 180, 120))

    # Game objects/state
    paddle = Paddle(HEIGHT - 40)
    ball = Ball()
    lives = START_LIVES
    score = 0
    level = 1
    bricks = build_level(BRICK_ROWS, BRICK_COLS)
    particles = []
    shake = 0.0
    running = True

    # Attach ball to paddle initially
    def stick_ball_to_paddle():
        ball.x = paddle.rect.centerx
        ball.y = paddle.rect.top - ball.r - 1
        ball.vx, ball.vy = 0, -260
        ball.stuck = True

    stick_ball_to_paddle()

    while running:
        dt = clock.tick(FPS) / 1000.0

        # --- Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # Hard reset
                    lives = START_LIVES
                    score = 0
                    level = 1
                    bricks = build_level(BRICK_ROWS, BRICK_COLS)
                    particles.clear()
                    stick_ball_to_paddle()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if ball.stuck:
                    ball.stuck = False
                    # give slight upward impulse
                    ball.vx = random.uniform(-80, 80)
                    ball.vy = -260
                    if sounds.get("launch"):
                        sounds["launch"].play()

        # --- Update
        paddle.update_mouse()

        if ball.stuck:
            ball.x = paddle.rect.centerx
            ball.y = paddle.rect.top - ball.r - 1
        else:
            # Keep speed roughly constant; increase slightly over time
            target_speed = clamp(260 + (level - 1) * 15 + score * 0.02, 260, 520)
            ball.set_speed(target_speed)
            ball.update(dt)

            # Wall collisions
            hit_wall = False
            if ball.x - ball.r <= 0:
                ball.x = ball.r
                ball.vx = abs(ball.vx)
                hit_wall = True
            elif ball.x + ball.r >= WIDTH:
                ball.x = WIDTH - ball.r
                ball.vx = -abs(ball.vx)
                hit_wall = True
            if ball.y - ball.r <= 0:
                ball.y = ball.r
                ball.vy = abs(ball.vy)
                hit_wall = True
            if hit_wall and sounds.get("wall"):
                sounds["wall"].play()

            # Bottom (lose life)
            if ball.y - ball.r > HEIGHT:
                lives -= 1
                if sounds.get("lost"):
                    sounds["lost"].play()
                if lives <= 0:
                    # Reset everything
                    lives = START_LIVES
                    score = 0
                    level = 1
                    bricks = build_level(BRICK_ROWS, BRICK_COLS)
                    particles.clear()
                stick_ball_to_paddle()

            # Paddle collision
            collided, nx, ny, pen = circle_rect_collision(ball.x, ball.y, ball.r, paddle.rect)
            if collided and ball.vy > 0:
                # Reflect and add "english" based on where it hit on the paddle
                cx = paddle.rect.centerx
                offset = (ball.x - cx) / (paddle.w * 0.5)  # -1..1
                angle = lerp(-math.pi * 0.75, -math.pi * 0.25, (offset + 1) / 2)
                speed = max(260, ball.speed())
                ball.vx = math.cos(angle) * speed
                ball.vy = math.sin(angle) * speed
                ball.y -= (pen + 0.5)
                if sounds.get("paddle"):
                    sounds["paddle"].play()
                if ENABLE_SHAKE:
                    shake = 0.08

            # Brick collisions
            if not ball.stuck:
                # Only handle one brick per frame for simplicity
                random.shuffle(bricks)  # small randomization to reduce tunneling patterns
                for br in bricks:
                    if not br.alive:
                        continue
                    collided, nx, ny, pen = circle_rect_collision(ball.x, ball.y, ball.r, br.rect)
                    if collided:
                        br.alive = False
                        score += 10
                        # Reflect
                        ball.vx, ball.vy = reflect_velocity_over_normal(ball.vx, ball.vy, nx, ny)
                        ball.x += nx * (pen + 0.6)
                        ball.y += ny * (pen + 0.6)
                        if sounds.get("brick"):
                            sounds["brick"].play()
                        if ENABLE_SHAKE:
                            shake = max(shake, 0.06)
                        if ENABLE_PARTICLES:
                            bx, by = br.rect.center
                            for _ in range(14):
                                particles.append(Particle(bx, by, br.color))
                        break

            # Level clear?
            if all(not b.alive for b in bricks):
                level += 1
                if sounds.get("win"):
                    sounds["win"].play()
                # Build a slightly denser level as we go (up to 9 rows)
                rows = clamp(BRICK_ROWS + level - 1, 6, 9)
                bricks = build_level(rows, BRICK_COLS)
                stick_ball_to_paddle()

        # Particles
        if ENABLE_PARTICLES:
            particles = [p for p in particles if p.life > 0]
            for p in particles:
                p.update(dt)

        # Camera shake
        cam_offset = (0, 0)
        if ENABLE_SHAKE and shake > 0:
            sx = random.uniform(-1, 1) * 6 * shake
            sy = random.uniform(-1, 1) * 6 * shake
            cam_offset = (int(sx), int(sy))
            shake = max(0.0, shake - dt * 2.6)

        # --- Render
        screen.blit(bg, (0, 0))

        # "PS5-ish" subtle vignette
        vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 40), (0, 0, WIDTH, HEIGHT), border_radius=30)
        screen.blit(vignette, (0, 0))

        # Translate by camera shake
        world = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # Draw bricks
        for b in bricks:
            b.draw(world, brick_glow)

        # Draw paddle and ball
        paddle.draw(world, paddle_glow)
        ball.draw(world, ball_glow)

        # Particles (additive)
        if ENABLE_PARTICLES:
            for p in particles:
                p.draw(world)

        screen.blit(world, cam_offset)

        # HUD
        draw_text(screen, f"Score: {score}", (12, 8), size=20)
        draw_text(screen, f"Lives: {lives}", (WIDTH - 120, 8), size=20)
        if ball.stuck:
            draw_text(screen, "Move mouse. Click to launch.  [R]estart  [Esc] Quit", (WIDTH//2 - 220, HEIGHT - 28), size=16, color=(210, 230, 255))

        # Flip
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
