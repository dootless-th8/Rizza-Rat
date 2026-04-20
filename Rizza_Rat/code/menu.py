from settings import *

class Button:
    def __init__(self, rect, text, font, callback=None):

        # Attributes
        self.rect = rect
        self.text = text
        self.font = font
        self.callback = callback
        self.is_hovered = False

        # Colors
        self.color_normal = (10, 94, 176)
        self.color_hover = (10, 151, 176)
        self.color_border = (150, 150, 150)
        self.text_color = (240, 240, 240)


    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)


    def draw(self, surface):
        # Bg
        color = self.color_hover if self.is_hovered else self.color_normal
        pygame.draw.rect(surface, color, self.rect)
        # Border
        pygame.draw.rect(surface, self.color_border, self.rect, 3)
        # Text
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_frect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_click(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos) and self.callback:
            self.callback()
            return True
        return False
    

class MainMenu:
    def __init__(self, display_surface, font_large, font_medium):
        self.display_surface = display_surface
        self.font_large = font_large
        self.font_medium = font_medium

        self.running = True
        ## States: 'game', 'settings', 'statistics', None
        self.selected_state = None

        self.buttons = self.create_buttons()

    def create_buttons(self):
        button_width = 200
        button_height = 50
        button_x = (WINDOW_WIDTH - WINDOW_HEIGHT) // 2

        start_y = WINDOW_HEIGHT // 2 - 100
        spacing = 70

        buttons = [
            Button(
                pygame.Rect(button_x, start_y, button_width, button_height),
                "Start Game",
                self.font_medium,
                callback=self._on_start_game
            ),
            Button(
                pygame.Rect(button_x, start_y + spacing, button_width, button_height),
                "Settings",
                self.font_medium,
                callback=self._on_settings
            ),
            Button(
                pygame.Rect(button_x, start_y + spacing * 2, button_width, button_height),
                "Statistics",
                self.font_medium,
                callback=self._on_statistics
            ),
            Button(
                pygame.Rect(button_x, start_y + spacing * 3, button_width, button_height),
                "Quit",
                self.font_medium,
                callback=self._on_quit
            ),
        ]
        
        return buttons
    
    # Callback functions
    def _on_start_game(self):
        """Start game button clicked."""
        print("Starting game...")
        self.selected_state = 'game'
        self.running = False
    
    def _on_settings(self):
        """Settings button clicked."""
        self.selected_state = 'settings'
        self.running = False
    
    def _on_statistics(self):
        """Statistics button clicked."""
        self.selected_state = 'statistics'
        self.running = False
    
    def _on_quit(self):
        """Quit button clicked."""
        print("Quitting game...")
        self.selected_state = 'quit'
        self.running = False
    
    def handle_events(self):
        """Handle menu input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.selected_state = 'quit'
                self.running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    for button in self.buttons:
                        button.handle_click(mouse_pos)
            
            # Optional: Allow ESC to quit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.selected_state = 'quit'
                    self.running = False
    
    def update(self):
        """Update menu state."""
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
    
    def draw(self):
        """Draw menu."""
        # Background
        self.display_surface.fill((20, 20, 20))
        
        # Title
        title_surf = self.font_large.render("Rizza-Rat", True, (240, 240, 240))
        title_rect = title_surf.get_frect(center=(WINDOW_WIDTH // 2, 80))
        self.display_surface.blit(title_surf, title_rect)
        
        # Buttons
        for button in self.buttons:
            button.draw(self.display_surface)
        
        # Optional: Version/Footer text
        footer_font = pygame.font.Font(None, 20)
        footer_surf = footer_font.render("v1.0", True, (100, 100, 100))
        footer_rect = footer_surf.get_frect(bottomright=(WINDOW_WIDTH - 10, WINDOW_HEIGHT - 10))
        self.display_surface.blit(footer_surf, footer_rect)
        
        pygame.display.update()
    
    def run(self):
        """Run main menu loop."""
        clock = pygame.time.Clock()
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(60)  # 60 FPS
        
        return self.selected_state