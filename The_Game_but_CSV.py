import pygame
import csv
from datetime import datetime
from os import listdir
from os.path import isfile, join
from sys import exit
pygame.init()

pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 1080, 600
FPS = 60
PLAYER_VEL = 5
SCORE = 0
ADD = True
global selected_character

window = pygame.display.set_mode((WIDTH, HEIGHT))

def font(size):
    return pygame.font.Font(join('assets','Pixeltype.ttf'),size)


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect1 = pygame.Rect(96, 64, size, size)
    rect2 = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect1)
    surface.blit(image, (0, 96), rect2)
    return pygame.transform.scale2x(surface)


def get_score(record):
    return record[1]

def display_score_table(window, scores):
    # Sort scores in descending order based on the score value and take the top 5
    top_scores = sorted(scores, key=get_score, reverse=True)[:5]
    
    # Title for the top scores
    title_surf = font(45).render("Top 5 Scores", True, (0, 0, 0))
    window.blit(title_surf, title_surf.get_rect(center=(540, 100)))
    
    y_pos = 150
    # Display the top 5 scores
    for _, record in enumerate(top_scores):
        score_text = f"Run {record[0]}: {record[1]} points"  # Add time format if desired
        score_surf = font(40).render(score_text, True, (0, 0, 0))
        window.blit(score_surf, score_surf.get_rect(center=(540, y_pos)))
        y_pos += 50

    pygame.display.update()


run = 0
class CSVHandler:
    def __init__(self, filename="scores.csv"):
        self.filename = filename
        # Create file with headers if it doesn't exist
        try:
            with open(self.filename, "x", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Run","Score", "Date"])  # Headers
        except FileExistsError:
            pass

    def get_top_scores(self, limit=5):
        with open(self.filename, "r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            scores = [(int(row[0]), row[1]) for row in reader]
            scores.sort(reverse=True, key=lambda x: x[0])  # Sort by Score, descending
            return scores[:limit]  # Return top `limit` scores

    def add(self, score):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.filename,"+a", newline="") as file:
            writer = csv.writer(file)
            global run
            run += 1
            writer.writerow([run, score, timestamp])  # Append new score with timestamp


class Player(pygame.sprite.Sprite):
    GRAVITY = 1
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height, character="PinkMan"):
        super().__init__()
        self.character = character
        self.SPRITES = load_sprite_sheets("MainCharacters", character, 32, 32, True)
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "right"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.health = 10


    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 1.3:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite) # Used to find the non transparent pixels. Enables pixel perfect collisions

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Button():
    def __init__(self, x, y, image, scale):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.click = False
    
    def draw(self):
        action = False
        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.click == False:
                self.click = True
                action = True 

        if pygame.mouse.get_pressed()[0] == 0:
            self.click = False

        window.blit(self.image, (self.rect.x, self.rect.y))
        return action


class Apple(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, 'apple')
        self.apple = load_sprite_sheets("Items", "Fruits", width, height)
        self.image = self.apple["Apple"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.hit = False
    
    def loop(self):
        if self.hit:
            self.rect.y = -100
            self.hit = False


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block1 = get_block(size)
        self.image.blit(block1, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class Spike(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "spike")
        self.spike = load_sprite_sheets("Traps","Spikes", width, height)
        self.image = pygame.transform.scale_by(self.spike["Idle"][0],1.5)
        self.mask = pygame.mask.from_surface(self.image)


class Trophy(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, 'trophy')
        self.trophy = load_sprite_sheets('Items','Checkpoints', width, height)
        self.image = self.trophy["End (Idle)"][0]
        self.mask = pygame.mask.from_surface(self.image)


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)
    
    Health_surf = font(40).render(f"Health : {int(player.health)}", False, (50, 50, 50))
    Health_rect = Health_surf.get_rect(center = (1000, 40))
    global Time
    Time = (pygame.time.get_ticks() - Start_Time)/1000
    Time_surf = font(40).render(f"Time: {int(Time)}", False, (50, 50, 50))
    Time_rect = Time_surf.get_rect(center = (60, 40))
    Score_surf = font(40).render(f"Score : {SCORE}", False, (50, 50, 50))
    Score_rect = Score_surf.get_rect(center = (540, 40))
    window.blit(Health_surf, Health_rect)
    window.blit(Score_surf, Score_rect)
    window.blit(Time_surf, Time_rect)
    player.draw(window, offset_x)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    global ADD, SCORE, Starting_ticks

    for obj in to_check:
        global SCORE
        if obj:
            if obj.name == "fire":
                player.make_hit()
                player.health -= 0.07
            elif obj.name == 'spike':
                player.make_hit()
                player.health -= 0.5
            elif obj.name == 'trophy':
                if player.health == 10:
                    SCORE += 20
                elif player.health < 10 and player.health > 5:
                    SCORE += 15
                elif player.health < 5 and player.health > 0:
                    SCORE += 10
                global Time
                if Time >= 0 and Time <= 30:
                    SCORE -= 0
                elif Time > 30 and Time <= 36:
                    SCORE -= 4
                elif Time > 36 and Time <= 42:
                    SCORE -= 8
                elif Time > 45:
                    SCORE -= 10
                not_main()
            elif obj.name == 'apple' and ADD:
                obj.hit = True
                SCORE += 5
                ADD = False

    Current_ticks = (pygame.time.get_ticks() - Starting_ticks) / 1000
    if Current_ticks > 2:
        Current_ticks = 0
        Starting_ticks = pygame.time.get_ticks()
        ADD = True


def Home(window):
    global selected_character
    Home_path = join('assets', 'MainCharacters')
    Char_Names = [name for name in listdir(Home_path)]

    count = 0
    Char_Lst = []
    for idx, char_name in enumerate(Char_Names):
        char_image = pygame.image.load(join('assets', 'MainCharacters', char_name, 'jump.png')).convert_alpha()
        if count > 1:
            char_image = pygame.transform.flip(char_image, True, False)
        x_pos = 100 + idx * 245
        char_button = Button(x_pos, 270, char_image, 4)
        Char_Lst.append((char_button, char_name))
        count += 1
    selected_character = None

    while True:
        background, bg_image = get_background("Green.png")
        for tile in background:
            window.blit(bg_image, tile)

        Home_surf = font(70).render("Platformer", False, (0, 0, 0))
        Home_rect = Home_surf.get_rect(center=(540, 130))
        window.blit(Home_surf, Home_rect)

        Play = pygame.image.load(join('assets', 'Menu', 'Buttons', 'Play.png')).convert_alpha()
        Play_btn = Button(500, 290, Play, 3)
        if Play_btn.draw() and selected_character:
            main(window, selected_character)  # Pass selected character to main

        for char_button, char_name in Char_Lst:
            if char_button.draw():
                selected_character = char_name  # Update selected character

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        pygame.display.update()


def main(window, character):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    block_size = 96
    global Starting_ticks, Start_Time
    Starting_ticks = pygame.time.get_ticks()
    Start_Time = pygame.time.get_ticks()

    player = Player(block_size, HEIGHT - block_size, 50, 50, character)  # Use selected character
    fires = [Fire(224, HEIGHT - block_size - 64, 16, 32),
             Fire(15 * block_size + 64, HEIGHT - block_size - 64, 16, 32),
             Fire(21 * block_size + 64, HEIGHT - block_size - 64, 16, 32)]
    for fire in fires:
        fire.on()


    floor1 = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-1 , (WIDTH - 200) // block_size)]
    floor2 = [Block(i * block_size, HEIGHT - block_size, block_size)
               for i in range(15, (int(WIDTH * 2.5)) // block_size)] 
    wall = [Block(-96, i, block_size)
             for i in range(HEIGHT, -100, -96)]
    block_pair = [Block(17 * block_size, HEIGHT - i * block_size, block_size) for i in range(2,4)]
    apples = [Apple(0, HEIGHT - block_size * 5 - 48, 24, 24),
              Apple(9 * block_size, HEIGHT - 6 * block_size - 48, 24, 24),
              Apple(17 * block_size, HEIGHT - block_size * 5 - 48, 24, 24),
              Apple(26 * block_size, HEIGHT - block_size - 48, 24, 24)]
    bridge1 = [Block(i * block_size, HEIGHT - 6 * block_size, block_size)
               for i in range(8,WIDTH // block_size)]
    spike_strips = [Spike(i * block_size, HEIGHT - block_size - 48, 16, 16) for i in range(18, 21)] + \
                   [Spike(i * block_size + 48, HEIGHT - block_size - 48, 16, 16) for i in range(18, 20)]
    stairs = [Block((29 + i) * block_size, HEIGHT - i * block_size, block_size) for i in range(0, 3)] + \
             [Block((21 + i) * block_size, HEIGHT - i * block_size, block_size) for i in range(3, 6)]
    bridge2 = [Block((26 + i) * block_size, HEIGHT - 5 * block_size, block_size)
               for i in range(1, 5)]
    floor3 = [Block((35 + i) * block_size, HEIGHT - 2 * block_size, block_size)
              for i in range(0,4)]
    trophy = Trophy(38 * block_size - 10, HEIGHT - 3 * block_size - 32, 56, 64)

    objects = [Block(0, HEIGHT - block_size * 5, block_size),*floor1,
                Block(2 * block_size, HEIGHT - (block_size * 4 - 16), block_size),
                 Block(6 * block_size, HEIGHT - block_size * 2, block_size), *floor2, *wall, *fires,
                  Block(6 * block_size, HEIGHT - 5 * block_size, block_size),
                   Spike(6 * block_size + 48, HEIGHT - 5 * block_size - 48, 16, 16),
               Spike(17 * block_size + 24, HEIGHT - block_size * 3 - 48, 16, 16), *block_pair,
                 Block(17 * block_size, HEIGHT - block_size * 5, block_size), *apples,
                  *bridge1, Block(12 * block_size, HEIGHT - 3 * block_size, block_size), *spike_strips,
                    *stairs, *bridge2, *floor3, Block(24 * block_size, HEIGHT - 2 * block_size, block_size),
                    trophy]
    
    offset_x = 0
    scroll_area_width = 500

    run = True
    while run:
        clock.tick(FPS)

        if player.rect.top > HEIGHT:
            player.rect.y = -100
            player.make_hit()
            player.health -= 5

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        
        for fire in fires:
            fire.loop()
        for apple in apples:
            apple.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel
        
        if int(player.health) <= 0:
            global SCORE
            SCORE = 0
            not_main()


def not_main():
    Play = pygame.image.load(join('assets','Menu','Buttons','Play.png')).convert_alpha()
    Restart = pygame.image.load(join('assets','Menu','Buttons','Restart.png')).convert_alpha()
    Close = pygame.image.load(join('assets','Menu','Buttons','Close.png')).convert_alpha()
    
    Play_btn = Button(400, 450, Play, 3)# old y = 350
    Restart_btn = Button(600, 450, Restart, 3)
    Close_btn = Button(1035,0, Close, 3)

    global SCORE
    CSVHandler().add(SCORE)

    scores = CSVHandler().get_top_scores()

    Play_Surf = font(50).render("PLAY",False,(0, 0, 0))
    Restart_Surf = font(50).render("RESTART",False,(0,0,0))

    while True:
        background, bg_image = get_background("Gray.png")
        for tile in background:
            window.blit(bg_image, tile)
        
        Play_Rect = Play_Surf.get_rect(center = (435,535))
        Restart_Rect = Restart_Surf.get_rect(center = (640, 535))
        
        if SCORE == 0:
            End_Surf = font(60).render("Game Over", False, (0, 0, 0))
            End_Rect = End_Surf.get_rect(center = (540,50))
        else:
            End_Surf = font(60).render("You Won!!", False, (0, 0, 0))
            End_Rect = End_Surf.get_rect(center = (540,50))

        score_surf = font(40).render(f"Score: {SCORE}", False, (50, 50, 50))
        score_rect = score_surf.get_rect(center = (80,40))

        window.blit(Play_Surf, Play_Rect)
        window.blit(Restart_Surf, Restart_Rect)
        window.blit(End_Surf, End_Rect)
        window.blit(score_surf, score_rect)
        
        if Restart_btn.draw():
            SCORE = 0
            global selected_character
            main(window, character = selected_character)

        if Play_btn.draw():
            SCORE = 0
            Home(window)

        if Close_btn.draw():
            pygame.quit()
            exit()
        
        if pygame.event.get() == pygame.QUIT:
            pygame.quit()
            exit()

        display_score_table(window, scores)

        pygame.display.update()


if __name__ == "__main__":
    Home(window)