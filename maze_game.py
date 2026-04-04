"""
Maze game: main maze + always-visible side panel (controls, inventory, stats, log).

Default board is 10×10 (100 tiles — treat as ~100 sq ft if 1 tile = 1 foot).

Legend: # wall, floor walkable, P player, E enemies, K keys, C chest, X exit.
Fog of war (BFS vision); explored stays lit; junctions briefly flood-local "rooms";
G = God mode (full map + autopilot to keys & exit). I = inventory (pauses; WASD selects slot). WASD moves when not in god mode and inventory closed.

Requires: pygame
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

try:
    import pygame
except ImportError:
    print("Install pygame:  py -m pip install pygame")
    sys.exit(1)

from maze_core import (
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    MAZE_DIM_MAX,
    MAZE_DIM_MIN,
    SMALL_MAZE_HEIGHT,
    SMALL_MAZE_WIDTH,
    Maze,
    clamp_maze_dimensions,
    find_corner_goal,
    generate_maze_grid,
    neighbors4,
)
import BFS_mazesolving
import DFS_mazesolving
import astar_mazesolving
import maze_battle as mb

Pos = Tuple[int, int]

PANEL_WIDTH = 336
PANEL_MIN_HEIGHT = 520
VISION_DEPTH = 10
ROOM_FLOOD_CAP = 28
KEYS_NEEDED = 2
FPS = 60
MONSTER_MOVE_MS = 520
GOD_AUTOPILOT_STEP_MS = 95
PLAYER_MAX_HP = 100
MONSTER_HIT_DAMAGE = 12
FIST_DAMAGE = 1

# Starter weapons: pick one at game start ([1]–[4])
STARTER_WEAPONS: List[Dict[str, object]] = [
    {"id": "katana", "name": "Katana", "short": "Katana", "dmg": 2, "hint": "Fast cuts"},
    {"id": "broadsword", "name": "Broadsword", "short": "Sword", "dmg": 3, "hint": "Heavy"},
    {"id": "dagger", "name": "Dagger", "short": "Dagger", "dmg": 1, "hint": "Quick"},
    {"id": "staff", "name": "Arcane Staff", "short": "Staff", "dmg": 2, "hint": "Magic"},
]

MONSTER_DEFS: Dict[str, Dict] = {
    "gray": {"max_hp": 1, "color": (152, 158, 170)},
    "blue": {"max_hp": 2, "color": (58, 118, 255)},
    "yellow": {"max_hp": 3, "color": (238, 214, 64)},
    "black": {"max_hp": 4, "color": (28, 30, 34)},
}

SPAWN_COUNTS_SMALL: Tuple[Tuple[str, int], ...] = (
    ("gray", 2),
    ("blue", 1),
    ("yellow", 1),
    ("black", 1),
)
SPAWN_COUNTS_LARGE: Tuple[Tuple[str, int], ...] = (
    ("gray", 2),
    ("blue", 2),
    ("yellow", 2),
    ("black", 2),
)


@dataclass
class Monster:
    row: int
    col: int
    kind: str
    hp: int
    max_hp: int
    color: Tuple[int, int, int]
    move_timer: float = 0.0
    burn_turns: int = 0
    miss_next: bool = False


@dataclass
class Inventory:
    owned_weapon_id: str = ""
    weapon_equipped: bool = True
    potions: int = 2
    buff_charges: int = 1
    keys: int = 0


def weapon_by_id(wid: str) -> Optional[Dict[str, object]]:
    for w in STARTER_WEAPONS:
        if w["id"] == wid:
            return w
    return None


def player_hit_damage(inv: Inventory) -> int:
    if not inv.weapon_equipped or not inv.owned_weapon_id:
        return FIST_DAMAGE
    w = weapon_by_id(inv.owned_weapon_id)
    return int(w["dmg"]) if w else FIST_DAMAGE


def weapon_display_name(inv: Inventory) -> str:
    if not inv.owned_weapon_id:
        return "(none)"
    w = weapon_by_id(inv.owned_weapon_id)
    return str(w["name"]) if w else inv.owned_weapon_id


INV_SLOT_COUNT = 4

def _blit_wrapped(
    surf: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    rect: pygame.Rect,
    color: Tuple[int, int, int],
    line_max: int = 5,
) -> None:
    words = text.replace("\n", " ").split()
    lines: List[str] = []
    cur = ""
    for w in words:
        cand = (cur + " " + w).strip()
        tw = font.render(cand, True, color).get_width()
        if tw <= rect.width - 8:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    y = rect.top + 6
    lh = font.get_linesize()
    for line in lines[:line_max]:
        surf.blit(font.render(line, True, color), (rect.left + 6, y))
        y += lh


def draw_inventory_slots(
    surf: pygame.Surface,
    area: pygame.Rect,
    inv: Inventory,
    body_font: pygame.font.Font,
    selected: int,
) -> None:
    """Horizontal item slots only; `selected` is 0..INV_SLOT_COUNT-1."""
    n = INV_SLOT_COUNT
    selected = max(0, min(n - 1, selected))
    gap = 8
    ox, oy = area.left, area.top
    bar_h = max(80, area.height)
    total_w = max(1, area.width - 8)
    slot_w = max(40, (total_w - gap * (n - 1)) // n)

    labels = [
        "",
        f"Potions\n×{inv.potions}",
        f"Keys\n{inv.keys}/{KEYS_NEEDED}",
        f"Buffs\n×{inv.buff_charges}",
    ]
    wname = weapon_display_name(inv)
    eq = "EQUIPPED" if inv.weapon_equipped else "stowed"
    labels[0] = f"{wname}\n[{eq}]\nDMG {player_hit_damage(inv)}"

    x0 = ox + (area.width - (n * slot_w + gap * (n - 1))) // 2
    for i in range(n):
        x = x0 + i * (slot_w + gap)
        cell = pygame.Rect(x, oy, slot_w, bar_h)
        sel = i == selected
        bg = (58, 62, 78) if sel else (48, 52, 64)
        brd = (255, 210, 90) if sel else (110, 118, 140)
        pygame.draw.rect(surf, bg, cell, border_radius=10)
        pygame.draw.rect(surf, brd, cell, 3 if sel else 2, border_radius=10)
        _blit_wrapped(surf, body_font, labels[i], cell, (220, 224, 235), line_max=5)


def draw_inventory_stats_panel(
    surf: pygame.Surface,
    area: pygame.Rect,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
    *,
    player_hp: int,
    player_max: int,
    player_bleed: int,
    player_stagger: int,
    inv: Inventory,
    keys_needed: int,
    keys_on_map: int,
    god_mode: bool,
    battle_active: bool,
    battle_enemy: str,
    battle_m_hp: int,
    battle_m_max: int,
) -> None:
    """Optional right-hand stats column inside the inventory overlay."""
    pygame.draw.rect(surf, (40, 44, 54), area, border_radius=10)
    pygame.draw.rect(surf, (100, 110, 135), area, 2, border_radius=10)
    x, y = area.left + 10, area.top + 10
    w = area.width - 20
    surf.blit(title_font.render("STATS", True, (220, 200, 140)), (x, y))
    y += title_font.get_linesize() + 8

    draw_bar(surf, x, y, w, 12, player_hp / max(1, player_max), (200, 70, 90))
    y += 18
    surf.blit(body_font.render(f"HP  {player_hp} / {player_max}", True, (230, 230, 235)), (x, y))
    y += body_font.get_linesize() + 6

    st: List[str] = []
    if player_bleed:
        st.append(f"Bleed stacks ~{player_bleed}")
    if player_stagger:
        st.append(f"Stagger turns ~{player_stagger}")
    if not st:
        st.append("Status: OK")
    else:
        st.insert(0, "Status:")
    for s in st:
        surf.blit(body_font.render(s[:44], True, (190, 195, 210)), (x, y))
        y += body_font.get_linesize() + 2
    y += 6

    wn = weapon_display_name(inv)
    eq = "equipped" if inv.weapon_equipped else "stowed"
    surf.blit(body_font.render(f"Weapon: {wn}", True, (210, 215, 225)), (x, y))
    y += body_font.get_linesize()
    surf.blit(
        body_font.render(f"  {eq}  ·  strike dmg {player_hit_damage(inv)}", True, (170, 175, 190)),
        (x, y),
    )
    y += body_font.get_linesize() + 8

    surf.blit(
        body_font.render(
            f"Potions ×{inv.potions}   Buffs ×{inv.buff_charges}",
            True,
            (200, 205, 215),
        ),
        (x, y),
    )
    y += body_font.get_linesize()
    surf.blit(
        body_font.render(
            f"Keys held {inv.keys}/{keys_needed}   K on map: {keys_on_map}",
            True,
            (200, 205, 215),
        ),
        (x, y),
    )
    y += body_font.get_linesize() + 10

    surf.blit(
        body_font.render(
            "God mode: ON" if god_mode else "God mode: off",
            True,
            (255, 220, 120) if god_mode else (140, 145, 160),
        ),
        (x, y),
    )
    y += body_font.get_linesize() + 8

    if battle_active and battle_enemy:
        surf.blit(title_font.render("Combat", True, (255, 180, 160)), (x, y))
        y += title_font.get_linesize() + 4
        draw_bar(surf, x, y, w, 12, battle_m_hp / max(1, battle_m_max), (90, 140, 220))
        y += 18
        surf.blit(
            body_font.render(f"{battle_enemy}  {battle_m_hp}/{battle_m_max}", True, (210, 215, 230)),
            (x, y),
        )


def draw_inventory_footer(
    surf: pygame.Surface,
    area: pygame.Rect,
    title_font: pygame.font.Font,
    *,
    stats_panel_open: bool,
) -> None:
    surf.blit(
        title_font.render(
            "W A S D — slots   Space — use   Tab — "
            + ("hide stats panel" if stats_panel_open else "show stats panel"),
            True,
            (170, 200, 255),
        ),
        (area.left + 6, area.top + 2),
    )
    surf.blit(
        title_font.render(
            "E / U — weapon   1 — potion   I — close",
            True,
            (150, 165, 190),
        ),
        (area.left + 6, area.top + 22),
    )


def draw_weapon_select(
    surf: pygame.Surface,
    area: pygame.Rect,
    title_font: pygame.font.Font,
    body_font: pygame.font.Font,
) -> None:
    overlay = pygame.Surface((area.width, area.height), pygame.SRCALPHA)
    overlay.fill((12, 14, 22, 235))
    surf.blit(overlay, area.topleft)
    t = title_font.render("Choose starting weapon", True, (240, 240, 250))
    surf.blit(t, t.get_rect(center=(area.centerx, area.top + 36)))
    sub = body_font.render("[1]-[4]  —  weapon goes in first inventory slot", True, (160, 170, 190))
    surf.blit(sub, sub.get_rect(center=(area.centerx, area.top + 62)))

    pad = 14
    card_w = (area.width - 3 * pad) // 2
    card_h = 102
    base_y = area.top + 92
    for i, w in enumerate(STARTER_WEAPONS):
        row, col = i // 2, i % 2
        x = area.left + pad + col * (card_w + pad)
        y = base_y + row * (card_h + pad)
        r = pygame.Rect(x, y, card_w, card_h)
        pygame.draw.rect(surf, (48, 52, 64), r, border_radius=12)
        pygame.draw.rect(surf, (130, 140, 170), r, 2, border_radius=12)
        hdr = body_font.render(f"[{i + 1}] {w['short']}", True, (255, 220, 140))
        surf.blit(hdr, (r.left + 10, r.top + 8))
        _blit_wrapped(
            surf,
            body_font,
            f"{w['name']} — {w['hint']} (dmg {w['dmg']})",
            pygame.Rect(r.left + 8, r.top + 30, r.width - 16, r.height - 36),
            (200, 205, 215),
            line_max=3,
        )


def _open_cells(grid: List[List[int]], banned: Sequence[Pos]) -> List[Pos]:
    ban = set(banned)
    out: List[Pos] = []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 0 and (r, c) not in ban:
                out.append((r, c))
    return out


def spawn_monsters(
    grid: List[List[int]],
    rng: random.Random,
    banned: Sequence[Pos],
    spawn_table: Sequence[Tuple[str, int]],
) -> List[Monster]:
    free = _open_cells(grid, banned)
    rng.shuffle(free)
    monsters: List[Monster] = []
    fi = 0
    for kind, count in spawn_table:
        spec = MONSTER_DEFS[kind]
        for _ in range(count):
            if fi >= len(free):
                return monsters
            r, c = free[fi]
            fi += 1
            mh = spec["max_hp"]
            monsters.append(
                Monster(row=r, col=c, kind=kind, hp=mh, max_hp=mh, color=spec["color"])
            )
    return monsters


def monster_at(monsters: List[Monster], pos: Pos) -> Monster | None:
    for m in monsters:
        if m.row == pos[0] and m.col == pos[1]:
            return m
    return None


def cell_occupied_by_monster(monsters: List[Monster], pos: Pos, skip: Monster | None = None) -> bool:
    for m in monsters:
        if m is skip:
            continue
        if m.row == pos[0] and m.col == pos[1]:
            return True
    return False


def bfs_limited(grid: List[List[int]], start: Pos, max_cells: int) -> Set[Pos]:
    q = deque([start])
    seen: Set[Pos] = {start}
    while q and len(seen) < max_cells:
        r, c = q.popleft()
        for nr, nc in neighbors4(grid, r, c):
            if (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append((nr, nc))
                if len(seen) >= max_cells:
                    break
    return seen


def vision_from_player(grid: List[List[int]], start: Pos, max_depth: int) -> Set[Pos]:
    """Lit tiles along open corridors up to max_depth steps from player."""
    q = deque([(start, 0)])
    seen: Set[Pos] = set()
    while q:
        (r, c), d = q.popleft()
        if (r, c) in seen:
            continue
        seen.add((r, c))
        if d >= max_depth:
            continue
        for nr, nc in neighbors4(grid, r, c):
            if (nr, nc) not in seen:
                q.append(((nr, nc), d + 1))
    return seen


def open_degree(grid: List[List[int]], r: int, c: int) -> int:
    return sum(1 for _ in neighbors4(grid, r, c))


def bfs_path_avoiding(
    grid: List[List[int]],
    start: Pos,
    goal: Pos,
    blocked: Set[Pos],
) -> List[Pos] | None:
    """Shortest path on open cells; positions in ``blocked`` are not entered (e.g. monsters)."""
    if start == goal:
        return [start]
    q: deque[Pos] = deque([start])
    parent: Dict[Pos, Pos | None] = {start: None}
    while q:
        r, c = q.popleft()
        if (r, c) == goal:
            out: List[Pos] = []
            cur: Pos | None = (r, c)
            while cur is not None:
                out.append(cur)
                cur = parent[cur]
            out.reverse()
            return out
        for nr, nc in neighbors4(grid, r, c):
            if (nr, nc) in blocked:
                continue
            if (nr, nc) not in parent:
                parent[(nr, nc)] = (r, c)
                q.append((nr, nc))
    return None


def draw_bar(
    surf: pygame.Surface,
    x: int,
    y: int,
    w: int,
    h: int,
    frac: float,
    fill: Tuple[int, int, int],
    bg: Tuple[int, int, int] = (60, 62, 70),
) -> None:
    pygame.draw.rect(surf, bg, pygame.Rect(x, y, w, h), border_radius=3)
    fw = max(0, int(w * max(0.0, min(1.0, frac))))
    if fw > 0:
        pygame.draw.rect(surf, fill, pygame.Rect(x, y, fw, h), border_radius=3)
    pygame.draw.rect(surf, (100, 105, 120), pygame.Rect(x, y, w, h), 1, border_radius=3)


def draw_battle_overlay(
    surf: pygame.Surface,
    font: pygame.font.Font,
    small: pygame.font.Font,
    *,
    player_hp: int,
    player_max: int,
    enemy_name: str,
    enemy_hp: int,
    enemy_max: int,
    phase: str,
    combo_node: mb.AttackNode | None,
    lines: Sequence[str],
) -> None:
    w, h = surf.get_size()
    dim = pygame.Surface((w, h), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 170))
    surf.blit(dim, (0, 0))
    box_w = min(440, w - 24)
    box_h = min(340, h - 24)
    box = pygame.Rect((w - box_w) // 2, (h - box_h) // 2, box_w, box_h)
    pygame.draw.rect(surf, (32, 36, 46), box)
    pygame.draw.rect(surf, (130, 140, 170), box, 2)
    x, y = box.x + 14, box.y + 12
    surf.blit(font.render("COMBAT", True, (240, 200, 120)), (x, y))
    y += 26
    draw_bar(surf, x, y, box.width - 28, 14, player_hp / max(1, player_max), (200, 70, 90))
    y += 18
    surf.blit(small.render(f"You  {player_hp}/{player_max}", True, (220, 222, 228)), (x, y))
    y += 22
    draw_bar(surf, x, y, box.width - 28, 14, enemy_hp / max(1, enemy_max), (90, 140, 220))
    y += 18
    surf.blit(small.render(f"{enemy_name}  {enemy_hp}/{enemy_max}", True, (220, 222, 228)), (x, y))
    y += 22
    if phase == "combo" and combo_node and combo_node.next_attacks:
        surf.blit(small.render("Combo — pick branch:", True, (160, 200, 255)), (x, y))
        y += 18
        for i, ch in enumerate(combo_node.next_attacks[:6], start=1):
            surf.blit(
                small.render(f"  [{i}] {ch.name}  (~{ch.damage} dmg)", True, (195, 198, 210)),
                (x, y),
            )
            y += 16
        y += 4
    else:
        surf.blit(small.render("T = Attack (combo)   H = Defend", True, (180, 185, 200)), (x, y))
        y += 20
    log_top = y
    for ln in list(lines)[-7:]:
        if log_top > box.bottom - 44:
            break
        surf.blit(small.render(ln[:56], True, (200, 202, 212)), (x, log_top))
        log_top += 15
    hint = "Esc quit   F11 fullscreen   R new maze"
    surf.blit(small.render(hint, True, (140, 145, 160)), (x, box.bottom - 28))


def draw_side_panel(
    surf: pygame.Surface,
    rect: pygame.Rect,
    font: pygame.font.Font,
    small: pygame.font.Font,
    *,
    player_hp: int,
    player_max: int,
    player_status: List[str],
    enemy_name: str,
    enemy_hp: int,
    enemy_max: int,
    enemy_status: List[str],
    inv: Inventory,
    keys_needed: int,
    log_lines: List[str],
    god_mode: bool,
    inv_open: bool,
) -> None:
    surf.fill((42, 44, 52), rect)
    pygame.draw.line(surf, (80, 85, 100), (rect.left, rect.top), (rect.left, rect.bottom), 2)

    y = rect.top + 10
    x = rect.left + 10
    w = rect.width - 20

    def header(title: str) -> int:
        nonlocal y
        t = font.render(title, True, (200, 205, 220))
        surf.blit(t, (x, y))
        y += 22
        return y

    def line(s: str, color=(190, 192, 200)) -> None:
        nonlocal y
        for wrap in range(0, len(s), 42):
            chunk = s[wrap : wrap + 42]
            surf.blit(small.render(chunk, True, color), (x, y))
            y += 16
        y += 4

    header("MAZE LEGEND")
    line("# wall  . floor  P you")
    line("E enemy  K key  C chest")
    line("X exit (2 keys)")

    header("CONTROLS")
    line("W A S D — move")
    line("G — God mode (play only)")
    line("I — inventory (pause) Tab stats")
    line("R — New maze  F11 — Fullscreen")
    line("1–4 — BFS / DFS / A* / RRT path")
    line("Esc — Quit")
    if god_mode:
        line("(God mode ON)", (255, 220, 120))

    header("INVENTORY")
    wn = weapon_display_name(inv)
    eq = "equipped" if inv.weapon_equipped else "unequipped"
    line(f"Weapon: {wn} ({eq})  dmg {player_hit_damage(inv)}")
    line(f"Potions x{inv.potions}  Buffs x{inv.buff_charges}")
    line(f"Keys: {inv.keys} / {keys_needed}")
    if inv_open:
        line("Inventory open — paused", (160, 200, 255))

    header("PLAYER STATS")
    draw_bar(surf, x, y, w, 14, player_hp / max(1, player_max), (200, 70, 90))
    y += 18
    line(f"Health: {player_hp}/{player_max}")
    ps = ", ".join(player_status) if player_status else "None"
    line(f"Status: {ps}")

    header("ENEMY (nearest)")
    if enemy_max > 0:
        draw_bar(surf, x, y, w, 14, enemy_hp / max(1, enemy_max), (90, 140, 220))
        y += 18
        line(f"{enemy_name}  {enemy_hp}/{enemy_max}")
        es = ", ".join(enemy_status) if enemy_status else "None"
        line(f"Status: {es}")
    else:
        line("No enemy in sight")

    header("LOG")
    for s in log_lines[-6:]:
        line(s[:48], (170, 175, 190))


def run(
    width: int = SMALL_MAZE_WIDTH,
    height: int = SMALL_MAZE_HEIGHT,
    cell_px: int | None = None,
    seed: int | None = None,
    start_fullscreen: bool = False,
) -> None:
    width, height = clamp_maze_dimensions(width, height)
    rng = random.Random(seed)

    def setup_level() -> Tuple:
        g = generate_maze_grid(width, height, rng=rng)
        mz = Maze(g)
        exit_pos = find_corner_goal(g)
        banned = [(0, 0), exit_pos]
        free = _open_cells(g, banned)
        rng.shuffle(free)
        key_cells: Set[Pos] = set()
        for _ in range(min(KEYS_NEEDED, len(free))):
            if not free:
                break
            key_cells.add(free.pop())
        chest_cells: Set[Pos] = set()
        for _ in range(min(2, len(free))):
            if not free:
                break
            chest_cells.add(free.pop())
        st = SPAWN_COUNTS_SMALL if max(width, height) <= 8 else SPAWN_COUNTS_LARGE
        mon_ban = list(banned) + list(key_cells) + list(chest_cells)
        mons = spawn_monsters(g, rng, banned=mon_ban, spawn_table=st)
        return g, mz, exit_pos, key_cells, chest_cells, mons

    grid, maze, exit_pos, key_cells, chest_cells, monsters = setup_level()
    player = [0, 0]
    explored_open: Set[Pos] = set()
    god_mode = False
    inventory = Inventory(keys=0, owned_weapon_id="", weapon_equipped=True)
    game_phase = "weapon_select"
    message_log: deque[str] = deque(maxlen=10)
    inv_open = False
    inv_selected = 0
    inv_stats_panel_open = False

    player_bleed = 0
    player_stagger = 0
    overlay_path: List[Pos] | None = None
    overlay_name = ""
    player_hp = PLAYER_MAX_HP
    game_over = False
    won = False
    god_autopilot_accum = 0.0

    battle_active = False
    battle_monster: Monster | None = None
    battle_cell: Pos | None = None
    battle_m_hp = 0
    battle_m_max = 0
    battle_phase = "ad"
    battle_combo_node: mb.AttackNode | None = None
    battle_last_player_move: str | None = None
    battle_player_effects: List[Dict[str, object]] = []
    battle_monster_effects: List[Dict[str, object]] = []
    battle_log: deque[str] = deque(maxlen=14)

    def log(msg: str) -> None:
        message_log.append(msg)

    def refresh_visibility(room_flood: bool = False) -> None:
        pr, pc = player[0], player[1]
        if god_mode:
            for r in range(maze.rows):
                for c in range(maze.cols):
                    if grid[r][c] == 0:
                        explored_open.add((r, c))
            return
        explored_open.update(vision_from_player(grid, (pr, pc), VISION_DEPTH))
        if room_flood and open_degree(grid, pr, pc) >= 3:
            explored_open.update(bfs_limited(grid, (pr, pc), ROOM_FLOOD_CAP))
            log("You entered a junction — nearby halls light up.")

    def tile_lit(r: int, c: int) -> bool:
        if god_mode:
            return True
        if (r, c) in explored_open:
            return True
        if grid[r][c] == 1:
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < maze.rows and 0 <= nc < maze.cols and (nr, nc) in explored_open:
                    return True
        return False

    refresh_visibility(room_flood=False)
    log("Choose a weapon [1]-[4], then explore. I = inventory (pause); Tab = optional stats panel.")

    if cell_px is None:
        m = max(width, height)
        if m <= 7:
            cell_px = 48
        elif m <= 12:
            cell_px = 36
        else:
            cell_px = 26

    pygame.init()
    pygame.display.set_caption("Maze — I inventory (pause)  WASD  G god")

    saved_window_cell_px = cell_px
    is_fullscreen = start_fullscreen
    display_w = display_h = 0
    board_px_w = board_px_h = 0
    frame_w = frame_h = 0
    screen: pygame.Surface
    font: pygame.font.Font
    small_font: pygame.font.Font
    panel_font: pygame.font.Font
    panel_small: pygame.font.Font

    def apply_video() -> None:
        nonlocal screen, cell_px, board_px_w, board_px_h, frame_w, frame_h
        nonlocal display_w, display_h, font, small_font, panel_font, panel_small
        panel_w = PANEL_WIDTH
        if is_fullscreen:
            info = pygame.display.Info()
            display_w, display_h = info.current_w, info.current_h
            cell_px = max(
                12,
                min(
                    (display_w - panel_w) // maze.cols,
                    display_h // maze.rows,
                ),
            )
        else:
            cell_px = saved_window_cell_px
            try:
                info = pygame.display.Info()
                avail_w = max(640, info.current_w - 64)
                avail_h = max(480, info.current_h - 100)
            except Exception:
                avail_w, avail_h = 1680, 1050
            max_cw = max(8, (avail_w - panel_w) // max(1, maze.cols))
            max_ch = max(8, avail_h // max(1, maze.rows))
            cell_px = max(8, min(cell_px, max_cw, max_ch))
            board_px_w = maze.cols * cell_px
            board_px_h = maze.rows * cell_px
            frame_w = board_px_w + panel_w
            frame_h = max(board_px_h, PANEL_MIN_HEIGHT)
            display_w, display_h = frame_w, frame_h
            screen = pygame.display.set_mode((frame_w, frame_h))
            fs = max(13, cell_px // 3)
            ss = max(9, cell_px // 5)
            font = pygame.font.SysFont("consolas", fs)
            small_font = pygame.font.SysFont("consolas", ss)
            panel_font = pygame.font.SysFont("consolas", 15)
            panel_small = pygame.font.SysFont("consolas", 13)
            return

        board_px_w = maze.cols * cell_px
        board_px_h = maze.rows * cell_px
        frame_w = board_px_w + panel_w
        frame_h = max(board_px_h, PANEL_MIN_HEIGHT)
        screen = pygame.display.set_mode((display_w, display_h), pygame.FULLSCREEN)
        fs = max(13, cell_px // 3)
        ss = max(9, cell_px // 5)
        font = pygame.font.SysFont("consolas", fs)
        small_font = pygame.font.SysFont("consolas", ss)
        panel_font = pygame.font.SysFont("consolas", 15)
        panel_small = pygame.font.SysFont("consolas", 13)

    apply_video()
    clock = pygame.time.Clock()

    def regen_maze() -> None:
        nonlocal grid, maze, exit_pos, key_cells, chest_cells, monsters
        nonlocal explored_open, player_hp, game_over, won, overlay_path, overlay_name
        nonlocal player_bleed, player_stagger, inventory, inv_open, inv_selected, inv_stats_panel_open
        nonlocal rng
        rng = random.Random()
        grid, maze, exit_pos, key_cells, chest_cells, monsters = setup_level()
        player[:] = [0, 0]
        explored_open.clear()
        inventory = Inventory(
            keys=0,
            owned_weapon_id=inventory.owned_weapon_id,
            weapon_equipped=inventory.weapon_equipped,
            potions=2,
            buff_charges=1,
        )
        inv_open = False
        inv_selected = 0
        inv_stats_panel_open = False
        player_bleed = player_stagger = 0
        overlay_path = None
        overlay_name = ""
        player_hp = PLAYER_MAX_HP
        game_over = won = False
        nonlocal god_autopilot_accum
        god_autopilot_accum = 0.0
        nonlocal battle_active, battle_monster, battle_cell, battle_m_hp, battle_m_max
        nonlocal battle_phase, battle_combo_node, battle_last_player_move
        nonlocal battle_player_effects, battle_monster_effects, battle_log
        battle_active = False
        battle_monster = None
        battle_cell = None
        battle_m_hp = battle_m_max = 0
        battle_phase = "ad"
        battle_combo_node = None
        battle_last_player_move = None
        battle_player_effects = []
        battle_monster_effects = []
        battle_log.clear()
        message_log.clear()
        log("New maze — collect keys (K), reach X with 2 keys.")
        refresh_visibility(False)
        apply_video()

    def compute_path(which: str) -> None:
        nonlocal overlay_path, overlay_name
        overlay_name = which
        here = (player[0], player[1])
        if which == "BFS":
            overlay_path = BFS_mazesolving.solve(grid, here, exit_pos)
        elif which == "DFS":
            overlay_path = DFS_mazesolving.solve(grid, here, exit_pos)
        elif which == "A*":
            overlay_path = astar_mazesolving.solve(grid, here, exit_pos)
        elif which == "RRT":
            import RRT_mazesolving

            overlay_path = RRT_mazesolving.solve_grid(grid, here, exit_pos)
        if overlay_path is None:
            overlay_name += " (no path)"

    def god_autopilot_goal() -> Pos:
        """Route to every key tile on the map first (key_cells), then the exit."""
        here = (player[0], player[1])
        blocked = {(m.row, m.col) for m in monsters}
        if key_cells:
            best_k: Pos | None = None
            best_len = 10**9
            for k in key_cells:
                pth = bfs_path_avoiding(grid, here, k, blocked)
                if pth and len(pth) < best_len:
                    best_len = len(pth)
                    best_k = k
            if best_k is not None:
                return best_k
            for k in key_cells:
                pth = bfs_path_avoiding(grid, here, k, set())
                if pth and len(pth) < best_len:
                    best_len = len(pth)
                    best_k = k
            if best_k is not None:
                return best_k
            return min(key_cells, key=lambda k: abs(k[0] - here[0]) + abs(k[1] - here[1]))
        return exit_pos

    def god_autopilot_step() -> None:
        nonlocal overlay_path, overlay_name
        if game_over or won or not god_mode or inv_open or game_phase != "play" or battle_active:
            return
        goal = god_autopilot_goal()
        blocked = {(m.row, m.col) for m in monsters}
        path = bfs_path_avoiding(grid, (player[0], player[1]), goal, blocked)
        if path is None or len(path) < 2:
            path = bfs_path_avoiding(grid, (player[0], player[1]), goal, set())
        if path and len(path) >= 2:
            overlay_path = path
            overlay_name = "God AI (auto)"
            r0, c0 = path[0]
            r1, c1 = path[1]
            try_move_player(r1 - r0, c1 - c0, god_skip_stagger=True)
        else:
            overlay_path = None

    def run_battle_round(player_ad: str, p_attack: mb.AttackNode | None) -> None:
        nonlocal player_hp, battle_m_hp, game_over, battle_active, battle_monster
        nonlocal battle_last_player_move, battle_phase, battle_combo_node
        m = battle_monster
        if m is None:
            return
        cpu_ad = mb.cpu_move_choice(battle_last_player_move, rng)
        cpu_root = mb.monster_attack_root(m.kind)
        cpu_node: mb.AttackNode | None = None
        if cpu_ad == "attack":
            cpu_node = mb.cpu_choose_attack(cpu_root, rng)
        new_p, new_m, lines = mb.clash_turn(
            player_ad=player_ad,
            player_attack=p_attack,
            cpu_ad=cpu_ad,
            cpu_attack=cpu_node,
            player_hp=player_hp,
            monster_hp=battle_m_hp,
            player_effects=battle_player_effects,
            monster_effects=battle_monster_effects,
            rng=rng,
            easy=True,
            cpu_mult=0.82,
        )
        player_hp = new_p
        battle_m_hp = new_m
        battle_last_player_move = player_ad
        battle_log.extend(lines)
        for ln in lines:
            log(ln)
        if battle_m_hp <= 0:
            tr, tc = battle_cell if battle_cell else (player[0], player[1])
            mk = m.kind
            if m in monsters:
                monsters.remove(m)
            player[0], player[1] = tr, tc
            battle_active = False
            battle_monster = None
            battle_combo_node = None
            battle_phase = "ad"
            log(f"Victory — {mk} defeated!")
            refresh_visibility(open_degree(grid, tr, tc) >= 3)
        elif player_hp <= 0:
            game_over = True
            battle_active = False
            battle_monster = None
            log("GAME OVER")
        else:
            battle_phase = "ad"
            battle_combo_node = None
            battle_log.append("— T Attack  H Defend —")

    def start_battle(m: Monster, tr: int, tc: int) -> None:
        nonlocal battle_active, battle_monster, battle_cell, battle_m_hp, battle_m_max
        nonlocal battle_phase, battle_combo_node, battle_last_player_move
        nonlocal battle_player_effects, battle_monster_effects, battle_log
        battle_active = True
        battle_monster = m
        battle_cell = (tr, tc)
        battle_m_max = mb.battle_hp_for_monster(m.max_hp)
        battle_m_hp = battle_m_max
        battle_phase = "ad"
        battle_combo_node = None
        battle_last_player_move = None
        battle_player_effects = []
        battle_monster_effects = []
        battle_log.clear()
        battle_log.append(f"Battle: {m.kind}!  T = Attack  H = Defend")
        battle_log.append("Attack → combo [1-4] branches; finisher ends combo")
        log(f"Battle started vs {m.kind}.")

    def try_move_player(dr: int, dc: int, *, god_skip_stagger: bool = False) -> None:
        nonlocal player_hp, game_over, won, monsters, player_stagger, player_bleed
        if battle_active or game_over or won or game_phase != "play":
            return
        if player_stagger > 0 and not (god_mode and god_skip_stagger):
            player_stagger -= 1
            log("Stagger — you skip a step!")
            return
        pr, pc = player
        nr, nc = pr + dr, pc + dc
        if not maze.is_free(nr, nc):
            return
        target = (nr, nc)
        m = monster_at(monsters, target)
        if m is not None:
            if god_mode:
                if m.miss_next:
                    m.miss_next = False
                monsters.remove(m)
                player[0], player[1] = nr, nc
                log("God mode — foe cleared (keys/path stay priority).")
                refresh_visibility(open_degree(grid, nr, nc) >= 3)
                return
            start_battle(m, nr, nc)
            return
        player[0], player[1] = nr, nc
        rc = open_degree(grid, nr, nc) >= 3
        if (nr, nc) in key_cells:
            key_cells.remove((nr, nc))
            inventory.keys += 1
            log("You found a Key!")
        if (nr, nc) in chest_cells:
            chest_cells.remove((nr, nc))
            inventory.potions += 1
            log("Chest opened — +1 Potion!")
        if (nr, nc) == exit_pos:
            if inventory.keys >= KEYS_NEEDED:
                won = True
                log("You reached the exit with all keys — YOU WIN!")
            else:
                log(f"Exit locked — need {KEYS_NEEDED} keys ({inventory.keys}/{KEYS_NEEDED}).")
        refresh_visibility(rc)

    def update_monsters(dt_ms: float) -> None:
        nonlocal player_hp, game_over, player_bleed, player_stagger
        if battle_active or game_over or won or game_phase != "play":
            return
        for m in monsters:
            if m.burn_turns > 0:
                m.burn_turns -= 1
                m.hp -= 1
                if m.hp <= 0:
                    log(f"{m.kind} succumbs to Burn!")
                continue
            m.move_timer += dt_ms
            if m.move_timer < MONSTER_MOVE_MS:
                continue
            m.move_timer = 0.0
            opts = list(neighbors4(grid, m.row, m.col))
            if not opts:
                continue
            rng.shuffle(opts)
            for nr, nc in opts:
                if cell_occupied_by_monster(monsters, (nr, nc), skip=m):
                    continue
                if (nr, nc) == (player[0], player[1]):
                    if rng.random() < 0.25:
                        m.miss_next = True
                        log("Enemy used Spin Slash — Miss!")
                    else:
                        player_hp -= MONSTER_HIT_DAMAGE
                        if rng.random() < 0.35:
                            player_bleed += 3
                            log("You triggered Bleed!")
                        if rng.random() < 0.2:
                            player_stagger += 1
                            log("You are Staggered!")
                        if player_hp <= 0:
                            game_over = True
                            log("GAME OVER")
                    break
                m.row, m.col = nr, nc
                break
        monsters[:] = [m for m in monsters if m.hp > 0]
        if player_bleed > 0 and rng.random() < 0.02:
            player_bleed -= 1
            player_hp -= 4
            log("Bleed ticks…")
            if player_hp <= 0:
                game_over = True

    def apply_inventory_slot_action() -> None:
        nonlocal player_hp, player_bleed
        if inv_selected == 0:
            if inventory.owned_weapon_id:
                inventory.weapon_equipped = not inventory.weapon_equipped
                log(
                    "Weapon equipped."
                    if inventory.weapon_equipped
                    else "Weapon unequipped — fists."
                )
            else:
                log("No weapon — choose one at start.")
        elif inv_selected == 1:
            if inventory.potions > 0:
                inventory.potions -= 1
                player_hp = min(PLAYER_MAX_HP, player_hp + 25)
                player_bleed = max(0, player_bleed - 2)
                log("Used Potion — +25 HP, eased Bleed.")
            else:
                log("No potions left.")
        elif inv_selected == 2:
            log(f"Keys: {inventory.keys}/{KEYS_NEEDED} — collect K tiles in the maze.")
        elif inv_selected == 3:
            if inventory.buff_charges > 0:
                inventory.buff_charges -= 1
                log("Buff charge used.")
            else:
                log("No buff charges left.")

    def nearest_monster() -> Monster | None:
        pr, pc = player[0], player[1]
        best: Monster | None = None
        best_d = 10**9
        for m in monsters:
            d = abs(m.row - pr) + abs(m.col - pc)
            if d < best_d:
                best_d = d
                best = m
        return best

    def handle_battle_keydown(event: pygame.event.Event) -> bool:
        nonlocal battle_phase, battle_combo_node
        if not battle_active or game_phase != "play":
            return False
        if inv_open:
            return False
        if event.type != pygame.KEYDOWN:
            return False
        if battle_phase == "ad":
            if event.key == pygame.K_t:
                battle_combo_node = mb.weapon_root(inventory.owned_weapon_id, inventory.weapon_equipped)
                if not battle_combo_node.next_attacks:
                    run_battle_round("attack", battle_combo_node)
                else:
                    battle_phase = "combo"
                    nn = len(battle_combo_node.next_attacks)
                    battle_log.append(f"{battle_combo_node.name} → choose [1-{nn}]")
                return True
            if event.key == pygame.K_h:
                run_battle_round("defend", None)
                return True
            return False
        if battle_phase == "combo":
            node = battle_combo_node
            if node is None:
                battle_phase = "ad"
                return True
            nch = len(node.next_attacks)
            digit_map = {
                pygame.K_1: 0,
                pygame.K_KP1: 0,
                pygame.K_2: 1,
                pygame.K_KP2: 1,
                pygame.K_3: 2,
                pygame.K_KP3: 2,
                pygame.K_4: 3,
                pygame.K_KP4: 3,
            }
            if event.key in digit_map:
                idx = digit_map[event.key]
                if idx < nch:
                    nxt = node.next_attacks[idx]
                    battle_combo_node = nxt
                    battle_log.append(f"> {nxt.name}")
                    if not nxt.next_attacks:
                        run_battle_round("attack", nxt)
                    return True
            if event.key == pygame.K_SPACE and not node.next_attacks:
                run_battle_round("attack", node)
                return True
            return False
        return False

    running = True
    while running:
        dt_ms = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if handle_battle_keydown(event):
                    continue
                if event.key == pygame.K_i and game_phase == "play":
                    inv_open = not inv_open
                    if inv_open:
                        inv_selected = 0
                    else:
                        inv_stats_panel_open = False
                    log("Inventory open — game paused." if inv_open else "Inventory closed — game resumes.")
                    continue
                if battle_active and game_phase == "play" and not inv_open:
                    if event.key not in (pygame.K_ESCAPE, pygame.K_F11, pygame.K_r):
                        continue
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F11:
                    if not is_fullscreen:
                        saved_window_cell_px = cell_px
                    is_fullscreen = not is_fullscreen
                    apply_video()
                elif event.key == pygame.K_g and game_phase == "play":
                    god_mode = not god_mode
                    god_autopilot_accum = 0.0
                    if god_mode:
                        log("God mode ON — autopilot visits every key, then exit.")
                    else:
                        log("God mode OFF — autopilot stopped.")
                    refresh_visibility(False)
                elif game_phase == "weapon_select":
                    key_to_i = {
                        pygame.K_1: 0,
                        pygame.K_KP1: 0,
                        pygame.K_2: 1,
                        pygame.K_KP2: 1,
                        pygame.K_3: 2,
                        pygame.K_KP3: 2,
                        pygame.K_4: 3,
                        pygame.K_KP4: 3,
                    }
                    if event.key in key_to_i:
                        choice = key_to_i[event.key]
                        w = STARTER_WEAPONS[choice]
                        inventory.owned_weapon_id = str(w["id"])
                        inventory.weapon_equipped = True
                        game_phase = "play"
                        log(f"Starter weapon: {w['name']} — I opens inventory (paused).")
                        refresh_visibility(False)
                elif game_phase == "play" and inv_open and event.key == pygame.K_TAB:
                    inv_stats_panel_open = not inv_stats_panel_open
                    log("Stats panel on." if inv_stats_panel_open else "Stats panel off.")
                elif game_phase == "play" and inv_open and event.key in (
                    pygame.K_a,
                    pygame.K_LEFT,
                    pygame.K_w,
                ):
                    inv_selected = (inv_selected - 1) % INV_SLOT_COUNT
                elif game_phase == "play" and inv_open and event.key in (
                    pygame.K_d,
                    pygame.K_RIGHT,
                    pygame.K_s,
                ):
                    inv_selected = (inv_selected + 1) % INV_SLOT_COUNT
                elif game_phase == "play" and inv_open and event.key in (
                    pygame.K_SPACE,
                    pygame.K_RETURN,
                ):
                    apply_inventory_slot_action()
                elif game_phase == "play" and inv_open and event.key == pygame.K_e:
                    if inventory.owned_weapon_id:
                        inventory.weapon_equipped = True
                        log("Weapon equipped.")
                elif game_phase == "play" and inv_open and event.key == pygame.K_u:
                    inventory.weapon_equipped = False
                    log("Weapon unequipped — fighting with fists.")
                elif game_phase == "play" and inv_open and event.key in (pygame.K_1, pygame.K_KP1):
                    if inventory.potions > 0:
                        inventory.potions -= 1
                        player_hp = min(PLAYER_MAX_HP, player_hp + 25)
                        player_bleed = max(0, player_bleed - 2)
                        log("Used Potion — +25 HP, eased Bleed.")
                    else:
                        log("No potions left.")
                elif event.key == pygame.K_r:
                    regen_maze()
                elif game_phase == "play" and not inv_open and event.key in (pygame.K_1, pygame.K_KP1):
                    compute_path("BFS")
                elif game_phase == "play" and not inv_open and event.key in (pygame.K_2, pygame.K_KP2):
                    compute_path("DFS")
                elif game_phase == "play" and not inv_open and event.key in (pygame.K_3, pygame.K_KP3):
                    compute_path("A*")
                elif game_phase == "play" and not inv_open and event.key in (pygame.K_4, pygame.K_KP4):
                    compute_path("RRT")
                elif game_phase == "play" and not god_mode:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        try_move_player(-1, 0)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        try_move_player(1, 0)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        try_move_player(0, -1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        try_move_player(0, 1)

        if not inv_open:
            update_monsters(dt_ms)

        if (
            god_mode
            and game_phase == "play"
            and not inv_open
            and not battle_active
            and not game_over
            and not won
        ):
            god_autopilot_accum += dt_ms
            while god_autopilot_accum >= GOD_AUTOPILOT_STEP_MS:
                god_autopilot_accum -= GOD_AUTOPILOT_STEP_MS
                god_autopilot_step()

        composite = pygame.Surface((frame_w, frame_h))
        composite.fill((24, 26, 32))
        board_y = (frame_h - board_px_h) // 2
        board = pygame.Surface((board_px_w, board_px_h))
        board.fill((28, 30, 38))
        cp = cell_px
        fog_cell = pygame.Surface((cp, cp), pygame.SRCALPHA)
        fog_cell.fill((0, 0, 0, 210))

        for r in range(maze.rows):
            for c in range(maze.cols):
                rect = pygame.Rect(c * cp, r * cp, cp, cp)
                if grid[r][c] == 1:
                    pygame.draw.rect(board, (48, 52, 62), rect)
                    lbl = small_font.render("#", True, (90, 95, 110))
                    board.blit(lbl, (c * cp + 3, r * cp + 2))
                else:
                    pygame.draw.rect(board, (72, 76, 88), rect, 1)
                    if (r, c) == exit_pos:
                        pygame.draw.rect(
                            board,
                            (60, 200, 120),
                            pygame.Rect(c * cp + 4, r * cp + 4, cp - 8, cp - 8),
                            border_radius=3,
                        )
                        board.blit(small_font.render("X", True, (20, 80, 40)), (c * cp + cp // 3, r * cp + cp // 4))
                    elif (r, c) in key_cells:
                        board.blit(small_font.render("K", True, (255, 230, 120)), (c * cp + cp // 4, r * cp + cp // 4))
                    elif (r, c) in chest_cells:
                        board.blit(small_font.render("C", True, (200, 160, 90)), (c * cp + cp // 4, r * cp + cp // 4))

                if not tile_lit(r, c):
                    board.blit(fog_cell, (c * cp, r * cp))

        if overlay_path and (god_mode or any(tile_lit(pr, pc) for pr, pc in overlay_path)):
            for i, (r, c) in enumerate(overlay_path):
                if not tile_lit(r, c):
                    continue
                center = (c * cp + cp // 2, r * cp + cp // 2)
                pygame.draw.circle(board, (140, 100, 255) if i == 0 else (100, 140, 255), center, max(2, cp // 8))

        rad = max(4, cp // 3)
        for m in monsters:
            vis = tile_lit(m.row, m.col)
            if not vis:
                continue
            cx = m.col * cp + cp // 2
            cy = m.row * cp + cp // 2
            mr = rad // 2 + 1
            if m.kind == "black":
                pygame.draw.circle(board, (200, 200, 210), (cx, cy), mr + 2, 2)
            pygame.draw.circle(board, m.color, (cx, cy), mr)
            board.blit(small_font.render("E", True, (255, 255, 255)), (cx - 4, cy - 6))

        pr, pc = player
        pygame.draw.circle(
            board,
            (255, 85, 85),
            (pc * cp + cp // 2, pr * cp + cp // 2),
            rad,
        )
        board.blit(small_font.render("P", True, (40, 0, 0)), (pc * cp + cp // 3, pr * cp + cp // 5))

        composite.blit(board, (0, board_y))
        panel_rect = pygame.Rect(board_px_w, 0, PANEL_WIDTH, frame_h)
        nm = nearest_monster()
        en_hp = en_mx = 0
        en_name = ""
        en_stat: List[str] = []
        if battle_active and battle_monster is not None:
            en_hp, en_mx = battle_m_hp, battle_m_max
            en_name = battle_monster.kind.capitalize()
        elif nm:
            en_hp, en_mx = nm.hp, nm.max_hp
            en_name = nm.kind.capitalize()
            if nm.burn_turns:
                en_stat.append("Burn")
            if nm.miss_next:
                en_stat.append("Miss")

        pl_stat: List[str] = []
        if player_bleed:
            pl_stat.append("Bleed")
        if player_stagger:
            pl_stat.append("Stagger")

        draw_side_panel(
            composite,
            panel_rect,
            panel_font,
            panel_small,
            player_hp=player_hp,
            player_max=PLAYER_MAX_HP,
            player_status=pl_stat,
            enemy_name=en_name,
            enemy_hp=en_hp,
            enemy_max=en_mx,
            enemy_status=en_stat,
            inv=inventory,
            keys_needed=KEYS_NEEDED,
            log_lines=list(message_log),
            god_mode=god_mode,
            inv_open=inv_open,
        )

        if game_phase == "weapon_select":
            draw_weapon_select(composite, pygame.Rect(0, 0, frame_w, frame_h), font, small_font)

        if battle_active and battle_monster is not None and game_phase == "play":
            draw_battle_overlay(
                composite,
                font,
                small_font,
                player_hp=player_hp,
                player_max=PLAYER_MAX_HP,
                enemy_name=battle_monster.kind.capitalize(),
                enemy_hp=battle_m_hp,
                enemy_max=battle_m_max,
                phase=battle_phase,
                combo_node=battle_combo_node,
                lines=battle_log,
            )

        if inv_open and game_phase == "play":
            ov = pygame.Surface((board_px_w, board_px_h), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 150))
            composite.blit(ov, (0, board_y))
            inv_rect = pygame.Rect(12, board_y + 8, board_px_w - 24, board_px_h - 16)
            title_h = font.get_linesize() + 10
            foot_h = 48
            body = pygame.Rect(
                inv_rect.left,
                inv_rect.top + title_h,
                inv_rect.width,
                max(80, inv_rect.height - title_h - foot_h),
            )
            foot = pygame.Rect(inv_rect.left, inv_rect.bottom - foot_h, inv_rect.width, foot_h)
            tab_hint = "Tab — hide stats" if inv_stats_panel_open else "Tab — stats panel"
            composite.blit(
                font.render(f"INVENTORY  (paused)   {tab_hint}", True, (240, 230, 200)),
                (inv_rect.left + 6, inv_rect.top + 4),
            )
            if inv_stats_panel_open:
                split = body.width // 2 - 8
                left = pygame.Rect(body.left, body.top, max(120, split), body.height)
                right = pygame.Rect(
                    body.left + split + 16,
                    body.top,
                    max(120, body.width - split - 16),
                    body.height,
                )
                draw_inventory_slots(composite, left, inventory, small_font, inv_selected)
                ben = battle_monster.kind.capitalize() if battle_monster else ""
                draw_inventory_stats_panel(
                    composite,
                    right,
                    font,
                    small_font,
                    player_hp=player_hp,
                    player_max=PLAYER_MAX_HP,
                    player_bleed=player_bleed,
                    player_stagger=player_stagger,
                    inv=inventory,
                    keys_needed=KEYS_NEEDED,
                    keys_on_map=len(key_cells),
                    god_mode=god_mode,
                    battle_active=battle_active,
                    battle_enemy=ben,
                    battle_m_hp=battle_m_hp,
                    battle_m_max=battle_m_max,
                )
            else:
                draw_inventory_slots(composite, body, inventory, small_font, inv_selected)
            draw_inventory_footer(composite, foot, small_font, stats_panel_open=inv_stats_panel_open)

        if is_fullscreen:
            screen.fill((0, 0, 0))
            ox = (display_w - frame_w) // 2
            oy = (display_h - frame_h) // 2
            screen.blit(composite, (ox, oy))
        else:
            screen.blit(composite, (0, 0))

        pygame.display.flip()

    pygame.quit()


def _resolved_maze_size(
    size: str,
    cols: int | None,
    rows: int | None,
) -> Tuple[int, int]:
    """Preset from --size, overridden by any --cols / --rows you pass."""
    if size == "small":
        bw, bh = SMALL_MAZE_WIDTH, SMALL_MAZE_HEIGHT
    else:
        bw, bh = DEFAULT_WIDTH, DEFAULT_HEIGHT
    w = cols if cols is not None else bw
    h = rows if rows is not None else bh
    return clamp_maze_dimensions(w, h)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Maze + side panel + fog of war.",
        epilog=(
            "Examples:  %(prog)s --size large --cols 80 --rows 50\n"
            f"  Custom sizes are clamped to {MAZE_DIM_MIN}…{MAZE_DIM_MAX} per side. "
            "Windowed mode shrinks tiles to fit your monitor; use --fullscreen for huge mazes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--size",
        choices=("small", "large"),
        default="small",
        help="Preset: small = 10×10; large = 20×6 unless --cols/--rows override.",
    )
    ap.add_argument(
        "--cols",
        type=int,
        default=None,
        metavar="N",
        help=f"maze width in cells (columns); default from --size (max {MAZE_DIM_MAX}).",
    )
    ap.add_argument(
        "--rows",
        type=int,
        default=None,
        metavar="N",
        help=f"maze height in cells (rows); default from --size (max {MAZE_DIM_MAX}).",
    )
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--fullscreen", action="store_true")
    args = ap.parse_args()
    mw, mh = _resolved_maze_size(args.size, args.cols, args.rows)
    run(width=mw, height=mh, seed=args.seed, start_fullscreen=args.fullscreen)
