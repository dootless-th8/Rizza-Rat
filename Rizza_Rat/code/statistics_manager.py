import os
import csv
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend, no window needed
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime


class StatisticsManager:
    STATS_DIR  = 'stats'
    DATA_DIR   = os.path.join('data', 'stats')

    ENEMY_TYPES  = ['bat', 'blob', 'skeleton']
    WEAPON_TYPES = ['glock', 'revolver', 'mp5', 'ak47', 'shotgun', 'sniper']

    # ------------------------------------------------------------------ init --
    def __init__(self):
        os.makedirs(self.STATS_DIR, exist_ok=True)
        os.makedirs(self.DATA_DIR,  exist_ok=True)

        self.enemy_kills_file  = os.path.join(self.DATA_DIR, 'enemy_kills.csv')
        self.weapon_usage_file = os.path.join(self.DATA_DIR, 'weapon_usage.csv')
        self.wave_data_file    = os.path.join(self.DATA_DIR, 'wave_data.csv')

        self._init_csv_files()
        self.reset_session()

    def _init_csv_files(self):
        if not os.path.exists(self.enemy_kills_file):
            with open(self.enemy_kills_file, 'w', newline='') as f:
                csv.writer(f).writerow(['session_id'] + self.ENEMY_TYPES)

        if not os.path.exists(self.weapon_usage_file):
            with open(self.weapon_usage_file, 'w', newline='') as f:
                csv.writer(f).writerow(['session_id'] + self.WEAPON_TYPES)

        if not os.path.exists(self.wave_data_file):
            with open(self.wave_data_file, 'w', newline='') as f:
                csv.writer(f).writerow(
                    ['session_id', 'wave', 'damage_taken',
                     'enemies_killed', 'currency_earned', 'completion_time']
                )

    # --------------------------------------------------------- session state --
    def reset_session(self):
        self.session_id       = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.enemies_count    = {t: 0 for t in self.ENEMY_TYPES}
        self.weapons_count    = {t: 0 for t in self.WEAPON_TYPES}
        self.wave_records     = []

        # Per-wave tracking helpers (set via start_wave)
        self.wave_start_time_ms = 0
        self.wave_start_health  = 100
        self.wave_start_money   = 0

    # ------------------------------------------------------ in-game recorders --
    def start_wave(self, player_health, player_money, current_time_ms):
        """Call this at the start of every wave (including wave 0)."""
        self.wave_start_time_ms = current_time_ms
        self.wave_start_health  = player_health
        self.wave_start_money   = player_money

    def record_enemy_kill(self, enemy_type):
        if enemy_type in self.enemies_count:
            self.enemies_count[enemy_type] += 1

    def record_shot(self, gun_key):
        if gun_key in self.weapons_count:
            self.weapons_count[gun_key] += 1

    def record_wave_end(self, wave_num, player_health, enemies_killed,
                        player_money, current_time_ms):
        """Call this at wave end, BEFORE health is refilled."""
        damage_taken    = max(0, self.wave_start_health - player_health)
        currency_earned = max(0, player_money - self.wave_start_money)
        completion_time = round((current_time_ms - self.wave_start_time_ms) / 1000, 1)

        self.wave_records.append({
            'wave':            wave_num + 1,
            'damage_taken':    damage_taken,
            'enemies_killed':  enemies_killed,
            'currency_earned': currency_earned,
            'completion_time': completion_time,
        })

    # ----------------------------------------------------------------- saving --
    def save_to_csv(self):
        # Enemy kills
        with open(self.enemy_kills_file, 'a', newline='') as f:
            csv.writer(f).writerow(
                [self.session_id] + [self.enemies_count.get(t, 0) for t in self.ENEMY_TYPES]
            )

        # Weapon usage
        with open(self.weapon_usage_file, 'a', newline='') as f:
            csv.writer(f).writerow(
                [self.session_id] + [self.weapons_count.get(t, 0) for t in self.WEAPON_TYPES]
            )

        # Wave data (one row per wave)
        with open(self.wave_data_file, 'a', newline='') as f:
            writer = csv.writer(f)
            for wd in self.wave_records:
                writer.writerow([
                    self.session_id,
                    wd['wave'],          wd['damage_taken'],
                    wd['enemies_killed'], wd['currency_earned'],
                    wd['completion_time']
                ])

    # ------------------------------------------------------------- graphs -----
    def generate_graphs(self):
        try:
            self._graph_enemy_kills()
            self._graph_weapon_usage()
            self._graph_damage_per_wave()
            self._graph_currency_vs_enemies()
            self._graph_wave_completion_time()
            print("Graphs saved to stats/")
        except Exception as e:
            print(f"Graph generation error: {e}")

    # --- shared helpers ---
    def _apply_style(self):
        plt.rcParams.update({
            'figure.facecolor': '#1a1a1a',
            'axes.facecolor':   '#2a2a2a',
            'axes.edgecolor':   '#555555',
            'text.color':       '#e0e0e0',
            'axes.labelcolor':  '#e0e0e0',
            'xtick.color':      '#e0e0e0',
            'ytick.color':      '#e0e0e0',
            'grid.color':       '#444444',
        })

    def _load_csv(self, filepath):
        rows = []
        try:
            with open(filepath, 'r') as f:
                for row in csv.DictReader(f):
                    rows.append(row)
        except Exception:
            pass
        return rows

    def _save(self, filename):
        plt.tight_layout()
        plt.savefig(os.path.join(self.STATS_DIR, filename), dpi=100,
                    facecolor=plt.rcParams['figure.facecolor'])
        plt.close()

    # --- graph 1: bar ---
    def _graph_enemy_kills(self):
        self._apply_style()
        rows   = self._load_csv(self.enemy_kills_file)
        totals = {t: 0 for t in self.ENEMY_TYPES}
        for row in rows:
            for t in self.ENEMY_TYPES:
                try: totals[t] += int(row.get(t, 0))
                except ValueError: pass

        fig, ax = plt.subplots(figsize=(8, 5))
        colors = ['#e05252', '#52a0e0', '#52e09a']
        bars   = ax.bar(list(totals.keys()), list(totals.values()), color=colors, width=0.5)
        ax.set_title('Enemy Types Defeated', fontsize=14)
        ax.set_xlabel('Enemy Type')
        ax.set_ylabel('Total Defeated')
        ax.grid(axis='y', alpha=0.4)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(int(bar.get_height())), ha='center', va='bottom', fontsize=11)
        self._save('1.png')

    # --- graph 2: pie ---
    def _graph_weapon_usage(self):
        self._apply_style()
        rows   = self._load_csv(self.weapon_usage_file)
        totals = {t: 0 for t in self.WEAPON_TYPES}
        for row in rows:
            for t in self.WEAPON_TYPES:
                try: totals[t] += int(row.get(t, 0))
                except ValueError: pass

        # Only show weapons that were actually used
        filtered = {k: v for k, v in totals.items() if v > 0} or {'no data': 1}

        fig, ax = plt.subplots(figsize=(8, 5))
        colors  = ['#e05252', '#52a0e0', '#52e09a', '#e0c052', '#c052e0', '#52e0d4']
        ax.pie(
            list(filtered.values()),
            labels=list(filtered.keys()),
            autopct='%1.1f%%',
            colors=colors[:len(filtered)],
            textprops={'color': '#e0e0e0'},
        )
        ax.set_title('Weapon Usage Frequency', fontsize=14)
        self._save('2.png')

    # --- graph 3: line ---
    def _graph_damage_per_wave(self):
        self._apply_style()
        rows        = self._load_csv(self.wave_data_file)
        wave_damage = {}
        for row in rows:
            try:
                w = int(row['wave'])
                d = float(row['damage_taken'])
                wave_damage.setdefault(w, []).append(d)
            except (KeyError, ValueError): pass

        if wave_damage:
            waves   = sorted(wave_damage.keys())
            avg_dmg = [np.mean(wave_damage[w]) for w in waves]
        else:
            waves, avg_dmg = [1], [0]

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(waves, avg_dmg, color='#e05252', marker='o', linewidth=2, markersize=6)
        ax.fill_between(waves, avg_dmg, alpha=0.15, color='#e05252')
        ax.set_title('Player Damage Taken Per Wave', fontsize=14)
        ax.set_xlabel('Wave')
        ax.set_ylabel('Avg Damage Taken')
        ax.set_xticks(waves)
        ax.grid(alpha=0.4)
        self._save('3.png')

    # --- graph 4: scatter ---
    def _graph_currency_vs_enemies(self):
        self._apply_style()
        rows     = self._load_csv(self.wave_data_file)
        enemies  = []
        currency = []
        for row in rows:
            try:
                enemies.append(int(row['enemies_killed']))
                currency.append(float(row['currency_earned']))
            except (KeyError, ValueError): pass

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(enemies, currency, color='#e0c052', alpha=0.75, s=60,
                   edgecolors='#a08030', linewidths=0.5)
        ax.set_title('Currency Earned vs Enemies Defeated Per Wave', fontsize=14)
        ax.set_xlabel('Enemies Defeated')
        ax.set_ylabel('Currency Earned ($)')
        ax.grid(alpha=0.4)
        self._save('4.png')

    # --- graph 5: boxplot ---
    def _graph_wave_completion_time(self):
        self._apply_style()
        rows       = self._load_csv(self.wave_data_file)
        wave_times = {}
        for row in rows:
            try:
                w = int(row['wave'])
                t = float(row['completion_time'])
                wave_times.setdefault(w, []).append(t)
            except (KeyError, ValueError): pass

        if wave_times:
            waves = sorted(wave_times.keys())
            data  = [wave_times[w] for w in waves]
        else:
            waves, data = [1], [[0]]

        fig, ax = plt.subplots(figsize=(8, 5))
        bp = ax.boxplot(data, labels=[f'W{w}' for w in waves], patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('#52a0e0')
            patch.set_alpha(0.7)
        for key in ('whiskers', 'caps', 'medians', 'fliers'):
            for item in bp[key]:
                item.set_color('#e0e0e0')

        ax.set_title('Wave Completion Time Distribution', fontsize=14)
        ax.set_xlabel('Wave')
        ax.set_ylabel('Completion Time (seconds)')
        ax.grid(axis='y', alpha=0.4)
        self._save('5.png')