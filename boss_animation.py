"""Combat-driven animation state selection for boss sprites.

This module deliberately contains no rendering or gameplay rules.  The combat
simulation owns the clock; renderers consume the state and elapsed time it
publishes here.  Missing art is reported to the renderer as a state to fall
back from, never synthesized into fake sprite frames.
"""

from __future__ import annotations


ANIMATION_STATES = (
    "idle", "anticipation", "attack", "impact", "recovery", "hurt", "death",
)

_BOSS_PHASE_STATE = {
    "rest": "idle",
    "telegraph": "anticipation",
    "fire": "attack",
    "recovery": "recovery",
}


def set_animation_state(enemy, state: str) -> None:
    """Change state without restarting an animation that is already active."""
    if state not in ANIMATION_STATES:
        state = "idle"
    if getattr(enemy, "boss_anim_state", "idle") != state:
        enemy.boss_anim_state = state
        enemy.boss_anim_elapsed = 0.0


def advance_boss_animation(enemy, dt: float) -> str:
    """Advance one combat-owned tick and derive the boss's visual state.

    Call only while combat advances.  Pausing the game therefore pauses this
    clock as well.  Gameplay attack timing remains owned by PvECombat.
    """
    dt = max(0.0, float(dt))
    enemy.boss_anim_elapsed = max(
        0.0, float(getattr(enemy, "boss_anim_elapsed", 0.0)) + dt
    )

    # A short impact window is set at projectile release.  It is subordinate
    # to a fresh hurt reaction and does not alter projectile or damage timing.
    if getattr(enemy, "hurt_t", 0.0) > 0.0:
        desired = "hurt"
    elif getattr(enemy, "boss_anim_attack_t", 0.0) > 0.0:
        enemy.boss_anim_attack_t = max(
            0.0, enemy.boss_anim_attack_t - dt
        )
        if enemy.boss_anim_attack_t == 0.0:
            enemy.boss_anim_impact_t = max(
                float(getattr(enemy, "boss_anim_impact_t", 0.0)), 0.12
            )
        desired = "attack"
    elif getattr(enemy, "boss_anim_impact_t", 0.0) > 0.0:
        enemy.boss_anim_impact_t = max(0.0, enemy.boss_anim_impact_t - dt)
        desired = "impact" if enemy.boss_anim_impact_t > 0.0 else None
    else:
        desired = None

    if desired is None:
        if getattr(enemy, "enemy_type", "") == "dragon":
            if getattr(enemy, "breath_phase", 0) == 1:
                desired = "anticipation"
            elif getattr(enemy, "breath_phase", 0) == 2:
                desired = "attack"
            elif getattr(enemy, "atk_kind", 0) in (2, 3):
                desired = "anticipation" if getattr(enemy, "atk_t", 0.0) > 0 else "attack"
            else:
                desired = "idle"
        else:
            desired = _BOSS_PHASE_STATE.get(
                getattr(enemy, "boss_attack_phase", "rest"), "idle"
            )
    set_animation_state(enemy, desired)
    return enemy.boss_anim_state

