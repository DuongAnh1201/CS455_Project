"""
Turn-based attack trees + attack/defend clash (from class project, pygame-ready).
No terminal input — maze_game drives keys and calls resolve_turn.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

Effect = Dict[str, Any]


@dataclass
class AttackNode:
    name: str
    damage: int
    next_attacks: List[AttackNode] = field(default_factory=list)
    effect: Optional[Effect] = None


def cpu_choose_attack(node: AttackNode, rng: random.Random) -> AttackNode:
    cur = node
    while cur.next_attacks and rng.random() < 0.55:
        cur = rng.choice(cur.next_attacks)
    return cur


def cpu_move_choice(last_player_move: Optional[str], rng: random.Random) -> str:
    if last_player_move == "attack":
        return rng.choices(["defend", "attack"], weights=[0.65, 0.35])[0]
    if last_player_move == "defend":
        return rng.choices(["attack", "defend"], weights=[0.65, 0.35])[0]
    return rng.choice(["attack", "defend"])


def apply_effects(
    effects_list: List[Effect],
    target_health: int,
    source_name: str,
    rng: random.Random,
    easy: bool = False,
) -> Tuple[int, bool, List[str]]:
    skip_turn = False
    msgs: List[str] = []
    chance_mod = 0.55 if easy else 1.0
    for effect in effects_list[:]:
        if rng.random() < chance_mod * float(effect.get("chance", 0)):
            en = effect.get("name")
            if en == "bleed":
                target_health -= 3
                msgs.append(f"{source_name}: Bleed (-3)")
            elif en == "stagger":
                skip_turn = True
                msgs.append(f"{source_name}: Stagger — skip attack!")
            elif en == "miss":
                msgs.append(f"{source_name}: Miss effect active")
            elif en == "burn":
                target_health -= 5
                msgs.append(f"{source_name}: Burn (-5)")
            elif en == "weaken":
                msgs.append(f"{source_name}: Weakened")
        effect["duration"] = int(effect.get("duration", 1)) - 1
        if effect["duration"] <= 0:
            effects_list.remove(effect)
    return target_health, skip_turn, msgs


def has_miss_effect(effects: List[Effect]) -> bool:
    return any(e.get("name") == "miss" for e in effects)


def maybe_apply_node_effect(
    node: AttackNode,
    target_effects: List[Effect],
    rng: random.Random,
) -> Optional[str]:
    if not node.effect:
        return None
    eff = node.effect
    if rng.random() < float(eff.get("chance", 0)):
        target_effects.append(
            {
                "name": eff["name"],
                "chance": float(eff.get("chance", 0.2)),
                "duration": int(eff.get("duration", 1)),
            }
        )
        return eff["name"]
    return None


# ---- Weapon trees (class project + dagger/staff) ----

def katana_tree() -> AttackNode:
    return AttackNode(
        "Quick Slash",
        8,
        [
            AttackNode(
                "Piercing Thrust",
                12,
                [AttackNode("Fatal Finish", 20)],
            ),
            AttackNode(
                "Swift Kick",
                5,
                effect={"name": "miss", "chance": 0.25, "duration": 1},
            ),
        ],
        effect={"name": "bleed", "chance": 0.1, "duration": 3},
    )


def broadsword_tree() -> AttackNode:
    return AttackNode(
        "Heavy Swing",
        12,
        [
            AttackNode(
                "Shield Bash",
                10,
                effect={"name": "miss", "chance": 0.15, "duration": 1},
            ),
            AttackNode(
                "Crushing Blow",
                15,
                [AttackNode("Armor Break", 25)],
                effect={"name": "stagger", "chance": 0.1, "duration": 1},
            ),
        ],
    )


def dagger_tree() -> AttackNode:
    return AttackNode(
        "Quick Stab",
        6,
        [
            AttackNode("Double Tap", 9, [AttackNode("Throat Cut", 14)]),
            AttackNode("Feint", 4, effect={"name": "miss", "chance": 0.2, "duration": 1}),
        ],
        effect={"name": "bleed", "chance": 0.15, "duration": 2},
    )


def staff_tree() -> AttackNode:
    return AttackNode(
        "Arc Bolt",
        7,
        [
            AttackNode(
                "Fire Pulse",
                11,
                [AttackNode("Meteor Tap", 18)],
                effect={"name": "burn", "chance": 0.12, "duration": 2},
            ),
            AttackNode("Weaken Hex", 5, effect={"name": "weaken", "chance": 0.3, "duration": 2}),
        ],
    )


def fist_tree_player() -> AttackNode:
    return AttackNode(
        "Punch",
        4,
        [
            AttackNode("Jab", 6, [AttackNode("Uppercut", 10)]),
            AttackNode("Kick", 5),
        ],
    )


def weapon_root(weapon_id: str, equipped: bool) -> AttackNode:
    if not equipped:
        return fist_tree_player()
    return {
        "katana": katana_tree,
        "broadsword": broadsword_tree,
        "dagger": dagger_tree,
        "staff": staff_tree,
    }.get(weapon_id, fist_tree_player)()


# ---- Monster move trees (CPU) ----

def cpu_fist_tree() -> AttackNode:
    return AttackNode(
        "Feint Strike",
        6,
        [
            AttackNode(
                "Counter Jab",
                10,
                [AttackNode("Vicious Uppercut", 18)],
            ),
            AttackNode("Spin Slash", 12, effect={"name": "miss", "chance": 0.2, "duration": 1}),
        ],
    )


def cpu_axe_tree() -> AttackNode:
    return AttackNode(
        "Chop",
        10,
        [
            AttackNode(
                "Overhead Smash",
                14,
                [AttackNode("Decapitate", 25)],
            ),
            AttackNode("Leg Sweep", 6, effect={"name": "stagger", "chance": 0.12, "duration": 1}),
        ],
    )


def cpu_brute_tree() -> AttackNode:
    return AttackNode(
        "Slam",
        14,
        [
            AttackNode("Ground Pound", 18, [AttackNode("Execute", 22)]),
            AttackNode("Roar", 4, effect={"name": "weaken", "chance": 0.25, "duration": 2}),
        ],
    )


def monster_attack_root(kind: str) -> AttackNode:
    return {
        "gray": cpu_fist_tree,
        "blue": cpu_axe_tree,
        "yellow": cpu_fist_tree,
        "black": cpu_brute_tree,
    }.get(kind, cpu_fist_tree)()


# ---- One clash (mirrors class project main loop body) ----

def clash_turn(
    *,
    player_ad: str,
    player_attack: Optional[AttackNode],
    cpu_ad: str,
    cpu_attack: Optional[AttackNode],
    player_hp: int,
    monster_hp: int,
    player_effects: List[Effect],
    monster_effects: List[Effect],
    rng: random.Random,
    easy: bool,
    cpu_mult: float,
) -> Tuple[int, int, List[str]]:
    """Returns new player_hp, monster_hp, log lines."""
    lines: List[str] = []
    player_skip = False
    cpu_skip = False

    player_hp, ps, m1 = apply_effects(player_effects, player_hp, "You", rng, easy)
    lines.extend(m1)
    if ps:
        player_skip = True
    monster_hp, ms, m2 = apply_effects(monster_effects, monster_hp, "Enemy", rng, easy)
    lines.extend(m2)
    if ms:
        cpu_skip = True

    cpu_missed = has_miss_effect(monster_effects)
    player_missed = has_miss_effect(player_effects)

    if player_skip:
        lines.append("You are staggered — you lose this action!")
        if cpu_ad == "attack" and not cpu_skip and cpu_attack is not None:
            tr2 = maybe_apply_node_effect(cpu_attack, player_effects, rng)
            if tr2:
                lines.append(f"Enemy {cpu_attack.name} applies {tr2}!")
            if not player_missed:
                dmg = max(1, int(cpu_attack.damage * cpu_mult))
                player_hp -= dmg
                lines.append(f"Enemy {cpu_attack.name}! You took {dmg}.")
            else:
                lines.append("Enemy whiffs!")
        return player_hp, monster_hp, lines

    if player_ad == "attack" and not player_skip and player_attack is not None:
        tr = maybe_apply_node_effect(player_attack, monster_effects, rng)
        if tr:
            lines.append(f"Your {player_attack.name} applies {tr} on enemy!")

        if cpu_ad == "attack" and not cpu_skip and cpu_attack is not None:
            tr2 = maybe_apply_node_effect(cpu_attack, player_effects, rng)
            if tr2:
                lines.append(f"Enemy {cpu_attack.name} applies {tr2} on you!")

            if not player_missed:
                dmg = max(1, int(cpu_attack.damage * cpu_mult))
                player_hp -= dmg
                lines.append(f"Enemy {cpu_attack.name}! You took {dmg}.")
            else:
                lines.append("Enemy attack missed you!")

            if not cpu_missed:
                pdmg = max(1, int(player_attack.damage * (0.85 if easy else 1.0)))
                monster_hp -= pdmg
                lines.append(f"You used {player_attack.name}! Enemy took {pdmg}.")
            else:
                lines.append("Your attack missed!")

        elif cpu_ad == "defend":
            base = int(player_attack.damage * (0.45 if easy else 0.25))
            if cpu_missed:
                base = player_attack.damage
            pdmg = max(1, base)
            monster_hp -= pdmg
            lines.append(f"You used {player_attack.name}! Enemy blocked — took {pdmg}.")

    elif player_ad == "defend":
        if cpu_ad == "attack" and not cpu_skip and cpu_attack is not None:
            maybe_apply_node_effect(cpu_attack, player_effects, rng)
            base = 5 if easy else 8
            if player_missed:
                base = 0
            dmg = max(0, int(base * cpu_mult))
            player_hp -= dmg
            lines.append(f"You defended. Enemy struck for {dmg}.")
        else:
            lines.append("Both cautious — little happened.")

    return player_hp, monster_hp, lines


def battle_hp_for_monster(max_hp: int) -> int:
    return 55 + max_hp * 28
