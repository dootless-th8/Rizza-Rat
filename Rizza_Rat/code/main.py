from settings import *
from player import Player
from sprites import *          # also imports CH_BG, CH_SHOP, CH_UI
from groups import AllSprites
from shop import ShopUI, GunData
from menu import MainMenu
from hotbar import Hotbar

from settings_manager import SettingsManager
from settings_menu import SettingsMenu
from statistics_manager import StatisticsManager   
from stats_menu import StatsMenu                   

from pytmx.util_pygame import load_pygame
from random import randint, choice
import random
# requirement: pytmx

class Game:
    def __init__(self, settings_manager, display_surface):
        # setup
        self.settings_manager = settings_manager
        self.display_surface = display_surface            
        
        # pygame.display.set_caption('Rizza-Rat')
        self.clock = pygame.time.Clock()
        self.running = True

        # groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.player_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.vendor_sprites = pygame.sprite.Group()
        
        self.ENEMY_CLASSES = {
            'bat': Bat,
            'blob': Blob,
            'skeleton': Skeleton,
        }
        
        # Wave attibutes            
        self.wave = 0                  
        self.wave_totals = self._calculate_wave_total()
        self.enemy_killed = 0
        self.enemy_spawned = 0
        self.enemy_per_spawn = 15        

        # Gun timer
        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = 500

        # Enemy Attributes
        ## Enemy Timer
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 500)
        self.spawn_positions = []        

        # Shopping Atributes
        self.vendor_pos = pygame.Vector2()
        self.trader_duration = 60 * 10**3
        self.trader_start_time = 0
        self.trader_remaining = 0

        # Game state - will return this value to main loop
        self.should_return_to_menu = False

        # UI elements
        self.font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
        self.font_small = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 28)

        self.font_gun_med = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 25)
        self.font_gun_small = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 18)

        ## Shopping UI        
        self.player_money = 500
        self.owned_guns = {'glock'}
        self.current_gun = 'glock'

        # State of the Game
        ## States: 'playing', 'shopping', 'pause', 'game_over', 'victory'
        self.state = 'playing'

        # Audio
        self.gen_vol = self.settings_manager.get('volume') / 100

        # Dedicated channels for music & UI (never compete with gameplay sounds)
        self._ch_bg   = pygame.mixer.Channel(CH_BG)
        self._ch_shop = pygame.mixer.Channel(CH_SHOP)
        self._ch_ui   = pygame.mixer.Channel(CH_UI)

        ## UI sfx
        self.success_buy_sfx = pygame.mixer.Sound(join('audio', 'success_buy.mp3'))
        self.success_buy_sfx.set_volume(self.gen_vol / 8)
        ## Shop phase bg
        self.vendouring_sfx = pygame.mixer.Sound(join('audio', f'shop_{random.randint(1,3)}.mp3'))
        self.vendouring_sfx.set_volume(self.gen_vol / 3)
        ## Main bg music
        self.bg_sfx = pygame.mixer.Sound(join('audio', 'bg.mp3'))
        self.bg_sfx.set_volume(self.gen_vol / 3)
        self._ch_bg.play(self.bg_sfx, -1)


        # Setup
        self.load_images()
        self.setup()                
        
        # Intialize hotbar
        self.hotbar = Hotbar(x=WINDOW_WIDTH/2 - 60, y=WINDOW_HEIGHT -60, font_small=self.font_gun_small, font_medium=self.font_gun_med)
        self.hotbar.equip_gun(1, 'glock')
        self.hotbar.select_slot(1)

        # ---- Statistics ---------------------------------------------------- #
        self.stats_manager = StatisticsManager()
        # Begin tracking wave 0
        self.stats_manager.start_wave(
            self.player.health,
            self.player_money,
            pygame.time.get_ticks()
        )
        # -------------------------------------------------------------------- #

    # -------------------------------------------------------------------------
    # Setup helpers
    # -------------------------------------------------------------------------

    def _calculate_wave_total(self):
        return [5 + (i * 5) + (i ** 2) for i in range(10)]

    def load_images(self):
        self.bullet_surf = pygame.image.load(join('images', 'bullet', 'bullet.png')).convert_alpha()
        self.vendor_surf = pygame.image.load(join('images', 'ShopKeeper', 'coward_duck.png')).convert_alpha()
        self.gun_surf = pygame.image.load(join('images', 'gun', 'glock.png')).convert_alpha()

        folders = list(walk(join('images', 'enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join('images', 'enemies', folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key = lambda name: int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)
        
        # Set shop and load guns' surfaces
        self.shop_ui = ShopUI(self.display_surface, self.font, self.font_small)
        self.shop_ui.load_gun_sprites()

    def setup(self):
        map = load_pygame(join('data', 'maps', 'world.tmx'))
        # For randomising how many will spawn throughout the wave
 
        for x,y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)
        
        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for colli in map.get_layer_by_name('Collisions'):
            CollisionSprite((colli.x, colli.y), pygame.Surface((colli.width, colli.height)), self.collision_sprites)        

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites)
                self.gun = Gun(self.player, self.all_sprites, gun_key='glock', gen_vol=self.gen_vol)
            if obj.name == 'Enemy':
                self.spawn_positions.append((obj.x, obj.y))

            if obj.name == 'Vendor':
                self.vendor_pos = (obj.x, obj.y)

    # -------------------------------------------------------------------------
    # State transitions  (one place to enter / exit each state)
    # -------------------------------------------------------------------------

    def _enter_shopping(self):
        # --- Record wave stats BEFORE health is refilled ---
        self.stats_manager.record_wave_end(
            self.wave,
            self.player.health,
            self.enemy_killed,
            self.player_money,
            pygame.time.get_ticks()
        )
        # Save CSV + regenerate graphs immediately so menu always shows fresh data
        self.stats_manager.save_to_csv()
        # self.stats_manager.generate_graphs()

        self.state = 'shopping'
        self.trader_start_time = pygame.time.get_ticks()
        self.trader_remaining = self.trader_duration
        # Refill player's health
        self.player.health = 100
        # Spawn vendor once
        self.vendor = Vendor(self.vendor_surf, self.vendor_pos, (self.all_sprites, self.vendor_sprites))
        self._ch_bg.stop()
        self._ch_shop.play(self.vendouring_sfx, -1)

    def _exit_shopping(self):
        for sprite in self.vendor_sprites:
            sprite.kill()
        self.wave += 1
        self.enemy_spawned = 0
        self.enemy_killed = 0
        self.state = 'playing'
        self._ch_shop.stop()
        self._ch_bg.play(self.bg_sfx, -1)

        # --- Begin tracking the new wave ---
        self.stats_manager.start_wave(
            self.player.health,
            self.player_money,
            pygame.time.get_ticks()
        )


    def _enter_pause(self):
        self.state = 'pause'

    def _exit_pause(self):
        self.state = 'playing'

    def _return_to_menu(self):
        # Save & generate before leaving
        self.stats_manager.save_to_csv()
        self.stats_manager.generate_graphs()

        self.should_return_to_menu = True
        self.running = False        
        
        pygame.mixer.stop()

    # -------------------------------------------------------------------------
    # Input & timers
    # -------------------------------------------------------------------------

    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            if self.gun.is_reloading:
                # Can't shoot while reloading
                return
            
            if self.gun.use_ammo():
                pos = self.gun.rect.center + self.gun.player_direction * 50
                Bullet(self.bullet_surf, pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprites), damage=self.gun.damage)
                self.can_shoot = False
                self.shoot_time = pygame.time.get_ticks()
                # --- Track weapon usage ---
                self.stats_manager.record_shot(self.current_gun)
            

    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()            
            if current_time - self.shoot_time >= self.gun.fire_cooldown:
                self.can_shoot = True

    def trader_time(self):
        if self.state == 'shopping':
            elapsed = pygame.time.get_ticks() - self.trader_start_time
            self.trader_remaining = max(0, self.trader_duration - elapsed)
            if self.trader_remaining == 0:
                self._exit_shopping()

    # -------------------------------------------------------------------------
    # Collision
    # -------------------------------------------------------------------------
    def bullet_collision(self):
        if self.bullet_sprites:
            for bullet in self.bullet_sprites:
                hit_enemies = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                hit_environment = pygame.sprite.spritecollide(bullet, self.collision_sprites, False, pygame.sprite.collide_mask)
                
                if hit_enemies:
                    for sprite in hit_enemies:
                        if sprite.death_time == 0:
                            enemy_died = sprite.take_damage(bullet.damage)
                            if enemy_died:                            
                                self.enemy_killed += 1                                                            
                                self.player_money += sprite.money_reward
                                # --- Track enemy kill by type ---
                                enemy_type = type(sprite).__name__.lower()
                                self.stats_manager.record_enemy_kill(enemy_type)
                    # if self.current_gun != 'shotgun' or self.current_gun != 'sniper' or self.current_gun != 'revolver':
                    bullet.kill()                                   
         
                elif hit_environment:
                    bullet.kill()
                    

    # !Might have to put it in each enemy sprite
    # !Might fix it later
    def player_collision(self):
        if self.player.get_player_health() <= 0:
            self.state = 'game_over'
            return
        
        hit_enemies = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask)
        for enemy in hit_enemies:
            enemy.attack_player(self.player)
                  
    
    # -------------------------------------------------------------------------
    # Event handling  (each state owns its events)
    # -------------------------------------------------------------------------

    # Game state Section
    def handling_events(self, event):                
        if   self.state == 'playing':   self.playing_events(event)
        elif self.state == 'shopping':  self.shopping_events(event)
        elif self.state == 'buying':    self.buying_events(event)
        elif self.state == 'pause':     self.pause_events(event)
        elif self.state == 'game_over': self.game_over_events(event)
        elif self.state == 'victory':   self.victory_events(event)

    def playing_events(self, event):    

        #SFX

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._enter_pause()
            
            if event.key == pygame.K_r:
                # Reloading                
                self.gun.start_reload()
                
            # Hotbar slot selection 
            if event.key == pygame.K_1:
                selected_gun = self.hotbar.select_slot(1)
                if selected_gun:
                    self.gun.equip_gun(selected_gun)
                    self.current_gun = selected_gun

            if event.key == pygame.K_2:
                selected_gun = self.hotbar.select_slot(2)
                if selected_gun:
                    self.gun.equip_gun(selected_gun)                    
                    self.current_gun = selected_gun


        # Spawning enemy
        if event.type == self.enemy_event:
            wave_total = self.wave_totals[self.wave]
            remaining_to_spawn = wave_total - self.enemy_spawned
            alive = len(self.enemy_sprites)

            if remaining_to_spawn > 0 and alive < self.enemy_per_spawn:
                spawn_amount = min(random.randint(1, 3), remaining_to_spawn, self.enemy_per_spawn - alive)            
                for _ in range(spawn_amount):
                    enemy_type = choice(list(self.ENEMY_CLASSES.keys()))
                    enemy_class = self.ENEMY_CLASSES[enemy_type]
                    enemy_class(
                        choice(self.spawn_positions), 
                        self.enemy_frames[enemy_type], 
                        (self.all_sprites, self.enemy_sprites), 
                        self.player, self.collision_sprites, self.gen_vol
                    )                
                self.enemy_spawned += spawn_amount

            if self.enemy_spawned >= wave_total and self.enemy_killed >= wave_total:                
                if self.wave + 1 < len(self.wave_totals):
                    self._enter_shopping()
                else:
                    self.state = 'victory'

    def shopping_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._exit_shopping()       
            if event.key == pygame.K_e:
                if pygame.sprite.spritecollide(self.player, self.vendor_sprites, False):
                    self.state = 'buying' 

            # Hotbar slot selection
            if event.key == pygame.K_1:
                selected_gun = self.hotbar.select_slot(1)
                if selected_gun:
                    self.gun.equip_gun(selected_gun)
                    self.hotbar.current_slot = 1
                    self.current_gun = selected_gun

            if event.key == pygame.K_2:
                selected_gun = self.hotbar.select_slot(2)
                if selected_gun:
                    self.gun.equip_gun(selected_gun)
                    self.hotbar.current_slot = 2
                    self.current_gun = selected_gun

    def buying_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e or event.key == pygame.K_ESCAPE:
                self.state = 'shopping'
            
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            selected_gun = self.shop_ui.handle_mouse_click(mouse_pos)

            if selected_gun:
                if self.shop_ui.buy_gun(selected_gun, self.owned_guns):

                    # Hotbar
                    if selected_gun not in self.hotbar.slots.values():
                        self.hotbar.add_gun_to_queue(selected_gun)
                    
                        curr_selecting_gun = self.hotbar.select_slot(self.hotbar.current_slot)
                        # Owning                        
                        self.owned_guns.add(selected_gun)
                        self.gun.equip_gun(curr_selecting_gun)
                        self.current_gun = curr_selecting_gun
                                                
                        # Money
                        self.player_money = self.shop_ui.player_money
                                                
                    # Add sound
                    self._ch_ui.play(self.success_buy_sfx)
                else:
                    # Not enough
                    print(f"Not enough money for {selected_gun}!")
                    pass    

    def pause_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._exit_pause()
            if event.key == pygame.K_m:
                self._return_to_menu()

    def game_over_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Save before restarting
                self.stats_manager.save_to_csv()
                self.stats_manager.generate_graphs()
                self.__init__(self.settings_manager, self.display_surface)
            if event.key == pygame.K_m:
                self._return_to_menu()

    def victory_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Save before restarting
                self.stats_manager.save_to_csv()
                self.stats_manager.generate_graphs()
                self.__init__(self.settings_manager, self.display_surface)
            if event.key == pygame.K_m:
                self._return_to_menu()

    # -------------------------------------------------------------------------
    # Update
    # -------------------------------------------------------------------------

    def updating(self, dt):
        if self.state == 'playing':            
            self.input()                        
            self.all_sprites.update(dt)
            self.bullet_collision()
            self.player_collision()
            self.gun_timer()

        elif self.state == 'shopping':
            self.trader_time()
            self.all_sprites.update(dt)        

        elif self.state == 'pause':
            pass
    # -------------------------------------------------------------------------
    # Drawing helpers
    # -------------------------------------------------------------------------
    
    def _draw_hud(self):
        # Health + wave info 
        self.display_player_health(self.all_sprites.offset)
        self.display_wave_info(self.all_sprites.offset)
        # Display Money
        money_surf = self.font.render("$ " + str(self.player_money), True, (255, 255, 0))
        money_rect = money_surf.get_frect(topleft=(WINDOW_WIDTH - 45 * len(str(self.player_money)), WINDOW_HEIGHT - 60))
        self.display_surface.blit(money_surf, money_rect)


    def display_gun_info(self):
        gun_name = self.gun.gun_data['name']        
        ammo = self.gun.current_ammo
        magazine = self.gun.magazine

        if self.gun.is_reloading:
            gun_info = f"{gun_name} | SAUCING UP..."
        else:
            gun_info = f"{gun_name} | AMMO: {ammo}/{magazine}"

        text_surf = self.font_small.render(gun_info, True, (247, 127, 0))
        text_rect = text_surf.get_frect(topleft=(10, WINDOW_HEIGHT - 60))
        self.display_surface.blit(text_surf, text_rect)
    
    def display_player_health(self, offset):
        text_surf = self.font_gun_med.render("Hp " + str(int(self.player.get_player_health())), True, (255, 30, 0))
        text_rect = text_surf.get_frect(midbottom = self.player.rect.midtop + offset)    
        self.display_surface.blit(text_surf, text_rect)        

    def display_wave_info(self, offset):
        remaining = self.wave_totals[self.wave] - self.enemy_killed
        label = f'Wave {self.wave + 1}  |  Remaining: {remaining}'
        text_surf = self.font.render(label, True, (240, 240, 240))
        pos = pygame.Vector2(WINDOW_WIDTH / 2.5, -100)        
        text_rect = text_surf.get_frect(topright = self.player.rect.topright + pos + offset)    
        self.display_surface.blit(text_surf, text_rect)

    def display_trader_hud(self):
        seconds_left = self.trader_remaining // 1000
        timer_surf = self.font.render(f'Trader closes in: {seconds_left}s', True, (255, 255, 0))
        timer_rect = timer_surf.get_frect(midtop=(WINDOW_WIDTH / 2, 20))
        self.display_surface.blit(timer_surf, timer_rect)

        hint_surf = self.font_small.render('[ESC] Skip trader', True, (200, 200, 200))
        hint_rect = hint_surf.get_frect(midtop=(WINDOW_WIDTH / 2, 70))
        self.display_surface.blit(hint_surf, hint_rect)

    def display_vendor_prompt(self, offset):
        if pygame.sprite.spritecollide(self.player, self.vendor_sprites, False, pygame.sprite.collide_mask):
            text_surf = self.font.render(str('Shopping [E]'), True, (240, 240, 240))
            text_rect = text_surf.get_frect(midbottom = self.vendor.rect.midbottom + offset + pygame.Vector2(0,30))    
            self.display_surface.blit(text_surf, text_rect)

    def _draw_overlay(self, message, sub=None):
        # Generic centred overlay for pause / game over / victory.
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0, 160))
        self.display_surface.blit(overlay, (0,0))

        text_surf = self.font.render(message, True, (240, 240, 240))
        text_rect = text_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 30))
        self.display_surface.blit(text_surf, text_rect)

        if sub:
            sub_surf = self.font_small.render(sub, True, (180, 180, 180))
            sub_rect = sub_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 30))
            self.display_surface.blit(sub_surf, sub_rect)

    # -------------------------------------------------------------------------
    # Drawing  (state-driven)
    # -------------------------------------------------------------------------

    def drawing(self):
        self.display_surface.fill('black')

        if self.state == 'playing':
            self.all_sprites.draw(self.player.rect.center)
            self._draw_hud()        
            self.display_gun_info()        
            self.hotbar.draw(self.display_surface)                

        elif self.state == 'shopping':
            self.all_sprites.draw(self.player.rect.center)
            self._draw_hud()
            self.display_trader_hud()
            self.display_vendor_prompt(self.all_sprites.offset)
            self.hotbar.draw(self.display_surface)
        
        elif self.state == 'buying':
            self.all_sprites.draw(self.player.rect.center)
            
            # Draw transparent bg
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,100))
            self.display_surface.blit(overlay, (0,0))
            
            # Draw shopping UI
            self.shop_ui.player_money = self.player_money
            self.shop_ui.owned_guns = self.owned_guns
            self.shop_ui.draw()
            
            # Manual
            manual = self.font_small.render('[Click gun to buy] [E/ESC] Back | [1][2] Select hotbar slot', True, (200,200,200))
            manual_rect = manual.get_frect(midbottom=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 20))
            self.display_surface.blit(manual, manual_rect)

            self.hotbar.draw(self.display_surface)

        elif self.state == 'pause':
            self.all_sprites.draw(self.player.rect.center)
            self.hotbar.draw(self.display_surface)
            self._draw_hud()
            self._draw_overlay('PAUSED', '[ESC] Resume | [M] Main Menu')


        elif self.state == 'game_over':
            self._draw_overlay('GAME OVER', '[R] Restart | [M] Main Menu')
 
        elif self.state == 'victory':
            self._draw_overlay('YOU WIN!', '[R] Restart | [M] Main Menu')

    # -------------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------------

    def run(self):
        while self.running:
            # dt
            dt = self.clock.tick() / 450            

            # event loops
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False                         
                    pygame.mixer.stop()           

                self.handling_events(event)                                

            # update
            self.updating(dt)
            self.drawing()            
            pygame.display.update()        
 
 
def main():
    # Main stuffs

    from os import chdir, path
    chdir(path.dirname(__file__))
    chdir('..')    
    
    pygame.init()
    pygame.mixer.set_num_channels(16)  # 16 channels: 6 reserved + 8 enemy pool + 2 spare
    
    # Load settings
    settings_manager = SettingsManager()
    
    # fonts
    font_large = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 60)
    font_medium = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 25)
    font_small = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 15)
    
    
    # Create initial display                    
    display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Rizza-Rat')
    
    while True:
        # Show main menu
        menu = MainMenu(display_surface, font_large, font_medium)
        menu_result = menu.run()
        
        if menu_result == 'quit':
            print("Thanks for playing!")
            break
        
        elif menu_result == 'game':
            # Start the game with current display surface
            game = Game(settings_manager, display_surface)
            game.run()        
            
            # Check if game wants to return to menu
            if game.should_return_to_menu:                
                continue
        
        elif menu_result == 'settings':            
            settings_menu = SettingsMenu(display_surface, font_large, font_medium, font_small, settings_manager)
            settings_menu.run()                                                                    
        
        elif menu_result == 'statistics':
            stats_menu = StatsMenu(display_surface, font_large, font_medium, font_small)
            stats_menu.run()
    
    pygame.quit()

if __name__ == '__main__':
    main()