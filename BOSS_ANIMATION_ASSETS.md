# Boss animation asset requirements

The runtime selects animations from combat states. Missing states fall back to
the existing idle animation; it does not synthesize replacement sprite art.
Frames are loaded from
`enemys/enemy_<boss>/<state>/enemy_<boss>_<state>_<index>.png`, with indices
starting at `0`. Sprite sheets are also accepted by the existing sheet loader.
The loader crops a whole sequence against one shared alpha bound so anchors do
not move from frame to frame. Non-idle states are scaled to the visible idle
height. Keep all frames transparent, in the same facing/perspective, and
aligned to a stable body anchor.

Use the 8 FPS runtime cadence as the authoring target. Recommended frame counts
are 8 for looping idle, 4 for anticipation, 6 for attack, 2 for impact, 4 for
recovery, and 3 for hurt. Death is optional and should be a one-shot. Match
durations to the combat attack configuration; the frame counts are guidelines,
not permission to alter projectile timing. Canvas dimensions may vary by boss
and state; do not crop attack reach at the canvas edge.

For attack-specific poses, use the combat attack key as a state suffix. For
example, `attack_starfall_fan` is resolved before the generic `attack` state.
The folders and filename stems follow the same naming pattern as other states.

## Required animation sequences

All ten listed bosses currently have only an 8-frame idle sheet. Every
anticipation, attack, impact, recovery, and hurt sequence below still needs
graphics. Existing combat projectile behavior already uses these attack keys.

| Boss ID | Attack-specific sequence keys |
|---|---|
| `astral_centaur` | `astral_lances`, `starfall_fan` |
| `colossal_armadillo` | `rolling_shells`, `shell_burst` |
| `corrupted_gryphon` | `talon_dive`, `wing_sweep` |
| `dreadmaw_behemoth` | `maw_barrage`, `shock_ring` |
| `obsidian_mantis` | `cross_lasers`, `scissor_shards` |
| `primordial_serpent` | `serpent_wave`, `coil_orbs` |
| `shadow_weave` | `web_spiral`, `void_mines` |
| `spire_walker` | `pillar_laser`, `spire_shards` |
| `void_lurker` | `seeking_void`, `eclipse_burst` |
| `lich_dragon` | phase appearance for the Void Lurker; its attack pose sequences are not present |

For each attack key, produce the keyed anticipation, attack, impact, and
recovery sequence. Generic state sequences can be shared only where the
existing art genuinely supports both attacks. Add a hurt sequence per boss.

## Existing Dragon asset gaps

The dragon has idle, breath attack, attack2, and hurt material. No `attack3`
sheet exists. Until one is authored, the ice-spike attack uses the existing
spike-lane telegraph and keeps the dragon's animated idle visible. This is a
clearly documented temporary fallback, not an attack-body animation.

