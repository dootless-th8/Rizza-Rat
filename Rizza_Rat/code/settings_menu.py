import pygame
from settings import *
from os.path import join

class Slider:        
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.font = font
        
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        
        # Slider bar
        self.slider_rect = pygame.Rect(x, y + 30, width, 10)
        self.knob_radius = 8
        
        # Colors
        self.bg_color = (50, 50, 50)
        self.slider_color = (100, 150, 200)
        self.knob_color = (150, 200, 255)
        self.text_color = (240, 240, 240)
        
        self.dragging = False
    
    def get_knob_pos(self):        
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        x = self.slider_rect.x + ratio * self.slider_rect.width
        y = self.slider_rect.y + self.slider_rect.height // 2
        return (x, y)
    
    def update(self, mouse_pos, mouse_pressed):
        # Update slider
        knob_pos = self.get_knob_pos()
        knob_rect = pygame.Rect(knob_pos[0] - self.knob_radius, knob_pos[1] - self.knob_radius, 
                               self.knob_radius * 2, self.knob_radius * 2)
        
        # Check if mouse over knob
        if mouse_pressed[0]:
            if knob_rect.collidepoint(mouse_pos) or self.dragging:
                self.dragging = True
                # Update value based on mouse pos
                relative_x = max(0, min(mouse_pos[0] - self.slider_rect.x, self.slider_rect.width))
                ratio = relative_x / self.slider_rect.width
                self.value = int(self.min_val + ratio * (self.max_val - self.min_val))
        else:
            self.dragging = False
    
    def draw(self, surface):        
        # Label
        label_surf = self.font.render(f"{self.label}: {self.value}", True, self.text_color)
        surface.blit(label_surf, (self.rect.x, self.rect.y))
        
        # Slider background
        pygame.draw.rect(surface, self.bg_color, self.slider_rect)
        pygame.draw.rect(surface, self.text_color, self.slider_rect, 2)
        
        # Slider bar (filled portion)
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        filled_width = self.slider_rect.width * ratio
        filled_rect = pygame.Rect(self.slider_rect.x, self.slider_rect.y, filled_width, self.slider_rect.height)
        pygame.draw.rect(surface, self.slider_color, filled_rect)
        
        # Knob
        knob_pos = self.get_knob_pos()
        pygame.draw.circle(surface, self.knob_color, knob_pos, self.knob_radius)


class SettingsMenu:        
    def __init__(self, display_surface, font_large, font_medium, font_small, settings_manager):
        self.display_surface = display_surface
        self.font_large = font_large
        self.font_medium = font_medium
        self.font_small = font_small
        self.settings_manager = settings_manager
        
        self.running = True
        self.result = None  # 'back' or 'apply'
        
        # Create controls
        self.volume_slider = None
        self.fullscreen_toggle = None
        self.buttons = []
        self._create_controls()
    
    def _create_controls(self):
        # Create settings controls.
        start_y = 150
        spacing = 120
        
        # Volume slider
        volume = self.settings_manager.get('volume', 100)
        self.volume_slider = Slider(
            x=150, y=start_y, width=400, height=50,
            min_val=0, max_val=100, initial_val=volume,
            label="Volume",
            font=self.font_small
        )        
        
        # Create buttons
        button_y = start_y + spacing * 2 + 50
        self._create_buttons(button_y)
    
    def _create_buttons(self, y):        
        from menu import Button
        
        button_width = 150
        button_height = 50
        spacing = 180
        start_x = (1280 - (button_width * 2 + spacing)) // 2
        
        self.apply_button = Button(
            pygame.Rect(start_x, y, button_width, button_height),
            "Apply",
            self.font_medium,
            callback=self._on_apply
        )
        
        self.back_button = Button(
            pygame.Rect(start_x + button_width + spacing, y, button_width, button_height),
            "Back",
            self.font_medium,
            callback=self._on_back
        )
        
        self.buttons = [self.apply_button, self.back_button]
    
    def _on_apply(self):
        # Apply settings and return to menu.
        self.settings_manager.set('volume', self.volume_slider.value)
        print("Settings applied!")
        print(f"  Volume: {self.volume_slider.value}")
        self.result = 'apply'
        self.running = False
    
    def _on_back(self):
        # Go back to menu without applying.
        self.result = 'back'
        self.running = False
    
    def handle_events(self):        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.result = 'quit'
                self.running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check button clicks
                for button in self.buttons:
                    button.handle_click(mouse_pos)                                
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._on_back()
        
        # Update slider
        self.volume_slider.update(mouse_pos, mouse_pressed)
    
    def update(self):
        # Update menu state
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
        
    
    def draw(self):        
        # Background
        self.display_surface.fill((20, 20, 20))
        
        # Title
        title_surf = self.font_large.render("Settings", True, (240, 240, 240))
        title_rect = title_surf.get_frect(center=(1280 // 2, 50))
        self.display_surface.blit(title_surf, title_rect)
        
        # Volume slider
        self.volume_slider.draw(self.display_surface)                        
        
        # Buttons
        for button in self.buttons:
            button.draw(self.display_surface)                
        
        pygame.display.update()
    
    def run(self):
        """Run settings menu loop."""
        clock = pygame.time.Clock()
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(60)
                