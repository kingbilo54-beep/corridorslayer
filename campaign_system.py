# -*- coding: utf-8 -*-
"""Data catalog for planet and playable-ship campaign tracks.

The catalog deliberately contains no Pygame or save-system dependencies.
Planet IDs match the established sector IDs so existing saves and map links
remain valid. Add new campaign content by adding a profile here.
"""

PLANETS = {
    1: {"id": "earth", "name": "ERDE", "kind": "planet",
        "story": "Heimatwelt der Flotte. Erste Verteidigungslinie gegen die Invasionsflotte.",
        "roster": ("skitter", "lancer", "interceptor", "shard"),
        "arcs": ((1, 4, "VERTEIDIGUNG"), (5, 10, "VORSTOSS"), (11, 14, "GEGENANGRIFF")),
        "bosses": {5: "interceptor", 10: "brute", 15: "dragon"},
        "final_boss": "dragon", "recommended_hull": 1,
        "reward_profile": 1.0},
    2: {"id": "orbital_station", "name": "RAUMSTATION", "kind": "station",
        "story": "Verlassene Orbitalstation. Feindliche Truppen haben die Ringe besetzt.",
        "roster": ("bomber", "frigate", "destroyer", "carrier"),
        "arcs": ((1, 4, "DOCKRINGE"), (5, 10, "REAKTOR"), (11, 14, "KOMMANDODECK")),
        "bosses": {5: "dreadmaw_behemoth", 10: "spire_walker", 15: "astral_centaur"},
        "final_boss": "astral_centaur", "recommended_hull": 2,
        "reward_profile": 1.03},
    3: {"id": "asteroid_belt", "name": "ASTEROIDENGÜRTEL", "kind": "region",
        "story": "Verdeckte Feindbasis zwischen den Felsen. Vorsicht: Hinterhalte.",
        "roster": ("stalker", "medusa", "eye", "crystal"),
        "arcs": ((1, 4, "FELSSCHATTEN"), (5, 10, "MINENFELD"), (11, 14, "FEINDBASIS")),
        "bosses": {5: "shadow_weave", 10: "corrupted_gryphon", 15: "colossal_armadillo"},
        "final_boss": "colossal_armadillo", "recommended_hull": 3,
        "reward_profile": 1.06},
    4: {"id": "mars", "name": "MARS", "kind": "planet",
        "story": "Kolonie-Kaime auf dem roten Planeten. Die Bergungswerke werden angegriffen.",
        "roster": ("husk", "hive", "wraith", "skitter"),
        "arcs": ((1, 4, "KOLONIE"), (5, 10, "BERGUNGSWERKE"), (11, 14, "POLKAPPE")),
        "bosses": {5: "void_lurker", 10: "shadow_weave", 15: "corrupted_gryphon"},
        "final_boss": "corrupted_gryphon", "recommended_hull": 4,
        "reward_profile": 1.09},
    5: {"id": "dark_sector", "name": "DUNKLER SEKTOR", "kind": "region",
        "story": "Quelle der Invasion. Hier steht das Herz der Feindflotte.",
        "roster": ("shard", "wraith", "hive", "destroyer"),
        "arcs": ((1, 4, "RANDZONE"), (5, 10, "SCHLACHTLINIE"), (11, 14, "FLAGGSCHIFF")),
        "bosses": {5: "colossal_armadillo", 10: "obsidian_mantis", 15: "dreadmaw_behemoth"},
        "final_boss": "dreadmaw_behemoth", "recommended_hull": 5,
        "reward_profile": 1.12},
    6: {"id": "rift", "name": "DER RISS", "kind": "rift",
        "story": "Der Sprung durch den Riss ist gelungen. Dahinter koordinierte Flotten.",
        "roster": ("interceptor", "crystal", "wraith", "shard"),
        "arcs": ((1, 4, "RISSRAND"), (5, 10, "GRAVITATIONSSTROM"), (11, 14, "NULLZONE")),
        "bosses": {5: "astral_centaur", 10: "colossal_armadillo", 15: "obsidian_mantis"},
        "final_boss": "obsidian_mantis", "recommended_hull": 7,
        "reward_profile": 1.16},
    7: {"id": "nebula_core", "name": "NEBELKERN", "kind": "nebula",
        "story": "Ein Sternennebel voller Werft-Schleusen. Hier baut der Feind seine Schiffe.",
        "roster": ("carrier", "medusa", "hive", "destroyer"),
        "arcs": ((1, 4, "NEBELFELD"), (5, 10, "WERFTSCHLEUSEN"), (11, 14, "KERNWERFT")),
        "bosses": {5: "dreadmaw_behemoth", 10: "obsidian_mantis", 15: "primordial_serpent"},
        "final_boss": "primordial_serpent", "recommended_hull": 9,
        "reward_profile": 1.20},
    8: {"id": "coreworld", "name": "KERNWELT", "kind": "planet",
        "story": "Das Herz des Feindreichs. Zerschlage den Kern und bring die Flotte nach Hause.",
        "roster": ("eye", "wraith", "husk", "crystal"),
        "arcs": ((1, 4, "AUSSENRING"), (5, 10, "KERNMANTEL"), (11, 14, "KERN")),
        "bosses": {5: "shadow_weave", 10: "spire_walker", 15: "void_lurker"},
        "final_boss": "void_lurker", "recommended_hull": 10,
        "reward_profile": 1.25},
}

# A ship campaign is a challenge overlay on real planet missions. It records
# its own completions without owning or rewriting planet-stage progress.
# Fortress is currently the only player-controlled hull in the runtime.
SHIP_CAMPAIGNS = {
    "fortress": {
        "name": "FORTRESS · BELAGERUNGSKAMPAGNE",
        "trait": "Schwere Hülle: Überleben und kontrollierter Vorstoß",
        "missions": (
            {"id": "earth_guard", "planet": 1, "stage": 5, "hull": 1,
             "title": "ERSTER SCHUTZWALL", "objective": "Elite-Verband auf der Erde abfangen."},
            {"id": "station_breaker", "planet": 2, "stage": 10, "hull": 3,
             "title": "DOCKBRECHER", "objective": "Den Stationskommandanten ausschalten."},
            {"id": "mars_siege", "planet": 4, "stage": 10, "hull": 5,
             "title": "MARS-BELAGERUNG", "objective": "Die Bergungswerke gegen den Elite-Boss halten."},
            {"id": "rift_anchor", "planet": 6, "stage": 15, "hull": 7,
             "title": "ANKER IM RISS", "objective": "Den Riss-Boss im direkten Vorstoß besiegen."},
            {"id": "coreworld_last_stand", "planet": 8, "stage": 15, "hull": 10,
             "title": "LETZTE BASTION", "objective": "Den Kernwelt-Endboss bezwingen."},
        ),
    },
}


def planet_profile(planet_id):
    return PLANETS.get(int(planet_id))


def final_boss_type(planet_id):
    profile = planet_profile(planet_id)
    return profile["final_boss"] if profile else None


def boss_type_for(planet_id, stage_id):
    profile = planet_profile(planet_id)
    return profile.get("bosses", {}).get(int(stage_id)) if profile else None


def ship_profile(ship_id):
    return SHIP_CAMPAIGNS.get(str(ship_id))


def next_ship_mission(progress, ship_id="fortress"):
    profile = ship_profile(ship_id)
    if not profile:
        return None
    completed = set(progress.get(ship_id, ())) if isinstance(progress, dict) else set()
    return next((m for m in profile["missions"] if m["id"] not in completed), None)
