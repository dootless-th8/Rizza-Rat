import pygame
import os
import csv
from settings import *
from menu import Button


# Which CSV columns to show per feature index
FEATURE_TABLE_CONFIG = {
    0: {'file': os.path.join('data', 'stats', 'enemy_kills.csv'),
        'cols': ['session_id', 'bat', 'blob', 'skeleton']},
    1: {'file': os.path.join('data', 'stats', 'weapon_usage.csv'),
        'cols': ['session_id', 'glock', 'revolver', 'mp5', 'ak47', 'shotgun', 'sniper']},
    2: {'file': os.path.join('data', 'stats', 'wave_data.csv'),
        'cols': ['session_id', 'wave', 'damage_taken']},
    3: {'file': os.path.join('data', 'stats', 'wave_data.csv'),
        'cols': ['session_id', 'wave', 'enemies_killed', 'currency_earned']},
    4: {'file': os.path.join('data', 'stats', 'wave_data.csv'),
        'cols': ['session_id', 'wave', 'completion_time']},
}


class ToggleButton:
    """A button that visually shows its on/off state."""
    def __init__(self, rect, label_on, label_off, font, callback=None):
        self.rect       = rect
        self.label_on   = label_on
        self.label_off  = label_off
        self.font       = font
        self.callback   = callback
        self.active     = False
        self.is_hovered = False

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_click(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.active = not self.active
            if self.callback:
                self.callback(self.active)
            return True
        return False

    def draw(self, surface):
        if self.active:
            bg_col     = (160, 100, 20)
            border_col = (230, 180, 60)
        elif self.is_hovered:
            bg_col     = (100, 100, 100)
            border_col = (180, 180, 180)
        else:
            bg_col     = (60, 60, 60)
            border_col = (130, 130, 130)

        pygame.draw.rect(surface, bg_col, self.rect, border_radius=6)
        pygame.draw.rect(surface, border_col, self.rect, 2, border_radius=6)

        label = self.label_on if self.active else self.label_off
        text_surf = self.font.render(label, True, (240, 240, 240))
        text_rect = text_surf.get_frect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class TableView:
    """Renders CSV data as a scrollable table inside a given rect."""

    ROW_H      = 32
    COL_PAD    = 16
    HEADER_COL = (40, 70, 120)
    ROW_COL_A  = (35, 35, 35)
    ROW_COL_B  = (28, 28, 28)
    BORDER_COL = (70, 70, 70)
    TEXT_COL   = (220, 220, 220)
    HEAD_TEXT  = (200, 220, 255)

    def __init__(self, rect, font):
        self.rect    = rect
        self.font    = font
        self.headers = []
        self.rows    = []
        self.scroll  = 0

    # ----------------------------------------------------------------- data --
    def load(self, filepath, cols):
        self.headers = []
        self.rows    = []
        self.scroll  = 0

        if not os.path.exists(filepath):
            return

        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                file_cols    = reader.fieldnames or []
                self.headers = [c for c in cols if c in file_cols]
                for row in reader:
                    self.rows.append([row.get(c, '') for c in self.headers])
        except Exception as e:
            print(f"Table load error: {e}")

    # --------------------------------------------------------------- scroll --
    def scroll_up(self, amount=3):
        self.scroll = max(0, self.scroll - amount)

    def scroll_down(self, amount=3):
        max_scroll = max(0, len(self.rows) - self._visible_rows() + 1)
        self.scroll = min(max_scroll, self.scroll + amount)

    def _visible_rows(self):
        return (self.rect.height - self.ROW_H) // self.ROW_H

    # ----------------------------------------------------------------- draw --
    def draw(self, surface):
        if not self.headers:
            msg = self.font.render('No data yet — play a game first!', True, (100, 100, 100))
            surface.blit(msg, msg.get_frect(center=self.rect.center))
            return

        n_cols  = len(self.headers)
        col_w   = max(80, (self.rect.width - 12) // n_cols)
        x0, y0  = self.rect.x, self.rect.y

        # Draw onto a clipping surface so rows don't spill outside rect
        clip = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

        # Header
        for ci, header in enumerate(self.headers):
            cell = pygame.Rect(ci * col_w, 0, col_w, self.ROW_H)
            pygame.draw.rect(clip, self.HEADER_COL, cell)
            pygame.draw.rect(clip, self.BORDER_COL, cell, 1)
            label = self._truncate(header, col_w - self.COL_PAD)
            t = self.font.render(label, True, self.HEAD_TEXT)
            clip.blit(t, t.get_frect(midleft=(cell.x + 8, cell.centery)))

        # Rows
        vis = self._visible_rows()
        for ri in range(vis):
            row_idx = self.scroll + ri
            if row_idx >= len(self.rows):
                break
            row_data = self.rows[row_idx]
            row_y    = (ri + 1) * self.ROW_H
            row_bg   = self.ROW_COL_A if ri % 2 == 0 else self.ROW_COL_B

            for ci, value in enumerate(row_data):
                cell = pygame.Rect(ci * col_w, row_y, col_w, self.ROW_H)
                pygame.draw.rect(clip, row_bg, cell)
                pygame.draw.rect(clip, self.BORDER_COL, cell, 1)
                label = self._truncate(str(value), col_w - self.COL_PAD)
                t = self.font.render(label, True, self.TEXT_COL)
                clip.blit(t, t.get_frect(midleft=(cell.x + 8, cell.centery)))

        surface.blit(clip, (x0, y0))

        # Scrollbar (only if content overflows)
        if len(self.rows) > vis:
            total   = max(1, len(self.rows))
            bar_h   = self.rect.height
            bar_x   = x0 + n_cols * col_w + 2
            thumb_h = max(20, int(bar_h * vis / total))
            thumb_y = int((bar_h - thumb_h) * self.scroll / max(1, total - vis))
            pygame.draw.rect(surface, (50, 50, 50),
                             pygame.Rect(bar_x, y0, 8, bar_h))
            pygame.draw.rect(surface, (120, 160, 220),
                             pygame.Rect(bar_x, y0 + thumb_y, 8, thumb_h),
                             border_radius=4)

    def _truncate(self, text, max_px):
        if self.font.size(text)[0] <= max_px:
            return text
        while text and self.font.size(text + '…')[0] > max_px:
            text = text[:-1]
        return text + '…'


class StatsMenu:
    GRAPH_LABELS = [
        'Enemy Types Defeated',
        'Weapon Usage Frequency',
        'Damage Taken Per Wave',
        'Currency vs Enemies',
        'Wave Completion Time',
    ]

    PANEL_W = 240

    def __init__(self, display_surface, font_large, font_medium, font_small):
        self.display_surface = display_surface
        self.font_large  = font_large
        self.font_medium = font_medium
        self.font_small  = font_small

        self.running    = True
        self.selected   = 0
        self.show_table = False

        # Content area (right side)
        self.content_rect = pygame.Rect(
            self.PANEL_W + 20, 80,
            WINDOW_WIDTH - self.PANEL_W - 40,
            WINDOW_HEIGHT - 100
        )

        # Graph images
        self.graph_images = [None] * 5
        self._load_all_graphs()

        # Table view
        table_font = pygame.font.Font(None, 22)
        self.table_view = TableView(self.content_rect, table_font)

        # Buttons
        self.feature_buttons = self._create_feature_buttons()
        self.back_button = Button(
            pygame.Rect(20, WINDOW_HEIGHT - 60, self.PANEL_W - 40, 45),
            'Back', self.font_small, callback=self._on_back,
        )

        # Toggle button — top right corner
        tog_w, tog_h = 110, 38
        self.toggle_button = ToggleButton(
            pygame.Rect(WINDOW_WIDTH - tog_w - 16, 18, tog_w, tog_h),
            label_on='Graph',     # shown when table is active (click to go back)
            label_off='Table',    # shown when graph is active (click to switch)
            font=self.font_small,
            callback=self._on_toggle,
        )

    # ---------------------------------------------------------------- helpers -
    def _load_all_graphs(self):
        for i in range(5):
            self._try_load_graph(i)

    def _try_load_graph(self, idx):
        path = os.path.join('stats', f'{idx + 1}.png')
        if os.path.exists(path):
            try:
                self.graph_images[idx] = pygame.image.load(path).convert()
            except Exception as e:
                print(f"Could not load graph {idx+1}: {e}")

    def _create_feature_buttons(self):
        buttons = []
        btn_w, btn_h = self.PANEL_W - 40, 52
        start_y, gap = 90, 60
        for i, label in enumerate(self.GRAPH_LABELS):
            btn = Button(
                pygame.Rect(20, start_y + i * gap, btn_w, btn_h),
                label, self.font_small,
                callback=lambda idx=i: self._select(idx),
            )
            buttons.append(btn)
        return buttons

    def _select(self, idx):
        self.selected = idx
        self._try_load_graph(idx)
        if self.show_table:
            self._reload_table()

    def _on_back(self):
        self.running = False

    def _on_toggle(self, is_table_now):
        self.show_table = is_table_now
        if self.show_table:
            self._reload_table()

    def _reload_table(self):
        cfg = FEATURE_TABLE_CONFIG.get(self.selected, {})
        self.table_view.load(cfg.get('file', ''), cfg.get('cols', []))

    # --------------------------------------------------------------- events --
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mp = pygame.mouse.get_pos()
                self.toggle_button.handle_click(mp)
                for btn in self.feature_buttons:
                    btn.handle_click(mp)
                self.back_button.handle_click(mp)

            elif event.type == pygame.MOUSEWHEEL:
                if self.show_table:
                    if event.y > 0:
                        self.table_view.scroll_up()
                    else:
                        self.table_view.scroll_down()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.show_table:
                    if event.key == pygame.K_UP:
                        self.table_view.scroll_up(1)
                    elif event.key == pygame.K_DOWN:
                        self.table_view.scroll_down(1)

    def update(self):
        mp = pygame.mouse.get_pos()
        for btn in self.feature_buttons:
            btn.update(mp)
        self.back_button.update(mp)
        self.toggle_button.update(mp)

    # --------------------------------------------------------------- drawing --
    def draw(self):
        self.display_surface.fill((20, 20, 20))

        # Title
        title_surf = self.font_large.render('Statistics', True, (240, 240, 240))
        title_rect = title_surf.get_frect(midtop=(WINDOW_WIDTH // 2, 8))
        self.display_surface.blit(title_surf, title_rect)

        # Divider
        pygame.draw.line(
            self.display_surface, (70, 70, 70),
            (self.PANEL_W, 75), (self.PANEL_W, WINDOW_HEIGHT - 10), 2
        )

        # Feature buttons
        for i, btn in enumerate(self.feature_buttons):
            if i == self.selected:
                pygame.draw.rect(self.display_surface, (50, 90, 150),
                                 btn.rect.inflate(6, 6), border_radius=4)
            btn.draw(self.display_surface)

        self.back_button.draw(self.display_surface)
        self.toggle_button.draw(self.display_surface)

        # Right panel — table or graph
        if self.show_table:
            self.table_view.draw(self.display_surface)
        else:
            img = self.graph_images[self.selected]
            if img:
                rw, rh     = self.content_rect.width, self.content_rect.height
                iw, ih     = img.get_size()
                scale      = min(rw / iw, rh / ih)
                new_w, new_h = int(iw * scale), int(ih * scale)
                scaled     = pygame.transform.smoothscale(img, (new_w, new_h))
                blit_x     = self.content_rect.x + (rw - new_w) // 2
                blit_y     = self.content_rect.y + (rh - new_h) // 2
                self.display_surface.blit(scaled, (blit_x, blit_y))
            else:
                msg  = self.font_medium.render('No data yet — play a game first!', True, (100, 100, 100))
                mrec = msg.get_frect(center=self.content_rect.center)
                self.display_surface.blit(msg, mrec)

        pygame.display.update()

    # ------------------------------------------------------------------ loop --
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(60)