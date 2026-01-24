import pygame
import sys
from config import DEBUG
from scripts.game_config import *

class Game:
    def __init__(self, all_team_troops, all_team_names):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("Mini Militia Bot Arena")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.fps = FPS

        self.all_team_troops = all_team_troops
        self.all_team_names = all_team_names

        self.game_counter = 0
        self.winner = None

        if DEBUG:
            for i, name in enumerate(self.all_team_names):
                print(f"[Game] Loaded Team {i+1}: {name}")

        # TODO: initialize players, weapons, map, physics, etc.
        self._init_players()

    def _init_players(self):
        self.players = []

        for team_idx, troops in enumerate(self.all_team_troops):
            for troop_idx, troop in enumerate(troops):
                # Distribute players across the map
                x_pos = 100 + (team_idx * 200) + (troop_idx * 50)
                y_pos = SCREEN_HEIGHT // 2
                
                # Placeholder player objects
                self.players.append({
                    "team": team_idx,
                    "troop": troop,
                    "x": x_pos,
                    "y": y_pos,
                    "width": PLAYER_WIDTH,
                    "height": PLAYER_HEIGHT,
                    "vx": 0,
                    "vy": 0
                })

        if DEBUG:
            print(f"[Game] Initialized {len(self.players)} players")

    def update(self):
        # TODO: physics, AI calls, combat resolution
        pass

    def draw(self):
        self.screen.fill((25, 25, 25))

        # Render players using team colors
        for p in self.players:
            color = TEAM_COLORS[p["team"]]
            pygame.draw.circle(self.screen, color, (int(p["x"]), int(p["y"])), PLAYER_WIDTH // 2)

        pygame.display.update()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.update()
            self.draw()

            self.clock.tick(self.fps)
            self.game_counter += 1
