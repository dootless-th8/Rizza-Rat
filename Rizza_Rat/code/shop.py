from settings import *
import pygame
from os.path import join

class GunData:
    """Data structure for all available guns."""
    
    GUNS = {
        'glock': {
            'name': 'Glock 19',
            'price': 500,
            'damage': 10,
            'fire_rate': 4,  # bullets per second
            'magazine': 17,
            'reload_time': 1500,
            'sfx':join('audio', 'guns', 'glock.mp3'),
            'description': 'Reliable handgun'
        },
        'revolver': {
            'name': 'Colt 45',
            'price': 800,
            'damage': 25,
            'fire_rate': 3,
            'magazine': 6,
            'reload_time': 2000,
            'sfx':join('audio', 'guns', 'revolver.mp3'),
            'description': 'Powerful revolver'
        },
        'mp5': {
            'name': 'MP5A3',
            'price': 1500,
            'damage': 10,
            'fire_rate': 7,
            'magazine': 30,
            'reload_time': 2000,
            'sfx':join('audio', 'guns', 'mp5.mp3'),
            'description': 'Submachine gun'
        },
        'ak47': {
            'name': 'AK-47',
            'price': 3500,
            'damage': 15,
            'fire_rate': 6,
            'magazine': 30,
            'reload_time': 2500,
            'sfx':join('audio', 'guns', 'ak47.mp3'),
            'description': 'Assault rifle'
        },
        'shotgun': {
            'name': 'Shotgun',
            'price': 2500,
            'damage': 35,
            'fire_rate': 2,
            'magazine': 8,
            'reload_time': 3000,
            'sfx':join('audio', 'guns', 'shotgun.mp3'),
            'description': 'Close quarters'
        },
        'sniper': {
            'name': 'Sniper',
            'price': 5000,
            'damage': 50,
            'fire_rate': 2.5,
            'magazine': 5,
            'reload_time': 4000,
            'sfx':join('audio', 'guns', 'sniper.mp3'),
            'description': 'Heavy weapon'
        },
    }
    
    @classmethod
    def get_gun_list(cls):
        """Return list of gun keys."""
        return list(cls.GUNS.keys())
    
    @classmethod
    def get_gun_data(cls, gun_key):
        """Get data for a specific gun."""
        return cls.GUNS.get(gun_key, None)


class ShopUI:
    """Interactive shop UI for buying guns."""
    
    def __init__(self, display_surface, font, font_small):
        self.display_surface = display_surface
        self.font = font
        self.font_small = font_small
        
        # Shop grid
        self.grid_cols = 3
        self.grid_rows = 2  # Changed to 2x3 for 6 guns instead of 3x3
        self.grid_padding = 20
        self.cell_width = (WINDOW_WIDTH // 2 - 60) // self.grid_cols
        self.cell_height = 150
        
        # Grid position (right side of screen)
        self.grid_start_x = WINDOW_WIDTH // 2 + 40
        self.grid_start_y = 100
        
        # Preview (left side)
        self.preview_width = WINDOW_WIDTH // 2 - 60
        self.preview_start_x = 20
        self.preview_start_y = 100
        
        # Selection
        self.selected_gun_index = 0
        self.gun_list = GunData.get_gun_list()
        
        # Player money (will be updated from Game class)
        self.player_money = 5000
        self.owned_guns = set()  # Track owned guns
        
        # Gun sprites (will be set from Game class)
        self.gun_sprites = {}
    
    def load_gun_sprites(self):
        """Load gun sprites from images/gun/ folder."""
        self.gun_sprites = {}
        
        for gun_key in self.gun_list:
            # Expected filename: gun_key.png (e.g., glock.png, revolver.png)
            sprite_path = join('images', 'gun', f'{gun_key}.png')
            
            try:
                surf = pygame.image.load(sprite_path).convert_alpha()
                self.gun_sprites[gun_key] = surf
            except pygame.error as e:
                print(f"Warning: Could not load sprite for {gun_key}: {e}")
                # Create a placeholder surface if file not found
                self.gun_sprites[gun_key] = pygame.Surface((64, 32))
                self.gun_sprites[gun_key].fill((100, 100, 100))
    
    def get_grid_position(self, index):
        """Convert grid index to screen position."""
        row = index // self.grid_cols
        col = index % self.grid_cols
        x = self.grid_start_x + col * (self.cell_width + self.grid_padding)
        y = self.grid_start_y + row * (self.cell_height + self.grid_padding)
        return (x, y, self.cell_width, self.cell_height)
    
    def handle_mouse_click(self, mouse_pos):
        """Handle gun selection via mouse click."""
        for i, gun_key in enumerate(self.gun_list):
            x, y, w, h = self.get_grid_position(i)
            gun_rect = pygame.Rect(x, y, w, h)
            
            if gun_rect.collidepoint(mouse_pos):
                self.selected_gun_index = i
                return gun_key
        
        return None
    
    def can_afford_gun(self, gun_key):
        """Check if player can afford the gun."""
        gun_data = GunData.get_gun_data(gun_key)
        return self.player_money >= gun_data['price']
    
    def buy_gun(self, gun_key, owned):
        """Purchase a gun."""
        gun_data = GunData.get_gun_data(gun_key)
        
        if gun_key in self.owned_guns:
            return True

        if self.can_afford_gun(gun_key) and gun_key not in owned:
            self.player_money -= gun_data['price']
            self.owned_guns.add(gun_key)
            return True
        
        return False
    
    def draw_preview(self):
        """Draw large preview of selected gun on the left side."""
        gun_key = self.gun_list[self.selected_gun_index]
        gun_data = GunData.get_gun_data(gun_key)
        
        # Background box
        preview_rect = pygame.Rect(self.preview_start_x, self.preview_start_y, 
                                   self.preview_width, 400)
        pygame.draw.rect(self.display_surface, (40, 40, 40), preview_rect)
        pygame.draw.rect(self.display_surface, (100, 100, 100), preview_rect, 3)
        
        # Gun name
        name_surf = self.font.render(gun_data['name'], True, (255, 255, 255))
        name_rect = name_surf.get_frect(topleft=(self.preview_start_x + 20, self.preview_start_y + 20))
        self.display_surface.blit(name_surf, name_rect)
        
        # Gun sprite (if available)
        if gun_key in self.gun_sprites:
            sprite = self.gun_sprites[gun_key]
            # Scale sprite to fit preview area (max 200 pixels wide)
            max_width = 250            
            scale_factor = max_width / sprite.get_width()
            new_size = (int(sprite.get_width() * scale_factor), 
                        int(sprite.get_height() * scale_factor))
            sprite = pygame.transform.scale(sprite, new_size)
        
            sprite_rect = sprite.get_frect(center=(self.preview_start_x + self.preview_width // 2,
                                                    self.preview_start_y + 150))
            self.display_surface.blit(sprite, sprite_rect)
        
        # Gun stats
        stats_y = self.preview_start_y + 250
        stats = [
            f"Damage: {gun_data['damage']}",
            f"Fire Rate: {gun_data['fire_rate']}/s",
            f"Magazine: {gun_data['magazine']}",
            f"Price: ${gun_data['price']}",
        ]
        
        for stat in stats:
            stat_surf = self.font_small.render(stat, True, (200, 200, 200))
            self.display_surface.blit(stat_surf, (self.preview_start_x + 20, stats_y))
            stats_y += 35
        
        # Owned indicator
        if gun_key in self.owned_guns:
            owned_surf = self.font_small.render("[OWNED]", True, (100, 255, 100))
            self.display_surface.blit(owned_surf, (self.preview_start_x + 20, stats_y + 20))
    
    def draw_grid(self):
        """Draw 2x3 grid of guns with prices."""
        for i, gun_key in enumerate(self.gun_list):
            gun_data = GunData.get_gun_data(gun_key)
            x, y, w, h = self.get_grid_position(i)
            
            # Cell background
            is_selected = (i == self.selected_gun_index)
            cell_color = (60, 80, 120) if is_selected else (40, 40, 40)
            pygame.draw.rect(self.display_surface, cell_color, (x, y, w, h))
            
            # Border
            border_color = (255, 200, 0) if is_selected else (100, 100, 100)
            border_width = 4 if is_selected else 2
            pygame.draw.rect(self.display_surface, border_color, (x, y, w, h), border_width)
            
            # Gun name
            name_surf = self.font_small.render(gun_data['name'], True, (255, 255, 255))
            name_rect = name_surf.get_frect(center=(x + w // 2, y + 20))
            self.display_surface.blit(name_surf, name_rect)
            
            # Gun sprite in cell (small thumbnail)
            if gun_key in self.gun_sprites:
                sprite = self.gun_sprites[gun_key]
                # Scale to fit in cell (max 60 pixels wide)
                adjust = 90
                scale_factor = adjust / sprite.get_width()
                new_size = (int(sprite.get_width() * scale_factor), 
                            int(sprite.get_height() * scale_factor))
                sprite = pygame.transform.scale(sprite, new_size)
                
                sprite_rect = sprite.get_frect(center=(x + w // 2, y + adjust - 20))
                self.display_surface.blit(sprite, sprite_rect)
            
            # Price
            price_color = (100, 255, 100) if self.can_afford_gun(gun_key) else (255, 100, 100)
            price_surf = self.font_small.render(f"${gun_data['price']}", True, price_color)
            price_rect = price_surf.get_frect(center=(x + w // 2, y + h - 25))
            self.display_surface.blit(price_surf, price_rect)
            
            # Owned indicator
            if gun_key in self.owned_guns:
                owned_surf = self.font_small.render("✓", True, (100, 255, 100))
                self.display_surface.blit(owned_surf, (x + w - 25, y + 5))
    
    def draw_player_money(self):
        """Draw player's current money in top corner."""
        money_surf = self.font.render(f"Money: ${self.player_money}", True, (255, 255, 0))
        money_rect = money_surf.get_frect(topright=(WINDOW_WIDTH - 20, 20))
        self.display_surface.blit(money_surf, money_rect)
    
    def draw(self):
        """Draw entire shop UI."""
        self.draw_preview()
        self.draw_grid()
        self.draw_player_money()