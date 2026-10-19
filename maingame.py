import math
import os
import random

# These settings let the template start in a headless Codespaces container too.
if not os.environ.get("DISPLAY"):
	os.environ["DISPLAY"] = ":99"

if not os.environ.get("XDG_RUNTIME_DIR"):
	os.environ["XDG_RUNTIME_DIR"] = "/tmp/runtime-vscode"
	os.makedirs("/tmp/runtime-vscode", exist_ok=True)

os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame


# Window setup
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 450
WINDOW_TITLE = "Shooter"

# Starter colours
BACKGROUND = (25, 25, 25)
TEXT_COLOUR = (235, 235, 235)
PLAYER_COLOUR = (52, 82, 170)
ENEMY_COLOUR = (210, 75, 75)
BULLET_COLOUR = (247, 195, 78)
RED = (210, 75, 75)
GREEN = (55, 120, 70)
WHITE = (255, 255, 255)

# Pygame initialization
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(WINDOW_TITLE)
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)
small_font = pygame.font.Font(None, 20)
label_font = pygame.font.Font(None, 22)

player = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
bullets = []
enemy_bullets = []
enemies = []
bosses = []
ammo = 12
max_ammo = 12
kills = 0
wave = 1
enemies_spawned = 0
wave_enemy_count = 0
spawn_timer = 0
next_wave_timer = 0
boss_spawned = False
game_over = False
game_started = False
selected_class = 0
player_health = 4
player_max_health = 4
invulnerability_timer = 0
ability_timer = 0
ability_cooldown = 0
ability_flash = 0
reload_timer = 0
reload_duration = 0
fire_timer = 0
big_font = pygame.font.Font(None, 64)
boss_font = pygame.font.Font(None, 20)

CLASS_KITS = [
	{
		"name": "Vanguard", "kit": "Assault Rifle", "health": 4, "speed": 225,
		"ammo": 16, "reload": 1.0, "fire_delay": 0.20, "ability": "Dash",
		"cooldown": 3.5, "weapon": "rifle",
	},
	{
		"name": "Medic", "kit": "Field Kit", "health": 5, "speed": 210,
		"ammo": 12, "reload": 0.9, "fire_delay": 0.32, "ability": "Medkit",
		"cooldown": 8.0, "weapon": "burst",
	},
	{
		"name": "Breacher", "kit": "Scattergun", "health": 7, "speed": 170,
		"ammo": 8, "reload": 1.25, "fire_delay": 0.65, "ability": "Blast",
		"cooldown": 7.0, "weapon": "shotgun",
	},
]

BOSS_TYPES = {
	"Normal": {"health": 8, "speed": 42, "radius": 25, "colour": (170, 70, 190), "behavior": "stalker"},
	"Speedy": {"health": 6, "speed": 80, "radius": 19, "colour": (235, 125, 40), "behavior": "charger"},
	"Tank": {"health": 16, "speed": 25, "radius": 32, "colour": (35, 95, 55), "behavior": "shooter"},
	"Warper": {"health": 8, "speed": 38, "radius": 24, "colour": (130, 80, 45), "behavior": "warper"},
	"Big": {"health": 20, "speed": 31, "radius": 43, "colour": (35, 55, 125), "behavior": "summoner"},
}


def spawn_enemy():
	"""Put an enemy just outside one random edge of the screen."""
	edge = random.choice(("top", "bottom", "left", "right"))
	if edge == "top":
		return pygame.Vector2(random.randint(0, SCREEN_WIDTH), -20)
	if edge == "bottom":
		return pygame.Vector2(random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 20)
	if edge == "left":
		return pygame.Vector2(-20, random.randint(0, SCREEN_HEIGHT))
	return pygame.Vector2(SCREEN_WIDTH + 20, random.randint(0, SCREEN_HEIGHT))


def spawn_boss():
	name = random.choice(list(BOSS_TYPES))
	stats = BOSS_TYPES[name]
	return {
		"name": name,
		"position": spawn_enemy(),
		"health": stats["health"],
		"max_health": stats["health"],
		"speed": stats["speed"],
		"radius": stats["radius"],
		"colour": stats["colour"],
		"behavior": stats["behavior"],
		"attack_timer": 2.0,
		"dash_timer": 0,
		"dash_direction": pygame.Vector2(),
	}


def start_wave(number):
	return number, 0, 3 + number * 2


def apply_class(class_index):
	global selected_class, ammo, max_ammo, player_health, player_max_health
	global ability_timer, ability_cooldown, reload_timer, reload_duration
	selected_class = class_index
	loadout = CLASS_KITS[selected_class]
	max_ammo = loadout["ammo"]
	ammo = max_ammo
	player_max_health = loadout["health"]
	player_health = player_max_health
	ability_timer = 0
	ability_cooldown = loadout["cooldown"]
	reload_timer = 0
	reload_duration = loadout["reload"]


def reset_game():
	global player, bullets, enemy_bullets, enemies, bosses, kills, wave
	global enemies_spawned, wave_enemy_count, spawn_timer, next_wave_timer
	global boss_spawned, game_over, game_started, invulnerability_timer
	global ability_timer, ability_flash, ability_cooldown, fire_timer
	player = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
	bullets.clear()
	enemy_bullets.clear()
	enemies.clear()
	bosses.clear()
	kills = 0
	wave = 1
	enemies_spawned = 0
	wave_enemy_count = 0
	spawn_timer = 0
	next_wave_timer = 0
	boss_spawned = False
	game_over = False
	game_started = False
	invulnerability_timer = 0
	ability_timer = 0
	ability_flash = 0
	fire_timer = 0
	apply_class(selected_class)
	wave, enemies_spawned, wave_enemy_count = start_wave(wave)


def draw_bar(x, y, width, height, value, maximum, colour):
	pygame.draw.rect(screen, (54, 61, 70), (x, y, width, height), border_radius=4)
	fill_width = width * max(0, value) / max(1, maximum)
	if fill_width > 0:
		pygame.draw.rect(screen, colour, (x, y, fill_width, height), border_radius=4)


def damage_player():
	global player_health, invulnerability_timer, game_over
	if invulnerability_timer <= 0:
		player_health -= 1
		invulnerability_timer = 0.9
		if player_health <= 0:
			game_over = True


wave, enemies_spawned, wave_enemy_count = start_wave(wave)
apply_class(selected_class)


running = True
while running:
	delta_time = clock.tick(60) / 1000
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
		elif event.type == pygame.KEYDOWN and event.key in (pygame.K_1, pygame.K_2, pygame.K_3) and not game_started and not game_over:
			apply_class(event.key - pygame.K_1)
		elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and not game_started and not game_over:
			game_started = True
		elif event.type == pygame.KEYDOWN and event.key == pygame.K_f and game_over:
			reset_game()
		elif event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_started and not game_over:
			if ammo < max_ammo and reload_timer <= 0:
				reload_timer = reload_duration
		elif event.type == pygame.KEYDOWN and event.key == pygame.K_q and game_started and not game_over and ability_timer <= 0:
			loadout = CLASS_KITS[selected_class]
			if loadout["ability"] == "Dash":
				direction = pygame.Vector2(pygame.mouse.get_pos()) - player
				if direction.length_squared() > 0:
					player += direction.normalize() * 115
					player.x = max(18, min(SCREEN_WIDTH - 18, player.x))
					player.y = max(18, min(SCREEN_HEIGHT - 18, player.y))
					invulnerability_timer = max(invulnerability_timer, 0.35)
			elif loadout["ability"] == "Medkit":
				player_health = min(player_max_health, player_health + 2)
			else:
				for enemy in enemies[:]:
					if enemy.distance_to(player) < 125:
						enemies.remove(enemy)
						kills += 1
				for boss in bosses[:]:
					if boss["position"].distance_to(player) < 135:
						boss["health"] -= 3
						if boss["health"] <= 0:
							bosses.remove(boss)
							kills += 1
			ability_timer = ability_cooldown
			ability_flash = 0.28
		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_started and ammo > 0 and reload_timer <= 0 and not game_over and fire_timer <= 0:
			mouse = pygame.Vector2(event.pos)
			direction = mouse - player
			if direction.length_squared() > 0:
				direction = direction.normalize()
				loadout = CLASS_KITS[selected_class]
				spread = (0,) if loadout["weapon"] == "rifle" else ((-0.12, 0, 0.12) if loadout["weapon"] == "burst" else (-0.42, -0.21, 0, 0.21, 0.42))
				for offset in spread:
					shot_direction = direction.rotate_rad(offset)
					bullets.append({"position": player.copy(), "velocity": shot_direction * 450, "damage": 1})
				ammo -= 1
				fire_timer = loadout["fire_delay"]

	if game_started and not game_over:
		keys = pygame.key.get_pressed()
		movement = pygame.Vector2(
			keys[pygame.K_d] - keys[pygame.K_a],
			keys[pygame.K_s] - keys[pygame.K_w],
		)
		if movement.length_squared() > 0:
			player += movement.normalize() * CLASS_KITS[selected_class]["speed"] * delta_time
		player.x = max(15, min(SCREEN_WIDTH - 15, player.x))
		player.y = max(15, min(SCREEN_HEIGHT - 15, player.y))
		invulnerability_timer = max(0, invulnerability_timer - delta_time)
		ability_timer = max(0, ability_timer - delta_time)
		ability_flash = max(0, ability_flash - delta_time)
		fire_timer = max(0, fire_timer - delta_time)
		if reload_timer > 0:
			reload_timer = max(0, reload_timer - delta_time)
			if reload_timer == 0:
				ammo = max_ammo

		spawn_timer += delta_time
		spawn_delay = max(0.42, 1.15 - wave * 0.06)
		if enemies_spawned < wave_enemy_count and spawn_timer > spawn_delay:
			enemies.append(spawn_enemy())
			enemies_spawned += 1
			spawn_timer = 0

		if (wave % 5 == 0 and enemies_spawned == wave_enemy_count
				and not enemies and not bosses and not boss_spawned):
			bosses.append(spawn_boss())
			boss_spawned = True

		for bullet in bullets[:]:
			bullet["position"] += bullet["velocity"] * delta_time
			if not screen.get_rect().inflate(60, 60).collidepoint(bullet["position"]):
				bullets.remove(bullet)
		for bullet in enemy_bullets[:]:
			bullet["position"] += bullet["velocity"] * delta_time
			if bullet["position"].distance_to(player) < 19:
				damage_player()
				enemy_bullets.remove(bullet)
			elif not screen.get_rect().inflate(30, 30).collidepoint(bullet["position"]):
				enemy_bullets.remove(bullet)

		for enemy in enemies[:]:
			direction = player - enemy
			if direction.length_squared() > 0:
				enemy += direction.normalize() * 75 * delta_time
			if enemy.distance_to(player) < 24:
				damage_player()
			for bullet in bullets[:]:
				if enemy.distance_to(bullet["position"]) < 17:
					enemies.remove(enemy)
					bullets.remove(bullet)
					kills += 1
					break

		for boss in bosses[:]:
			boss_position = boss["position"]
			direction = player - boss_position
			boss["attack_timer"] -= delta_time
			boss["dash_timer"] = max(0, boss["dash_timer"] - delta_time)
			if boss["behavior"] == "charger" and boss["attack_timer"] <= 0:
				boss["dash_direction"] = direction.normalize() if direction.length_squared() > 0 else pygame.Vector2(1, 0)
				boss["dash_timer"] = 0.65
				boss["attack_timer"] = 3.1
			if boss["behavior"] == "charger" and boss["dash_timer"] > 0:
				boss_position += boss["dash_direction"] * 255 * delta_time
			elif direction.length_squared() > 0:
				boss_position += direction.normalize() * boss["speed"] * (1 + wave * 0.03) * delta_time
			if boss["behavior"] == "warper" and boss["attack_timer"] <= 0:
				boss_position = player + pygame.Vector2(random.randint(-150, 150), random.randint(-150, 150))
				boss_position.x = max(35, min(SCREEN_WIDTH - 35, boss_position.x))
				boss_position.y = max(35, min(SCREEN_HEIGHT - 35, boss_position.y))
				boss["position"] = boss_position
				boss["attack_timer"] = 5.0
			elif boss["behavior"] == "shooter" and boss["attack_timer"] <= 0:
				shot_direction = direction.normalize() if direction.length_squared() > 0 else pygame.Vector2(1, 0)
				enemy_bullets.append({"position": boss_position.copy(), "velocity": shot_direction * 190})
				boss["attack_timer"] = 1.35
			elif boss["behavior"] == "summoner" and boss["attack_timer"] <= 0:
				enemies.append(spawn_enemy())
				boss["attack_timer"] = 4.2
			if boss_position.distance_to(player) < boss["radius"] + 16:
				damage_player()
			for bullet in bullets[:]:
				if boss_position.distance_to(bullet["position"]) < boss["radius"]:
					boss["health"] -= bullet["damage"]
					bullets.remove(bullet)
					if boss["health"] <= 0:
						bosses.remove(boss)
						kills += 1
					break

		if (enemies_spawned == wave_enemy_count and not enemies and not bosses):
			next_wave_timer += delta_time
			if next_wave_timer >= 2:
				wave += 1
				enemies_spawned = 0
				wave_enemy_count = 3 + wave * 2
				next_wave_timer = 0
				boss_spawned = False

	screen.fill((17, 22, 29))
	pygame.draw.rect(screen, (23, 30, 39), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
	for bullet in bullets:
		pygame.draw.circle(screen, BULLET_COLOUR, bullet["position"], 4)
	for bullet in enemy_bullets:
		pygame.draw.circle(screen, (255, 95, 105), bullet["position"], 6)
	for enemy in enemies:
		pygame.draw.circle(screen, ENEMY_COLOUR, enemy, 14)
		pygame.draw.circle(screen, BACKGROUND, enemy, 5)
	for boss in bosses:
		boss_position = boss["position"]
		pygame.draw.circle(screen, boss["colour"], boss_position, boss["radius"])
		pygame.draw.circle(screen, BACKGROUND, boss_position, max(5, boss["radius"] // 3))
		if boss["behavior"] == "charger":
			pygame.draw.circle(screen, (255, 215, 130), boss_position, boss["radius"] - 4, 2)
			if boss["dash_timer"] > 0:
				pygame.draw.line(screen, (255, 220, 150), boss_position, boss_position + boss["dash_direction"] * 48, 3)
		elif boss["behavior"] == "shooter":
			pygame.draw.line(screen, (255, 115, 115), boss_position, player, 1 if boss["attack_timer"] > 0.35 else 3)
		elif boss["behavior"] == "warper":
			pygame.draw.circle(screen, (220, 170, 255), boss_position, boss["radius"] - 3, 2)
		elif boss["behavior"] == "summoner":
			pygame.draw.circle(screen, (135, 190, 255), boss_position, boss["radius"] - 4, 2)
		health_width = 64 * boss["health"] / boss["max_health"]
		pygame.draw.rect(screen, (70, 25, 25), (boss_position.x - 32, boss_position.y - boss["radius"] - 14, 64, 6))
		pygame.draw.rect(screen, (70, 210, 100), (boss_position.x - 32, boss_position.y - boss["radius"] - 14, health_width, 6))
		nametag = boss_font.render(boss["name"], True, WHITE)
		screen.blit(nametag, nametag.get_rect(center=(boss_position.x, boss_position.y - boss["radius"] - 24)))

	if game_started:
		loadout = CLASS_KITS[selected_class]
		if ability_flash > 0:
			pygame.draw.circle(screen, (245, 215, 120), player, 52, 3)
		if invulnerability_timer <= 0 or int(invulnerability_timer * 12) % 2 == 0:
			pygame.draw.circle(screen, PLAYER_COLOUR, player, 16)
			mouse = pygame.Vector2(pygame.mouse.get_pos())
			angle = math.atan2(mouse.y - player.y, mouse.x - player.x)
			barrel = player + pygame.Vector2(math.cos(angle), math.sin(angle)) * 25
			pygame.draw.line(screen, (195, 210, 230), player, barrel, 7)

		pygame.draw.rect(screen, (17, 22, 29), (0, 0, SCREEN_WIDTH, 66))
		pygame.draw.line(screen, (58, 69, 81), (0, 65), (SCREEN_WIDTH, 65), 1)
		pygame.draw.rect(screen, (37, 45, 54), (18, 13, 34, 34), border_radius=6)
		heart = small_font.render("HP", True, (255, 130, 135))
		screen.blit(heart, (25, 21))
		draw_bar(62, 14, 112, 10, player_health, player_max_health, (235, 95, 100))
		health_label = small_font.render(f"{player_health}/{player_max_health}", True, TEXT_COLOUR)
		screen.blit(health_label, (62, 29))
		wave_label = label_font.render(f"WAVE {wave:02}", True, WHITE)
		screen.blit(wave_label, (205, 20))
		kills_label = small_font.render(f"{kills} ELIMINATED", True, (170, 185, 198))
		screen.blit(kills_label, (302, 23))
		class_label = small_font.render(f"{loadout['name'].upper()}  /  {loadout['kit']}", True, (177, 205, 228))
		screen.blit(class_label, class_label.get_rect(right=SCREEN_WIDTH - 18, centery=24))

		pygame.draw.rect(screen, (17, 22, 29), (0, SCREEN_HEIGHT - 54, SCREEN_WIDTH, 54))
		pygame.draw.line(screen, (58, 69, 81), (0, SCREEN_HEIGHT - 54), (SCREEN_WIDTH, SCREEN_HEIGHT - 54), 1)
		ammo_label = label_font.render(f"AMMO  {ammo:02}/{max_ammo:02}", True, WHITE)
		screen.blit(ammo_label, (18, SCREEN_HEIGHT - 39))
		for index in range(max_ammo):
			cell_x = 145 + index * 10
			pygame.draw.rect(screen, BULLET_COLOUR if index < ammo else (65, 69, 72), (cell_x, SCREEN_HEIGHT - 34, 6, 16), border_radius=2)
		if reload_timer > 0:
			draw_bar(145, SCREEN_HEIGHT - 15, 100, 4, reload_duration - reload_timer, reload_duration, (220, 190, 100))
		ability_text = f"Q  {loadout['ability']}"
		if ability_timer > 0:
			ability_text += f"  {ability_timer:.1f}s"
		ability_label = small_font.render(ability_text, True, (190, 215, 235) if ability_timer <= 0 else (130, 145, 155))
		screen.blit(ability_label, (SCREEN_WIDTH - 170, SCREEN_HEIGHT - 36))
		controls = small_font.render("WASD move   LMB fire   R reload", True, (145, 157, 168))
		screen.blit(controls, controls.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20)))

	if not game_started and not game_over:
		overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
		overlay.fill((9, 13, 18, 232))
		screen.blit(overlay, (0, 0))
		title = big_font.render("shooter game", True, WHITE)
		screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 62)))
		subtitle = small_font.render("choose a class", True, (161, 179, 194))
		screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH / 2, 100)))
		card_width = 205
		for index, loadout in enumerate(CLASS_KITS):
			card = pygame.Rect(22 + index * 220, 132, card_width, 205)
			selected = index == selected_class
			pygame.draw.rect(screen, (34, 45, 56) if selected else (24, 31, 39), card, border_radius=8)
			pygame.draw.rect(screen, (100, 190, 225) if selected else (58, 69, 81), card, 2, border_radius=8)
			number = small_font.render(f"0{index + 1}", True, (111, 197, 226))
			name = label_font.render(loadout["name"], True, WHITE)
			kit = small_font.render(loadout["kit"], True, (173, 190, 205))
			ability = small_font.render(f"Q  {loadout['ability']}", True, (239, 201, 110))
			stats = small_font.render(f"HEALTH  {loadout['health']}     SPEED  {loadout['speed']}", True, (173, 190, 205))
			screen.blit(number, (card.x + 14, card.y + 13))
			screen.blit(name, (card.x + 14, card.y + 48))
			screen.blit(kit, (card.x + 14, card.y + 77))
			screen.blit(ability, (card.x + 14, card.y + 124))
			screen.blit(stats, (card.x + 14, card.y + 158))
		start_text = font.render("1-3 select     ENTER deploy", True, (245, 203, 111))
		screen.blit(start_text, start_text.get_rect(center=(SCREEN_WIDTH / 2, 380)))

	if game_over:
		overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
		overlay.fill((0, 0, 0, 175))
		screen.blit(overlay, (0, 0))
		game_over_text = big_font.render("GAME OVER", True, (255, 255, 255))
		stats_text = font.render(f"Wave {wave}    Kills {kills}", True, WHITE)
		restart_text = font.render("Press F to restart", True, BULLET_COLOUR)
		screen.blit(game_over_text, game_over_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 25)))
		screen.blit(stats_text, stats_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 22)))
		screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 58)))
	pygame.display.flip()

pygame.quit()
