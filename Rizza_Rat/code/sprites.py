from settings import *
from math import atan2, degrees
from shop import GunData

# ---------------------------------------------------------------------------
# Mixer channel assignments
# ---------------------------------------------------------------------------
# Set at startup in main() via pygame.mixer.set_num_channels(16)
CH_BG         = 0   # background music  (looping)
CH_SHOP       = 1   # shop music         (looping)
CH_GUN        = 2   # gunshot — single channel means rapid fire interrupts
                    #           itself instead of stacking up
CH_RELOAD     = 3   # reload sound
CH_PLAYER_HIT = 4   # player-takes-damage — single channel, no stacking
CH_UI         = 5   # buy / UI sounds
# Channels 6-13: rotating pool for enemy death / hit sounds (8 slots)
_CH_ENEMY_POOL_START = 6
_CH_ENEMY_POOL_SIZE  = 8
_enemy_ch_idx        = 0   # module-level round-robin counter


def _next_enemy_channel():
    """Return the next channel in the enemy pool (round-robin)."""
    global _enemy_ch_idx
    ch = pygame.mixer.Channel(_CH_ENEMY_POOL_START + (_enemy_ch_idx % _CH_ENEMY_POOL_SIZE))
    _enemy_ch_idx += 1
    return ch


# ---------------------------------------------------------------------------

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)
        self.ground = True

class CollisionSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf        
        self.rect = self.image.get_frect(topleft = pos)

class Gun(pygame.sprite.Sprite):
    def __init__(self, player, groups, gun_key='glock', gen_vol=None):
        
        super().__init__(groups)
        # player 
        self.player = player
        self.distance = 100
        self.player_direction = pygame.Vector2(1,0)

        # Loads Sprite
        self.gun_key = gun_key
        self.gun_data = GunData.get_gun_data(gun_key)

        # Stats
        self.damage = self.gun_data['damage']
        self.fire_rate = self.gun_data['fire_rate']
        self.magazine = self.gun_data['magazine']
        self.reload_time = self.gun_data['reload_time']
        self.sfx_path = self.gun_data['sfx']
        self.current_ammo = self.magazine

        # Fire rate cooldown
        self.fire_cooldown = int(1000 / self.fire_rate) if self.fire_rate > 0 else 1000

        # Reload System
        self.is_reloading = False
        self.reload_start_time = 0

        self.gen_vol = gen_vol

        # Dedicated channels
        self._ch_gun    = pygame.mixer.Channel(CH_GUN)
        self._ch_reload = pygame.mixer.Channel(CH_RELOAD)

        # SFX
        if self.gen_vol is not None:
            self.shoot_sfx = pygame.mixer.Sound(self.sfx_path)
            self.shoot_sfx.set_volume(self.gen_vol / 3)

            self.rel_sfx = pygame.mixer.Sound(join('audio', 'guns', 'reload.mp3'))
            self.rel_sfx.set_volume(self.gen_vol / 3)

        # Load and set sprite
        self.load_gun_sprite(gun_key)

    def load_gun_sprite(self, gun_key):
        try:
            path = join('images', 'gun', f'{gun_key}.png')
            self.gun_surf = pygame.image.load(path).convert_alpha()
            self.image = self.gun_surf
        except pygame.error as e:
            print(f"Could not load the sprite {gun_key}: {e}")
            self.gun_surf = pygame.Surface((64, 64))
            self.gun_surf.fill((100, 100, 100))
            self.image = self.gun_surf

        self.rect = self.image.get_frect(
            center=self.player.rect.center + self.player_direction * self.distance
        )

    def equip_gun(self, gun_key):
        self.gun_key  = gun_key
        self.gun_data = GunData.get_gun_data(gun_key)

        # Re-stats
        self.damage      = self.gun_data['damage']
        self.fire_rate   = self.gun_data['fire_rate']
        self.magazine    = self.gun_data['magazine']
        self.current_ammo = self.magazine

        # Re-SFX
        self.sfx_path  = self.gun_data['sfx']
        self.shoot_sfx = pygame.mixer.Sound(self.sfx_path)
        self.shoot_sfx.set_volume(self.gen_vol / 3)

        # Fire-rate cooldown
        self.fire_cooldown = int(1000 / self.fire_rate) if self.fire_rate > 0 else 1000

        self.load_gun_sprite(gun_key)

    def start_reload(self):
        if not self.is_reloading and self.current_ammo < self.magazine:
            self.is_reloading = True
            self.reload_start_time = pygame.time.get_ticks()            
            self._ch_reload.play(self.rel_sfx)

    def update_reload(self):
        if self.is_reloading:
            elapsed = pygame.time.get_ticks() - self.reload_start_time
            if elapsed >= self.reload_time:
                self.current_ammo = self.magazine
                self.is_reloading = False

    def use_ammo(self):
        if self.is_reloading:
            return False

        if self.current_ammo > 0:
            self.current_ammo -= 1            
            self._ch_gun.play(self.shoot_sfx)
            return True
        else:
            self.start_reload()
            return False

    def get_direction(self):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        player_pos = pygame.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        diff = mouse_pos - player_pos
        if diff.length() > 0:
            self.player_direction = diff.normalize()

    def rotate_gun(self):
        angle = degrees(atan2(self.player_direction.x, self.player_direction.y)) - 90
        if self.player_direction.x > 0:
            self.image = pygame.transform.rotozoom(self.gun_surf, angle, 1)
        else:
            self.image = pygame.transform.rotozoom(self.gun_surf, abs(angle), 1)
            self.image = pygame.transform.flip(self.image, False, True)

    def update(self, _):
        self.get_direction()
        self.rotate_gun()
        self.update_reload()
        self.rect.center = self.player.rect.center + self.player_direction * self.distance


class Bullet(pygame.sprite.Sprite):
    def __init__(self, surf, pos, direction, groups, damage=100):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center=pos)

        self.spawn_time = pygame.time.get_ticks()
        self.life_time = 600

        self.direction = direction
        self.speed = 1200
        self.damage = damage

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if pygame.time.get_ticks() - self.spawn_time >= self.life_time:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    speed = 1
    health = 30
    damage = 10
    attack_cooldown = 500
    sfx_path = join('audio', 'enemies', 'hit.mp3')
    money_reward = 25

    def __init__(self, pos, frames, groups, player, collision_sprites, gen_vol=None):
        super().__init__(groups)
        self.player = player

        # image
        self.frames, self.frame_index = frames, 0
        self.image = self.frames[self.frame_index]
        self.animation_speed = 3

        # rect
        self.rect = self.image.get_frect(center=pos)
        self.hitbox_rect = self.rect.inflate(-20, -40)
        self.collision_sprites = collision_sprites
        self.direction = pygame.Vector2()

        # attributes
        self.speed = 1
        self.current_health = self.health

        # timers
        self.can_attack  = True
        self.attack_time = 0
        self.death_time  = 0
        self.death_duration = 400

        # SFX
        if gen_vol is not None:
            self.collide_sfx = pygame.mixer.Sound(self.sfx_path)
            self.collide_sfx.set_volume(gen_vol / 5)

            self.hit_sfx = pygame.mixer.Sound(join('audio', 'player_hit.mp3'))
            self.hit_sfx.set_volume(gen_vol)
            
            self._ch_player_hit = pygame.mixer.Channel(CH_PLAYER_HIT)

    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        self.image = self.frames[int(self.frame_index) % len(self.frames)]

    def move(self, dt):
        player_pos = pygame.Vector2(self.player.rect.center)
        enemy_pos  = pygame.Vector2(self.rect.center)
        self.direction = (player_pos - enemy_pos).normalize()

        self.hitbox_rect.x += self.direction.x * self.speed
        self.collsion('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed
        self.collsion('vertical')

        self.rect.center = self.hitbox_rect.center

    def collsion(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left  = sprite.rect.right
                elif direction == 'vertical':
                    if self.direction.y < 0: self.hitbox_rect.top    = sprite.rect.bottom
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprite.rect.top

    def take_damage(self, amount):
        self.current_health -= amount
        # Enemies sounds play cycling
        _next_enemy_channel().play(self.collide_sfx)
        if self.current_health <= 0:
            self.destroy()
            return True
        return False

    def destroy(self):
        self.death_time = pygame.time.get_ticks()
        surf = pygame.mask.from_surface(self.frames[0]).to_surface()
        surf.set_colorkey('black')
        self.image = surf

    def attack_player(self, player):
        if self.can_attack and self.death_time == 0:
            player.reduce_player_health(self.damage)            
            self._ch_player_hit.play(self.hit_sfx)
            self.can_attack  = False
            self.attack_time = pygame.time.get_ticks()

    def update_attack_timer(self):
        if not self.can_attack:
            if pygame.time.get_ticks() - self.attack_time >= self.attack_cooldown:
                self.can_attack = True

    def death_timer(self):
        if pygame.time.get_ticks() - self.death_time >= self.death_duration:
            self.kill()

    def update(self, dt):
        if self.death_time == 0:
            self.move(dt)
            self.animate(dt)
            self.update_attack_timer()
        else:
            self.death_timer()


class Bat(Enemy):
    speed = 0.75
    health = 30
    damage = 25
    attack_cooldown = 1500
    money_reward = 75
    sfx_path = join('audio', 'enemies', 'bat.mp3')


class Blob(Enemy):
    speed = 1.7
    health = 15
    damage = 5
    attack_cooldown = 1000
    sfx_path = join('audio', 'enemies', 'blob.mp3')

    def attack_player(self, player):
        if self.can_attack and self.death_time == 0:
            player.reduce_player_health(self.damage)
            self._ch_player_hit.play(self.hit_sfx)
            self.can_attack  = False
            self.attack_time = pygame.time.get_ticks()


class Skeleton(Enemy):
    speed = 1
    health = 45
    damage = 10
    attack_cooldown = 800
    money_reward = 125

    def __enrage(self):
        if self.current_health < self.health / 2:
            self.speed = 1.75

    def attack_player(self, player):
        if self.can_attack and self.death_time == 0:
            player.reduce_player_health(self.damage * 1.5)
            self._ch_player_hit.play(self.hit_sfx)
            self.can_attack  = False
            self.attack_time = pygame.time.get_ticks()

    def update(self, dt):
        if self.death_time == 0:
            self.move(dt)
            self.animate(dt)
            self.update_attack_timer()
            self.__enrage()
        else:
            self.death_timer()


class Vendor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect  = self.image.get_frect(center=pos)