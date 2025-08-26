import pygame
import sys

# Initialize Pygame
pygame.init()

# Display configuration
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Mario World - CatSama Edition")

# Colors
SKY_BLUE = (107, 140, 255)
GREEN = (0, 168, 0)
BROWN = (180, 122, 48)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BROWN = (101, 67, 33)
GRAY = (128, 128, 128)
DARK_BLUE = (0, 0, 128)

# Game states
OVERWORLD = 0
LEVEL = 1
game_state = OVERWORLD
current_level_index = 0

# Player properties
player_pos = [100, 100]
player_vel = [0, 0]
player_acc = 0.5
player_friction = -0.12
player_jump_strength = -12
player_gravity = 0.5
player_rect = pygame.Rect(player_pos[0], player_pos[1], 20, 32)
player_on_ground = False
player_score = 0
player_lives = 3

# Level data
levels = [
    {"x": 100, "y": 100, "width": 40, "height": 40, "color": GREEN, "completed": False,
     "name": "Grass Land", "theme": "grass", "rect": pygame.Rect(100, 100, 40, 40)},
    {"x": 200, "y": 150, "width": 40, "height": 40, "color": DARK_BROWN, "completed": False,
     "name": "Underground", "theme": "underground", "rect": pygame.Rect(200, 150, 40, 40)},
    {"x": 300, "y": 200, "width": 40, "height": 40, "color": SKY_BLUE, "completed": False,
     "name": "Sky World", "theme": "sky", "rect": pygame.Rect(300, 200, 40, 40)},
    {"x": 400, "y": 250, "width": 40, "height": 40, "color": GRAY, "completed": False,
     "name": "Castle", "theme": "castle", "rect": pygame.Rect(400, 250, 40, 40)},
    {"x": 500, "y": 300, "width": 40, "height": 40, "color": DARK_BLUE, "completed": False,
     "name": "Water World", "theme": "water", "rect": pygame.Rect(500, 300, 40, 40)},
]

# Paths between levels
paths = [
    (levels[0], levels[1]),
    (levels[1], levels[2]),
    (levels[2], levels[3]),
    (levels[3], levels[4]),
]

# Level-specific data (platforms, enemies, coins)
level_data = {
    "grass": {
        "platforms": [
            pygame.Rect(0, 400, SCREEN_WIDTH, 200),  # Ground
            pygame.Rect(100, 350, 50, 50),  # Block
            pygame.Rect(200, 300, 50, 50),  # Block
            pygame.Rect(600, 350, 50, 50),  # Block near end
        ],
        "enemies": [
            {"rect": pygame.Rect(300, 368, 20, 32), "speed": 2, "direction": 1},
            {"rect": pygame.Rect(500, 368, 20, 32), "speed": 2, "direction": -1},
        ],
        "coins": [
            pygame.Rect(150, 320, 16, 16),
            pygame.Rect(250, 270, 16, 16),
            pygame.Rect(350, 350, 16, 16),
            pygame.Rect(600, 320, 16, 16),
        ],
    },
    "underground": {
        "platforms": [
            pygame.Rect(0, 400, SCREEN_WIDTH, 200),  # Ground
            pygame.Rect(150, 350, 100, 50),  # Platform
            pygame.Rect(500, 300, 100, 50),  # Platform
        ],
        "enemies": [
            {"rect": pygame.Rect(400, 368, 20, 32), "speed": 2, "direction": 1},
            {"rect": pygame.Rect(600, 268, 20, 32), "speed": 2, "direction": -1},
        ],
        "coins": [
            pygame.Rect(200, 320, 16, 16),
            pygame.Rect(300, 320, 16, 16),
            pygame.Rect(550, 270, 16, 16),
        ],
    },
    "sky": {
        "platforms": [
            pygame.Rect(100, 350, 100, 20),  # Cloud platform
            pygame.Rect(300, 300, 100, 20),
            pygame.Rect(500, 250, 100, 20),
            pygame.Rect(700, 350, 100, 20),
        ],
        "enemies": [
            {"rect": pygame.Rect(200, 318, 20, 32), "speed": 2, "direction": 1},
        ],
        "coins": [
            pygame.Rect(150, 320, 16, 16),
            pygame.Rect(350, 270, 16, 16),
            pygame.Rect(750, 320, 16, 16),
        ],
    },
    "castle": {
        "platforms": [
            pygame.Rect(0, 400, SCREEN_WIDTH, 200),  # Ground
            pygame.Rect(200, 200, 200, 200),  # Castle base
            pygame.Rect(250, 100, 100, 100),  # Castle tower
            pygame.Rect(600, 300, 100, 50),   # Platform
        ],
        "enemies": [
            {"rect": pygame.Rect(450, 368, 20, 32), "speed": 2, "direction": -1},
            {"rect": pygame.Rect(650, 268, 20, 32), "speed": 2, "direction": 1},
        ],
        "coins": [
            pygame.Rect(300, 170, 16, 16),
            pygame.Rect(650, 270, 16, 16),
        ],
    },
    "water": {
        "platforms": [
            pygame.Rect(0, 400, SCREEN_WIDTH, 200),  # Ground
            pygame.Rect(200, 350, 100, 20),  # Platform
            pygame.Rect(500, 350, 100, 20),  # Platform
        ],
        "enemies": [
            {"rect": pygame.Rect(300, 368, 20, 32), "speed": 2, "direction": 1},
            {"rect": pygame.Rect(600, 368, 20, 32), "speed": 2, "direction": -1},
        ],
        "coins": [
            pygame.Rect(200, 320, 16, 16),
            pygame.Rect(400, 320, 16, 16),
            pygame.Rect(600, 320, 16, 16),
        ],
    },
}

# Set up the clock for 60 FPS
clock = pygame.time.Clock()

# Font
font = pygame.font.SysFont(None, 36)

def draw_overworld():
    screen.fill(SKY_BLUE)
    
    # Draw paths
    for start, end in paths:
        pygame.draw.line(screen, BROWN, 
                         (start["x"] + 20, start["y"] + 20), 
                         (end["x"] + 20, end["y"] + 20), 5)

    # Draw levels
    for level in levels:
        color = GREEN if level["completed"] else level["color"]
        pygame.draw.rect(screen, color, (level["x"], level["y"], level["width"], level["height"]))
        level_font = pygame.font.SysFont(None, 20)
        text = level_font.render(level["name"], True, WHITE)
        screen.blit(text, (level["x"] - 10, level["y"] + 45))

    # Draw player
    pygame.draw.circle(screen, YELLOW, (int(player_pos[0]), int(player_pos[1])), 15)
    
    # Draw instructions
    instructions = font.render("Click a level to enter, ESC to quit", True, BLACK)
    screen.blit(instructions, (50, 500))

def draw_level(level_index):
    theme = levels[level_index]["theme"]
    level = level_data[theme]
    
    # Draw background
    if theme == "grass":
        screen.fill((100, 200, 100))  # Green background
        for i in range(0, SCREEN_WIDTH, 50):
            pygame.draw.rect(screen, (50, 150, 50), (i, 400, 50, 200))  # Grass
    elif theme == "underground":
        screen.fill(DARK_BROWN)
        for i in range(0, SCREEN_WIDTH, 100):
            pygame.draw.rect(screen, GRAY, (i, 300, 50, 200))  # Rocks
    elif theme == "sky":
        screen.fill(SKY_BLUE)
        pygame.draw.ellipse(screen, WHITE, (100, 100, 100, 50))  # Clouds
        pygame.draw.ellipse(screen, WHITE, (300, 150, 120, 60))
        pygame.draw.ellipse(screen, WHITE, (500, 200, 80, 40))
    elif theme == "castle":
        screen.fill(GRAY)
    elif theme == "water":
        screen.fill(DARK_BLUE)
        for i in range(0, SCREEN_WIDTH, 70):
            pygame.draw.ellipse(screen, (0, 0, 200), (i, 450, 60, 20))  # Waves

    # Draw platforms
    for platform in level["platforms"]:
        pygame.draw.rect(screen, BROWN if theme != "sky" else WHITE, platform)

    # Draw coins
    for coin in level["coins"]:
        pygame.draw.ellipse(screen, YELLOW, coin)

    # Draw enemies
    for enemy in level["enemies"]:
        pygame.draw.rect(screen, RED, enemy["rect"])

    # Draw player
    pygame.draw.rect(screen, YELLOW, player_rect)
    
    # Draw UI
    level_name = font.render(levels[level_index]["name"], True, WHITE)
    screen.blit(level_name, (SCREEN_WIDTH // 2 - level_name.get_width() // 2, 50))
    score_text = font.render(f"Score: {player_score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    lives_text = font.render(f"Lives: {player_lives}", True, WHITE)
    screen.blit(lives_text, (SCREEN_WIDTH - lives_text.get_width() - 10, 10))
    instructions = font.render("Press ESC to return to overworld", True, WHITE)
    screen.blit(instructions, (SCREEN_WIDTH // 2 - instructions.get_width() // 2, 500))

def update_player(dt):
    global player_on_ground, player_pos, player_vel, player_rect, player_lives, game_state

    # Apply gravity
    player_vel[1] += player_gravity * dt

    # Handle input
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_vel[0] -= player_acc * dt
    if keys[pygame.K_RIGHT]:
        player_vel[0] += player_acc * dt
    if keys[pygame.K_SPACE] and player_on_ground:
        player_vel[1] = player_jump_strength
        player_on_ground = False

    # Apply friction
    player_vel[0] += player_vel[0] * player_friction * dt

    # Update position
    player_pos[0] += player_vel[0] * dt
    player_pos[1] += player_vel[1] * dt

    # Keep player in bounds
    player_pos[0] = max(0, min(player_pos[0], SCREEN_WIDTH - player_rect.width))
    if player_pos[1] > SCREEN_HEIGHT:
        player_lives -= 1
        if player_lives <= 0:
            game_state = OVERWORLD
            player_lives = 3
            player_score = 0
        player_pos = [100, 100]
        player_vel = [0, 0]
        player_rect.topleft = player_pos

    player_rect.topleft = (int(player_pos[0]), int(player_pos[1]))

def handle_collisions(level_index):
    global player_on_ground, player_score
    level = level_data[levels[level_index]["theme"]]

    # Platform collisions
    player_on_ground = False
    for platform in level["platforms"]:
        if player_rect.colliderect(platform):
            if player_vel[1] > 0 and player_rect.bottom <= platform.top + 10:
                player_rect.bottom = platform.top
                player_pos[1] = player_rect.top
                player_vel[1] = 0
                player_on_ground = True
            elif player_vel[1] < 0 and player_rect.top >= platform.bottom - 10:
                player_rect.top = platform.bottom
                player_pos[1] = player_rect.top
                player_vel[1] = 0
            elif player_vel[0] > 0 and player_rect.right <= platform.left + 10:
                player_rect.right = platform.left
                player_pos[0] = player_rect.left
                player_vel[0] = 0
            elif player_vel[0] < 0 and player_rect.left >= platform.right - 10:
                player_rect.left = platform.right
                player_pos[0] = player_rect.left
                player_vel[0] = 0

    # Coin collisions
    for coin in level["coins"][:]:
        if player_rect.colliderect(coin):
            level["coins"].remove(coin)
            player_score += 100
            if not level["coins"]:
                levels[level_index]["completed"] = True
                game_state = OVERWORLD
                player_pos = [levels[level_index]["x"] + 20, levels[level_index]["y"] + 20]
                player_vel = [0, 0]
                player_rect.topleft = player_pos

    # Enemy collisions
    for enemy in level["enemies"]:
        if player_rect.colliderect(enemy["rect"]):
            if player_vel[1] > 0 and player_rect.bottom <= enemy["rect"].top + 10:
                level["enemies"].remove(enemy)
                player_score += 200
                player_vel[1] = -8  # Bounce
            else:
                player_lives -= 1
                if player_lives <= 0:
                    game_state = OVERWORLD
                    player_lives = 3
                    player_score = 0
                player_pos = [100, 100]
                player_vel = [0, 0]
                player_rect.topleft = player_pos
                break

def update_enemies(level_index, dt):
    level = level_data[levels[level_index]["theme"]]
    for enemy in level["enemies"]:
        enemy["rect"].x += enemy["speed"] * enemy["direction"] * dt
        if enemy["rect"].left < 0 or enemy["rect"].right > SCREEN_WIDTH:
            enemy["direction"] *= -1
        for platform in level["platforms"]:
            if enemy["rect"].colliderect(platform) and platform != level["platforms"][0]:
                enemy["direction"] *= -1
                break

# Main game loop
running = True
current_level = 0
player_pos = [levels[0]["x"] + 20, levels[0]["y"] + 20]
while running:
    dt = clock.tick(60) / 1000.0  # Delta time in seconds for 60 FPS

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if game_state == OVERWORLD:
                if event.key == pygame.K_RIGHT and current_level < len(levels) - 1:
                    current_level += 1
                    player_pos = [levels[current_level]["x"] + 20, levels[current_level]["y"] + 20]
                elif event.key == pygame.K_LEFT and current_level > 0:
                    current_level -= 1
                    player_pos = [levels[current_level]["x"] + 20, levels[current_level]["y"] + 20]
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif game_state == LEVEL:
                if event.key == pygame.K_ESCAPE:
                    game_state = OVERWORLD
                    player_pos = [levels[current_level]["x"] + 20, levels[current_level]["y"] + 20]
                    player_vel = [0, 0]
                    player_rect.topleft = player_pos
        elif event.type == pygame.MOUSEBUTTONDOWN and game_state == OVERWORLD:
            mouse_pos = pygame.mouse.get_pos()
            for i, level in enumerate(levels):
                if level["rect"].collidepoint(mouse_pos):
                    game_state = LEVEL
                    current_level = i
                    current_level_index = i
                    player_pos = [100, 100]
                    player_vel = [0, 0]
                    player_rect.topleft = player_pos

    # Update
    if game_state == LEVEL:
        update_player(dt)
        handle_collisions(current_level_index)
        update_enemies(current_level_index, dt)

    # Draw
    if game_state == OVERWORLD:
        draw_overworld()
    elif game_state == LEVEL:
        draw_level(current_level_index)

    pygame.display.flip()

# Clean up
pygame.quit()
sys.exit()
