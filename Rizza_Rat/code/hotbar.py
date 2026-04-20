import pygame
from os.path import join

class Hotbar:
    """Hotbar UI for displaying equipped guns (slots 1 and 2)."""
    
    def __init__(self, x, y, font_small, font_medium):
        self.x = x
        self.y = y
        self.font_small = font_small
        self.font_medium = font_medium
        
        # Hotbar settings
        self.slot_size = 60
        self.slot_spacing = 20
        self.num_slots = 2
        
        # Gun slots: {1: 'glock', 2: None}
        self.slots = {1: None, 2: None}
        self.current_slot = 1
        
        # Gun sprites cache
        self.gun_sprites = {}
        
        # Colors
        self.bg_color = (0, 0, 0, 150)  # Semi-transparent black
        self.border_color = (100, 150, 200)
        self.selected_border_color = (200, 200, 0)  # Yellow for selected
        self.empty_color = (50, 50, 50)
        self.text_color = (240, 240, 240)
        
        self.selected_slot = 1  # Currently selected slot
    
    def load_gun_sprite(self, gun_key):
        """Load gun sprite if not already cached."""
        if gun_key not in self.gun_sprites:
            try:
                gun_path = join('images', 'gun', f'{gun_key}.png')
                sprite = pygame.image.load(gun_path).convert_alpha()
                # Scale to fit slot
                sprite = pygame.transform.scale(sprite, (self.slot_size - 10, self.slot_size - 10))
                self.gun_sprites[gun_key] = sprite
            except:
                self.gun_sprites[gun_key] = None
    
    def equip_gun(self, slot, gun_key):
        """Equip a gun in a slot (1 or 2)."""
        if slot in self.slots and gun_key:
            self.slots[slot] = gun_key
            self.load_gun_sprite(gun_key)
            # print(f"✓ Equipped {gun_key} to slot {slot}")
    
    def add_gun_to_queue(self, gun_key):
        """Add gun to hotbar (pushes existing guns forward)."""
        # If slot 1 is empty, fill it
        if self.slots[1] is None:
            self.equip_gun(1, gun_key)
            self.selected_slot = 1
        # If slot 2 is empty, fill it
        elif self.slots[2] is None:
            self.equip_gun(2, gun_key)
        # Both full: push slot 2 to front, new gun to slot 2
        else:
            self.slots[1] = self.slots[2]
            self.equip_gun(2, gun_key)
    
    def select_slot(self, slot):
        """Select a hotbar slot (1 or 2)."""
        if slot in self.slots and self.slots[slot] is not None:
            self.selected_slot = slot
            return self.slots[slot]
        return None
    
    def get_selected_gun(self):
        """Get currently selected gun."""
        return self.slots.get(self.selected_slot)
    
    def draw(self, surface):
        """Draw hotbar on surface."""
        for slot_num in range(1, self.num_slots + 1):
            slot_x = self.x + (slot_num - 1) * (self.slot_size + self.slot_spacing)
            slot_y = self.y
            slot_rect = pygame.Rect(slot_x, slot_y, self.slot_size, self.slot_size)
            
            # Determine colors
            if slot_num == self.selected_slot:
                border_color = self.selected_border_color
                border_width = 3
            else:
                border_color = self.border_color
                border_width = 2
            
            # Draw semi-transparent background
            surf = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
            surf.fill(self.bg_color)
            surface.blit(surf, (slot_x, slot_y))
            
            # Draw border
            pygame.draw.rect(surface, border_color, slot_rect, border_width)
            
            # Draw gun sprite or empty slot
            gun_key = self.slots.get(slot_num)
            if gun_key and gun_key in self.gun_sprites:
                sprite = self.gun_sprites[gun_key]
                if sprite:
                    # Center sprite in slot
                    sprite_x = slot_x + (self.slot_size - sprite.get_width()) // 2
                    sprite_y = slot_y + (self.slot_size - sprite.get_height()) // 2
                    surface.blit(sprite, (sprite_x, sprite_y))
            
            # Draw key number at bottom
            key_text = str(slot_num)
            key_surf = self.font_medium.render(key_text, True, self.text_color)
            key_rect = key_surf.get_frect(center=(slot_x + self.slot_size // 2, slot_y + self.slot_size - 10))
            surface.blit(key_surf, key_rect)
            
            # Draw gun name if equipped
            if gun_key:
                name_text = gun_key.upper()
                name_surf = self.font_small.render(name_text, True, self.text_color)
                name_rect = name_surf.get_frect(center=(slot_x + self.slot_size // 2, slot_y + 8))
                surface.blit(name_surf, name_rect)