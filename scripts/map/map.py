# map.py
import pygame
import random
from config import *
from game_config import *

class GameMap:
    def __init__(self, grid_data):
        """
        grid_data: A 2D list (list of lists) where:
        0 = Air, 1 = Wall, 2 = Spawn Candidate
        """
        self.grid = grid_data
        self.width = len(grid_data[0])
        self.height = len(grid_data)
        
        # Pre-calculate spawn points so we don't search every frame
        self.spawn_candidates = []
        self._parse_map_features()

    def _parse_map_features(self):
        """Scans grid once to find spawns or special zones"""
        for y, row in enumerate(self.grid):
            for x, tile_id in enumerate(row):
                if tile_id == 2:  # Spawn Point Marker
                    # Store center of tile for spawning
                    center_x = (x * TILE_SIZE) + (TILE_SIZE // 2)
                    center_y = (y * TILE_SIZE) + (TILE_SIZE // 2)
                    self.spawn_candidates.append((center_x, center_y))

    def allocate_spawns(self, num_players=2):
        """
        Returns a list of (x, y) tuples for player starts.
        Ensures randomness but prevents spawning on top of each other.
        """
        if len(self.spawn_candidates) < num_players:
            raise ValueError("Not enough spawn points on map!")
        
        # Simple random selection (Logic can be improved for distance checks)
        return random.sample(self.spawn_candidates, num_players)

    def get_tile_rects(self, area_rect):
        """
        Optimized collision: Only returns Wall Rects close to the player.
        area_rect: The player's bounding box.
        """
        hit_walls = []
        
        # Convert pixel coordinates to grid coordinates
        start_col = max(0, int(area_rect.left // TILE_SIZE))
        end_col = min(self.width, int(area_rect.right // TILE_SIZE) + 1)
        start_row = max(0, int(area_rect.top // TILE_SIZE))
        end_row = min(self.height, int(area_rect.bottom // TILE_SIZE) + 1)

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                if self.grid[y][x] == 1: # If Wall
                    wall_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    hit_walls.append(wall_rect)
                    
        return hit_walls