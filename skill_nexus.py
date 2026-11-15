# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | SKILL-NEXUS v6 - ORBITAL ENERGY LATTICE
============================================================
Komplett neues visuelles Konzept (Paket 6). Keine vier geraden Arme mehr,
sondern ein organisches, asymmetrisches Energie-Netzwerk:

  - Vier Sparten winden sich als Bezier-Energieadern vom NEXUS-KERN in
    unterschiedliche Richtungen - jede mit eigenem Schwung und eigener
    Farbidentitaet (Waffen=Magenta, Verteidigung=Cyan, Energie=Amber,
    Spezial=Violett; Farben kommen unveraendert aus skill_tree.py).
  - Knoten haben tier-abhaengige Groessen (Kronen-Knoten am Ende jedes
    Pfades) und individuelle Vektor-Symbole.
  - Aktive Verbindungen tragen wandernde Energiestrome (additive Glueh-
    Punkte entlang gekruemmter Polylinien). Gekaufte Knoten leuchten
    dauerhaft, freischaltbare pulsieren, gesperrte bleiben bewusst
    unvollstaendig enthuellt (Nebel des Krieges, gestrichelter Ring,
    Schloss-Symbol, kein Name).
  - Hintergrund: skill_tree_bg.jpg wird cover-skalierd, abgedunkelt und
    mit Vignette als EIN gecachtes Surface pro Bildschirmgroesse
    ausgegeben (1 Blit/Frame). Ohne Bild: prozedurales Nebel-Fallback.
  - Info-Sheet: Landscape = einklappendes Panel rechts, Portrait = Band
    unten. Slide-In-Animation, grosser TRAIN-Button.

Unveraendert gegenueber Paket 5 (API-Vertrag mit main.py):
  compute/hit/fire/select/draw, hitmap, nodes, core, selected,
  train_rect, close_rect, bursts. Daten, Voraussetzungen, Kosten und
  Speicherstaende kommen weiterhin ausschliesslich aus skill_tree.py.
"""
import math
import random
import pygame
import ui_kit
from ui_kit import (u, F, text, neon_text, panel, draw_btn, Btn, wrap_text,
                    radial_glow, VOID, LINE, DIM, MUTED, WHITE, GREEN, RED,
                    AMBER, CYAN, CYAN_SOFT)

# ---------------- Topologie (PAKET 7B: datengetrieben) ----------------
# Die Layout-Positionen werden nicht mehr handgesetz vorgegeben, sondern aus
# dem Skill-Baum in skill_tree.py abgeleitet: Jede Sparte strahlt als Ader-
# bueschel vom NEXUS-KERN aus, Tier-Stufen werden aus den "reqs"-Kanten
# berechnet, Geschwisterknoten faechern auf. Verbindungen = echte
# Voraussetzungs-Kanten (Kern->Wurzel, Parent->Kind).
CORE_UV = (0.0, 0.0)            # Kern sitzt in der Flachenmitte
TIER_SCALE = (0.85, 1.00, 1.12, 1.30)         # Knotenradius je Tier

GLYPH = {
    "waffen_dmg": "burst", "waffen_rate": "chevrons", "waffen_salve": "triple",
    "waffen_krit": "reticle", "waffen_kritschaden": "serration",
    "off_durchschlag": "pierce",
    "vert_panzerung": "shield", "vert_nano": "cross", "vert_schild": "dome",
    "vert_kuehlung": "aster", "vert_puls": "wave", "vert_wille": "power",
    "vert_kondensator": "battery",
    "ener_leitung": "bolt", "ener_taktik": "delta", "ener_idle": "coin",
    "ener_bonus": "stack", "ener_sep": "core",
    "tec_kuehlung": "aster", "tec_tempfeld": "chevrons", "tec_notstrom": "cross",
    "tec_synergie": "core",
    "eko_bergung": "stack", "eko_kontrakte": "scroll",
    "spez_bully": "hammer", "spez_exekutor": "xmark", "spez_spreng": "star",
    "spez_adrenalin": "gauge", "spez_overdrive": "power", "spez_boss": "crown",
}


def _short(name, n=14):
    return name if len(name) <= n else name[:n - 1] + "…"


def _mix(c, other, k):
    return (int(c[0] + (other[0] - c[0]) * k),
            int(c[1] + (other[1] - c[1]) * k),
            int(c[2] + (other[2] - c[2]) * k))


def _scaled_c(c, k):
    return (max(0, int(c[0] * k)), max(0, int(c[1] * k)), max(0, int(c[2] * k)))


def _bez(p0, p1, p2, n=14):
    """Quadratic Bezier als Punktliste (inkl. Endpunkte)."""
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1.0 - t
        pts.append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                    mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))
    return pts


def _cumlen(pts):
    lens, total = [0.0], 0.0
    for i in range(1, len(pts)):
        total += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        lens.append(total)
    return lens, total


def _point_at(pts, lens, total, t):
    """Punkt + Winkel an Parameter t (0..1) entlang der Polylinie."""
    d = max(0.0, min(1.0, t)) * total
    for i in range(1, len(lens)):
        if lens[i] >= d or i == len(lens) - 1:
            seg = (lens[i] - lens[i - 1]) or 1.0
            k = (d - lens[i - 1]) / seg
            x = pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * k
            y = pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * k
            ang = math.atan2(pts[i][1] - pts[i - 1][1], pts[i][0] - pts[i - 1][0])
            return x, y, ang
    return pts[-1][0], pts[-1][1], 0.0


class NexusUI:
    """Zeichnung + Hit-Test des Orbital Energy Lattice (Kauf-Logik in main.py)."""

    def __init__(self):
        self.selected = None
        self.bursts = []              # [x, y, t, color]
        self.hitmap = {}              # node_id -> Rect
        self.nodes = {}               # node_id -> (x, y, r)
        self.core = (0, 0)
        self._tiers = {}              # PAKET 7B: branch_id -> {node_id: tier}
        self._leaves = {}             # PAKET 7B: branch_id -> Menge der Blattknoten
        self._edge_list = []          # PAKET 7B: [(branch_id, parent|None, child, key)]
        self.train_rect = None
        self.close_rect = None
        self.sheet_rect = None
        self._geo_key = None
        self._paths = {}              # (branch_id, idx) -> (pts, lens, total)
        self._link_state = {}         # (branch_id, idx) -> 'on'|'ready'|'off'
        self._sat = []                # Satelliten-Deko (x, y, ax, ay, color)
        self._bg_key = None
        self._bg_ready = None
        self._sheet_t = 0.0           # Slide-In 0..1
        self._sheet_last = None       # letzter dargestellter Knoten (Fade-Out)
        self._last_elapsed = 0.0

    # ---------------- Geometrie ----------------
    def _branch_layout(self, branch):
        """Tier-Stufen + Blattknoten einer Sparte (aus den reqs abgeleitet).
        AUFTRAG 1: Zyklus-Schutz. Ein fehlerhafter req-Kreis (a -> b -> a)
        liess die Rekursion endlos laufen (Stack Overflow beim Aufbau des
        Nexus). Der in-Arbeit-Merk-Set (in_progress) erkennt den Kreis und
        bricht ihn deterministisch ab - der Baum wird trotzdem gebaut."""
        tiers, nodes = {}, {n["id"]: n for n in branch["nodes"]}
        child_ids = set()
        in_progress = set()          # AUFTRAG 1: Knoten auf dem Rekursionsweg

        def tier_of(nid):
            if nid in tiers:
                return tiers[nid]
            if nid in in_progress:   # AUFTRAG 1: Kreis erkannt -> abbrechen
                tiers[nid] = 0
                return 0
            n = nodes.get(nid)
            if n is None:
                tiers[nid] = 0
                return 0
            in_progress.add(nid)
            reqs = [r for r, _l in n.get("reqs", []) if r in nodes]
            t = 0
            if reqs:
                t = 1 + max(tier_of(r) for r in reqs)
                child_ids.update(reqs)
            in_progress.discard(nid)
            tiers[nid] = t
            return t

        for n in branch["nodes"]:
            tier_of(n["id"])
        leaves = {nid for nid in nodes if nid not in child_ids}
        return tiers, leaves

    def _make_path(self, p0, nid):
        """Bezier-Kurve zu Knoten nid (organischer Schwung, wie in Paket 6)."""
        p1 = self.nodes[nid][:2]
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        ddx, ddy = p1[0] - p0[0], p1[1] - p0[1]
        dist = math.hypot(ddx, ddy) or 1.0
        k = 0.10 + (hash(str(p0) + nid) % 5) * 0.03
        sign = -1.0 if (hash(nid) % 2 == 0) else 1.0
        cx = mx - ddy / dist * dist * k * sign
        cy = my + ddx / dist * dist * k * sign
        pts = _bez(p0, (cx, cy), p1, 14)
        lens, total = _cumlen(pts)
        return (pts, lens, total, nid)

    def compute(self, branches, top, bottom):
        """PAKET 7B: Berechnet den Baum im Bereich [top..bottom] (gecacht).
        Jede Sparte ist ein Faecher vom Kern; Tier = Tiefe in den reqs."""
        W, H = ui_kit.W, ui_kit.H
        sig = tuple((n["id"], tuple(map(tuple, n.get("reqs", []))))
                    for b in branches for n in b["nodes"])
        key = (W, H, top, bottom, sig)
        if key == self._geo_key:
            return self.nodes
        self._geo_key = key

        m = u(24)
        pad = u(30)                                   # Platz fuer Halo + Label
        base_r = max(9, u(15))
        cx_area = m + (W - 2 * m) / 2
        cy_area = top + pad + max(60, bottom - top - 2 * pad) / 2
        avail_r = min(W - 2 * m - pad, (bottom - top) / 2 - pad)
        avail_r = max(base_r * 5.0, avail_r)          # Mindestgroesse
        R_node = avail_r / base_r - 1.7               # Radius in Knoten-Einheiten

        rnd = random.Random(7331)
        self.nodes = {}
        self.hitmap = {}
        self._tiers = {}
        self._leaves = {}
        n_br = max(1, len(branches))
        sector = (2.0 * math.pi / n_br) * 0.85      # Sektor pro Sparte (mit Luft)
        max_t_all = max(1, max((max(t.values()) for t in
                                (self._branch_layout(b)[0] for b in branches)), default=1))
        for bi, branch in enumerate(branches):
            bid = branch["id"]
            tiers, leaves = self._branch_layout(branch)
            self._tiers[bid] = tiers
            self._leaves[bid] = leaves
            base_ang = -math.pi / 2 + bi * (2.0 * math.pi / n_br)
            # --- PAKET 7B: Tidy-Tree ---
            # Blaetter teilen sich den Sparten-Sektor gleichmaessig (DFS-
            # Reihenfolge = keine gekreuzten Aeste); Eltern sitzen im Mittel-
            # winkel ihrer Kinder. Verzweigungen bleiben so klar sichtbar.
            nodes_b = {n["id"]: n for n in branch["nodes"]}
            children = {nid: [] for nid in nodes_b}
            roots = []
            for n in branch["nodes"]:
                reqs = [r for r, _l in n.get("reqs", []) if r in nodes_b]
                if reqs:
                    for r in reqs:
                        children[r].append(n["id"])
                else:
                    roots.append(n["id"])
            angles = {}
            bfs = []
            seen = set()

            def dfs(nid):
                if nid in seen:
                    return
                seen.add(nid)
                ch = children[nid]
                if not ch:
                    bfs.append(nid)
                    return
                for c in ch:
                    dfs(c)

            for r in roots:
                dfs(r)
            nl = max(1, len(bfs))
            for i, lid in enumerate(bfs):
                angles[lid] = (base_ang if nl == 1 else
                               base_ang + (i / (nl - 1) - 0.5) * sector)
            for nid in sorted(nodes_b, key=lambda x: -tiers.get(x, 0)):
                if nid in angles:
                    continue
                ch = [c for c in children[nid] if c in angles]
                if ch:
                    angles[nid] = sum(angles[c] for c in ch) / len(ch)
                else:
                    angles[nid] = base_ang
            # Zickzack fuer Einzelkind-Ketten: verhindert direktes Uebereinander-
            # stapeln langsamer Linien (Parent->einziges Kind->...)
            for root in roots:
                stack = [(root, 0)]
                guard = 0
                while stack and guard < 200:
                    guard += 1
                    nid, depth = stack.pop()
                    ch = children[nid]
                    if len(ch) == 1:
                        c = ch[0]
                        sign = 1.0 if depth % 2 == 0 else -1.0
                        angles[c] = angles[nid] + sign * 0.12
                        stack.append((c, depth + 1))
                    else:
                        for c in ch:
                            stack.append((c, depth + 1))
            # Positionen auf einer Ellipse (breites Landscape nutzt die Breite;
            # die Hoehe bleibt fuer 4 Tier-Ebenen knapp -> rho + Zickzack)
            rx = (W - 2 * m - pad) / 2 * 0.97
            ry = max(base_r * 5.0, (bottom - top) / 2 - pad) * 0.97
            for n in branch["nodes"]:
                nid = n["id"]
                t = tiers.get(nid, 0)
                rho = 0.44 + 0.52 * (t / max_t_all)
                ang = angles.get(nid, base_ang) + rnd.uniform(-0.010, 0.010)
                x = int(cx_area + math.cos(ang) * rx * rho)
                y = int(cy_area + math.sin(ang) * ry * rho)
                r = int(base_r * TIER_SCALE[min(t, len(TIER_SCALE) - 1)])
                self.nodes[nid] = (x, y, r)
                tap = max(u(44), r * 2 + u(10))
                self.hitmap[nid] = pygame.Rect(x - tap // 2, y - tap // 2, tap, tap)
        self.core = (int(cx_area), int(cy_area))

        # --- PAKET 7B: Kollisions-Aufloesung (paarweise Abstossung) ---
        # Der Winkel-Entwurf kann an Sektor-Grenzen eng werden; diese kleine
        # Relaxation garantiert freie Knoten an JEDER Aufloesung. Nur
        # Node-Positionen werden verschoben (Hitmaps danach neu gebaut).
        core_r = u(22)
        ids = list(self.nodes.keys())
        lo_x, hi_x = m + core_r + u(6), W - m - core_r - u(6)
        lo_y, hi_y = top + core_r + u(6), bottom - core_r - u(6)
        for _it in range(30):
            moved = False
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    a, b = ids[i], ids[j]
                    ax, ay, ar = self.nodes[a]
                    bx, by, br = self.nodes[b]
                    min_d = (ar + br) * 1.30
                    dx, dy = bx - ax, by - ay
                    d = math.hypot(dx, dy) or 0.01
                    if d < min_d:
                        push = (min_d - d) / 2.0
                        ux, uy = dx / d, dy / d
                        self.nodes[a] = (int(ax - ux * push), int(ay - uy * push), ar)
                        self.nodes[b] = (int(bx + ux * push), int(by + uy * push), br)
                        moved = True
            # Kern bleibt frei; Nodes bleiben im Bereich
            for k in ids:
                x, y, r = self.nodes[k]
                dx, dy = x - cx_area, y - cy_area
                d = math.hypot(dx, dy) or 0.01
                need = core_r + r + u(6)
                if d < need:
                    self.nodes[k] = (int(cx_area + dx / d * need),
                                     int(cy_area + dy / d * need), r)
                    moved = True
                x, y, r = self.nodes[k]
                nx = min(hi_x, max(lo_x, x))
                ny = min(hi_y, max(lo_y, y))
                if (nx, ny) != (x, y):
                    self.nodes[k] = (nx, ny, r)
                    moved = True
            if not moved:
                break
        for k in ids:                                 # Hitmaps aktualisieren
            x, y, r = self.nodes[k]
            tap = max(u(44), r * 2 + u(10))
            self.hitmap[k] = pygame.Rect(x - tap // 2, y - tap // 2, tap, tap)

        # Bezier-Energieadern: Kern->Wurzel und Voraussetzung->Knoten
        self._paths = {}
        self._edge_list = []
        for branch in branches:
            bid = branch["id"]
            for n in branch["nodes"]:
                nid = n["id"]
                reqs = [r for r, _l in n.get("reqs", []) if r in self.nodes]
                if not reqs:
                    keyp = (bid, None, nid)
                    self._edge_list.append((bid, None, nid, keyp))
                    self._paths[keyp] = self._make_path(self.core, nid)
                else:
                    for par in reqs:
                        keyp = (bid, par, nid)
                        self._edge_list.append((bid, par, nid, keyp))
                        self._paths[keyp] = self._make_path(self.nodes[par][:2], nid)

        # Satelliten-Deko: Mini-Knoten neben ausgewaehlten Adern (rein visuell)
        self._sat = []
        for i, (bid, _par, nid, keyp) in enumerate(self._edge_list):
            if i % 3:
                continue
            pts, lens, total, _nid = self._paths[keyp]
            t = 0.45 + 0.3 * ((hash(bid + nid) % 7) / 7.0)
            x, y, ang = _point_at(pts, lens, total, t)
            side = 1 if i % 2 == 0 else -1
            sx = x + math.cos(ang + side * 1.9) * u(16)
            sy = y + math.sin(ang + side * 1.9) * u(16)
            self._sat.append((sx, sy, x, y, _scaled_c((120, 140, 170), 0.55)))
        return self.nodes

    # ---------------- Interaktion ----------------
    def hit(self, pos):
        """Naechstgelegener Knoten innerhalb seiner Tap-Flaeche."""
        best, best_d = None, 1e18
        for nid, rect in self.hitmap.items():
            if rect.collidepoint(pos):
                x, y, _r = self.nodes[nid]
                d = (x - pos[0]) ** 2 + (y - pos[1]) ** 2
                if d < best_d:
                    best, best_d = nid, d
        return best

    def fire(self, x, y, color):
        self.bursts.append([x, y, 0.0, color])

    def select(self, node_id):
        if node_id and node_id != self.selected:
            self._sheet_t = 0.0
        self.selected = node_id
        if node_id:
            self._sheet_last = node_id

    # ---------------- Hintergrund ----------------
    def _prepare_bg(self, bg):
        W, H = ui_kit.W, ui_kit.H
        key = (W, H, id(bg) if bg is not None else -1)
        if key == self._bg_key:
            return self._bg_ready
        self._bg_key = key
        ready = pygame.Surface((W, H))
        ready.fill((2, 4, 10))
        if bg is not None:
            iw, ih = bg.get_size()
            s = max(W / iw, H / ih)
            img = pygame.transform.smoothscale(bg, (max(2, int(iw * s)) + 1,
                                                    max(2, int(ih * s)) + 1))
            ready.blit(img, ((W - img.get_width()) // 2, (H - img.get_height()) // 2))
            # PAKET 7C: heller (96/106/134 statt 72/84/110) - lesbarer,
            # Atmosphaere bleibt (Vignette folgt unten)
            ready.fill((96, 106, 134), special_flags=pygame.BLEND_RGB_MULT)
        else:
            # Prozedurales Nebelfeld (Fallback, gecacht)
            rnd = random.Random(4242)
            NEBULA_VIOLET = (110, 60, 200)
            for _ in range(5):
                gx, gy = rnd.randrange(W), rnd.randrange(H)
                gr = rnd.randrange(int(min(W, H) * 0.22), int(min(W, H) * 0.5))
                col = rnd.choice((CYAN, NEBULA_VIOLET, (200, 60, 130)))
                ready.blit(radial_glow(_scaled_c(col, 0.5), gr // 2), (gx - gr, gy - gr),
                           special_flags=pygame.BLEND_ADD)
            for _ in range(150):
                x, y = rnd.randrange(W), rnd.randrange(H)
                a = rnd.randrange(30, 110)
                c = rnd.choice(((170, 220, 255), (255, 255, 255), (210, 170, 255)))
                pygame.draw.circle(ready, _scaled_c(c, a / 255.0), (x, y),
                                   rnd.choice((1, 1, 1, 2)))
        # Vignette (Ringe von aussen nach innen, einmalig)
        vg = pygame.Surface((W, H), pygame.SRCALPHA)
        cxy = (W // 2, H // 2)
        maxr = int(math.hypot(W, H) // 2) + 2
        steps = 26
        band = max(4, maxr // steps)
        for i in range(steps):
            t = i / (steps - 1)
            alpha = int(150 * (t ** 2.1))
            rr = maxr - i * band
            if rr <= 0:
                break
            pygame.draw.circle(vg, (0, 0, 0, alpha), cxy, rr, band)
        ready.blit(vg, (0, 0))
        self._bg_ready = ready
        return ready

    # ---------------- Glyphen ----------------
    def _glyph(self, surface, kind, x, y, r, color, lw=None):
        """Individuelles Vektor-Symbol pro Knoten (skaliert mit dem Radius)."""
        s = max(2.0, r * 0.52)
        lw = lw or max(1, int(u(1.6)))
        ln = pygame.draw.line
        ci = pygame.draw.circle
        pg = pygame.draw.polygon
        if kind == "burst":
            for a in (0, 72, 144, 216, 288):
                ax = math.radians(a)
                ln(surface, color, (x + math.cos(ax) * s * 0.3, y + math.sin(ax) * s * 0.3),
                   (x + math.cos(ax) * s, y + math.sin(ax) * s), lw)
            ci(surface, color, (int(x), int(y)), max(1, int(s * 0.22)))
        elif kind == "chevrons":
            for off in (-s * 0.32, s * 0.18):
                pg(surface, color, [(x + off - s * 0.3, y - s * 0.5),
                                    (x + off + s * 0.3, y),
                                    (x + off - s * 0.3, y + s * 0.5),
                                    (x + off - s * 0.05, y)])
        elif kind == "triple":
            ci(surface, color, (int(x), int(y - s * 0.45)), max(1, int(s * 0.26)))
            ci(surface, color, (int(x - s * 0.45), int(y + s * 0.3)), max(1, int(s * 0.26)))
            ci(surface, color, (int(x + s * 0.45), int(y + s * 0.3)), max(1, int(s * 0.26)))
        elif kind == "reticle":
            ci(surface, color, (int(x), int(y)), int(s * 0.7), lw)
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                ln(surface, color, (x + dx * s * 0.45, y + dy * s * 0.45),
                   (x + dx * s, y + dy * s), lw)
        elif kind == "serration":
            pts = []
            for i in range(5):
                pts.append((x - s * 0.7 + i * s * 0.35,
                            y + (s * 0.4 if i % 2 else -s * 0.4)))
            ln(surface, color, pts[0], pts[1], lw)
            for i in range(1, 4):
                ln(surface, color, pts[i], pts[i + 1], lw)
        elif kind == "shield":
            pg(surface, color, [(x, y - s * 0.7), (x + s * 0.6, y - s * 0.35),
                                (x + s * 0.45, y + s * 0.45), (x, y + s * 0.75),
                                (x - s * 0.45, y + s * 0.45), (x - s * 0.6, y - s * 0.35)], lw)
        elif kind == "cross":
            ln(surface, color, (x - s * 0.65, y), (x + s * 0.65, y), lw + 1)
            ln(surface, color, (x, y - s * 0.65), (x, y + s * 0.65), lw + 1)
        elif kind == "dome":
            pygame.draw.arc(surface, color, (x - s * 0.6, y - s * 0.55, s * 1.2, s * 1.2),
                            0.0, math.pi, lw)
            ln(surface, color, (x - s * 0.7, y + s * 0.05), (x + s * 0.7, y + s * 0.05), lw)
        elif kind == "aster":
            for a in (30, 90, 150):
                ax = math.radians(a)
                dx, dy = math.cos(ax) * s * 0.65, math.sin(ax) * s * 0.65
                ln(surface, color, (x - dx, y - dy), (x + dx, y + dy), lw)
        elif kind == "wave":
            pts = [(x - s * 0.7 + i * s * 0.175,
                    y + math.sin(i * 1.05) * s * 0.4) for i in range(9)]
            for i in range(8):
                ln(surface, color, pts[i], pts[i + 1], lw)
        elif kind == "bolt":
            pg(surface, color, [(x + s * 0.15, y - s * 0.75), (x - s * 0.4, y + s * 0.1),
                                (x - s * 0.02, y + s * 0.1), (x - s * 0.2, y + s * 0.75),
                                (x + s * 0.42, y - s * 0.12), (x + s * 0.02, y - s * 0.12)])
        elif kind == "delta":
            pg(surface, color, [(x - s * 0.6, y + s * 0.4), (x + s * 0.65, y),
                                (x - s * 0.6, y - s * 0.4), (x - s * 0.25, y)])
        elif kind == "coin":
            ci(surface, color, (int(x), int(y)), int(s * 0.62), lw)
            ln(surface, color, (x - s * 0.3, y), (x + s * 0.3, y), lw)
        elif kind == "stack":
            for i, oy in enumerate((-s * 0.3, s * 0.05)):
                rect = pygame.Rect(int(x - s * 0.5), int(y + oy), int(s), int(s * 0.26))
                pygame.draw.rect(surface, color, rect, lw, border_radius=2)
        elif kind == "core":
            pg(surface, color, [(x, y - s * 0.7), (x + s * 0.5, y),
                                (x, y + s * 0.7), (x - s * 0.5, y)], lw)
            ci(surface, color, (int(x), int(y)), max(1, int(s * 0.16)))
        elif kind == "hammer":
            rect = pygame.Rect(int(x - s * 0.5), int(y - s * 0.7), int(s * 0.9), int(s * 0.42))
            pygame.draw.rect(surface, color, rect, lw, border_radius=2)
            ln(surface, color, (x, y - s * 0.28), (x + s * 0.3, y + s * 0.7), lw + 1)
        elif kind == "xmark":
            for dx, dy in ((1, 1), (-1, 1)):
                ln(surface, color, (x - dx * s * 0.55, y - dy * s * 0.55),
                   (x + dx * s * 0.55, y + dy * s * 0.55), lw + 1)
        elif kind == "star":
            for a in (0, 45, 90, 135):
                ax = math.radians(a)
                ln(surface, color, (x - math.cos(ax) * s * 0.7, y - math.sin(ax) * s * 0.7),
                   (x + math.cos(ax) * s * 0.7, y + math.sin(ax) * s * 0.7), lw)
            ci(surface, color, (int(x), int(y)), max(1, int(s * 0.2)))
        elif kind == "gauge":
            pygame.draw.arc(surface, color, (x - s * 0.6, y - s * 0.45, s * 1.2, s * 1.1),
                            math.pi * 0.15, math.pi * 0.85, lw)
            na = math.radians(70)
            ln(surface, color, (x, y + s * 0.1),
               (x + math.cos(na) * s * 0.45, y - abs(math.sin(na)) * s * 0.45), lw)
        elif kind == "power":
            ci(surface, color, (int(x), int(y + s * 0.12)), int(s * 0.55), lw)
            ln(surface, color, (x, y - s * 0.7), (x, y + s * 0.1), lw + 1)
        elif kind == "pierce":                  # DURCHSCHLAG: Pfeil durch Panzerplatte
            pygame.draw.rect(surface, color, (int(x - s * 0.15), int(y - s * 0.6),
                                              int(s * 0.34), int(s * 1.2)), lw)
            pg(surface, color, [(x - s * 0.1, y - s * 0.85), (x + s * 0.75, y),
                                (x - s * 0.1, y + s * 0.85)])
        elif kind == "battery":                 # SCHILDKONDENSATOR
            pygame.draw.rect(surface, color, (int(x - s * 0.45), int(y - s * 0.55),
                                              int(s * 0.9), int(s * 1.1)), lw, border_radius=2)
            pygame.draw.line(surface, color, (x, y - s * 0.8), (x, y - s * 0.55), lw + 1)
            ln(surface, color, (x - s * 0.2, y + s * 0.05), (x + s * 0.2, y - s * 0.15), lw)
            ln(surface, color, (x - s * 0.2, y + s * 0.35), (x + s * 0.2, y + s * 0.15), lw)
        elif kind == "scroll":                  # KONTRAKTE
            pygame.draw.rect(surface, color, (int(x - s * 0.45), int(y - s * 0.6),
                                              int(s * 0.9), int(s * 1.2)), lw, border_radius=2)
            for oy in (-s * 0.3, 0.0, s * 0.3):
                ln(surface, color, (x - s * 0.25, y + oy), (x + s * 0.25, y + oy), lw)
        elif kind == "crown":                   # BOSS-JAEGER
            pg(surface, color, [(x - s * 0.7, y + s * 0.5), (x - s * 0.7, y - s * 0.3),
                                (x - s * 0.35, y + s * 0.05), (x, y - s * 0.55),
                                (x + s * 0.35, y + s * 0.05), (x + s * 0.7, y - s * 0.3),
                                (x + s * 0.7, y + s * 0.5)])
        elif kind == "lock":
            body = pygame.Rect(int(x - s * 0.42), int(y - s * 0.05), int(s * 0.84), int(s * 0.62))
            pygame.draw.rect(surface, color, body, lw, border_radius=max(1, int(s * 0.12)))
            pygame.draw.arc(surface, color, (x - s * 0.3, y - s * 0.62, s * 0.6, s * 0.6),
                            0.0, math.pi, lw)

    def _hex(self, x, y, r, rot=0.0):
        return [(int(x + math.cos(math.radians(rot + 60 * i)) * r),
                 int(y + math.sin(math.radians(rot + 60 * i)) * r)) for i in range(6)]

    # ---------------- Zeichnen ----------------
    def draw(self, surface, elapsed, skills, cores, branches, top, bottom, bg=None):
        """Zeichnet Lattice + Info-Sheet. Liefert {'train': rect, 'close': rect}."""
        W, H = ui_kit.W, ui_kit.H
        dt = max(0.0, min(0.1, elapsed - self._last_elapsed))
        self._last_elapsed = elapsed

        surface.blit(self._prepare_bg(bg), (0, 0))
        self.compute(branches, top, bottom)
        m = u(24)

        # Zustand aller Knoten (Datenquelle: skills -> skill_tree.py, unveraendert)
        state = {}
        for branch in branches:
            for node in branch["nodes"]:
                ok, _ = skills.unlock_info(node["id"])
                state[node["id"]] = (skills.level_of(node["id"]), ok, branch)

        # ---- Satelliten-Deko ----
        for sx, sy, ax, ay, col in self._sat:
            pygame.draw.line(surface, _scaled_c(col, 0.5), (ax, ay), (sx, sy), 1)
            pygame.draw.circle(surface, col, (int(sx), int(sy)), max(1, u(2)))

        # ---- Energieadern (PAKET 7B: echte Voraussetzungs-Kanten) ----
        branch_col = {b["id"]: b["color"] for b in branches}
        for (bid, _par, nid, keyp) in self._edge_list:
            color = branch_col[bid]
            if keyp not in self._paths:
                continue
            pts, lens, total, _nid = self._paths[keyp]
            lvl, ok, _b = state[nid]
            segs = list(zip(pts, pts[1:]))
            if lvl > 0:
                # aktive Ader: dunkle Aura + Kern + helle Seele
                pygame.draw.lines(surface, _scaled_c(color, 0.22), False, pts, max(3, u(5)))
                pygame.draw.lines(surface, color, False, pts, max(2, u(2)))
                pygame.draw.lines(surface, _mix(color, WHITE, 0.55), False, pts, 1)
                # wandernde Energiestrome
                speed = 0.22 + (hash(nid) % 5) * 0.035
                for pj in range(2):
                    t = ((elapsed * speed + pj * 0.5 + (hash(nid) % 97) / 97.0) % 1.0)
                    px, py, _a = _point_at(pts, lens, total, t)
                    glow = radial_glow(color, 7)
                    surface.blit(glow, glow.get_rect(center=(int(px), int(py))),
                                 special_flags=pygame.BLEND_ADD)
                    pygame.draw.circle(surface, WHITE, (int(px), int(py)), max(1, u(2)))
            elif ok:
                a = 0.45 + 0.3 * math.sin(elapsed * 2.6 + hash(nid) % 7)
                pygame.draw.lines(surface, _scaled_c(color, a), False, pts, max(1, u(1)))
            else:
                seg = max(6, u(9))
                acc, dash_on = 0.0, True
                for (p1, p2) in segs:
                    d = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
                    if acc + d >= seg:
                        dash_on = not dash_on
                        acc = 0.0
                    acc += d
                    if dash_on:
                        pygame.draw.line(surface, _scaled_c(DIM, 0.85), p1, p2, 1)

        # ---- Knoten ----
        for branch in branches:
            color = branch["color"]
            for ni, node in enumerate(branch["nodes"]):
                nid = node["id"]
                x, y, r = self.nodes[nid]
                lvl, ok, _b = state[nid]
                sel = (self.selected == nid)
                rot = (hash(nid) % 60)
                cap = (nid in self._leaves.get(branch["id"], ()))   # PAKET 7B: Blattknoten
                pts = self._hex(x, y, r, rot)

                # persistentes Leuchten gekaufter Knoten
                if lvl > 0:
                    glow = radial_glow(color, int(r * (2.6 if sel else 2.0)))
                    surface.blit(glow, glow.get_rect(center=(x, y)),
                                 special_flags=pygame.BLEND_ADD)

                if sel:
                    g2 = radial_glow(_mix(color, WHITE, 0.4), int(r * 2.8))
                    surface.blit(g2, g2.get_rect(center=(x, y)),
                                 special_flags=pygame.BLEND_ADD)

                if lvl > 0:
                    fill = _mix(_scaled_c(color, 0.30), (6, 10, 18), 0.35)
                    ring, rw = (GREEN if lvl >= node["max"] else color), max(2, u(2))
                elif ok:
                    fill = (7, 12, 20)
                    ring, rw = color, max(1, u(2))
                else:
                    fill = (7, 9, 14)
                    ring, rw = _scaled_c(DIM, 0.9), 1
                pygame.draw.polygon(surface, fill, pts)
                if lvl == 0 and not ok:
                    for i in range(0, 6, 2):        # gestrichelter Ring (Nebel)
                        pygame.draw.line(surface, ring, pts[i], pts[(i + 1) % 6], rw)
                else:
                    pygame.draw.polygon(surface, ring, pts, rw)
                if cap and (lvl > 0 or ok):         # Kronen-Knoten: Doppelring
                    outer = self._hex(x, y, int(r * 1.30), rot + 30)
                    pygame.draw.polygon(surface, _scaled_c(ring, 0.55), outer, 1)

                # Symbol / Schloss
                if lvl > 0 or ok:
                    gcol = WHITE if lvl > 0 else _mix(color, WHITE, 0.15)
                    self._glyph(surface, GLYPH.get(nid, "core"), x, y, r, gcol)
                    if lvl > 0:
                        pygame.draw.circle(surface, color, (x, y), max(2, int(r * 0.34)))
                        self._glyph(surface, GLYPH.get(nid, "core"), x, y,
                                    max(3, int(r * 0.55)), WHITE, lw=1)
                else:
                    self._glyph(surface, "lock", x, y, int(r * 0.8), _scaled_c(MUTED, 0.8))

                # Puls-Halo freischaltbarer Knoten
                if lvl == 0 and ok:
                    pr = r + u(4) + math.sin(elapsed * 3.0 + ni * 1.3) * u(2.5)
                    pygame.draw.circle(surface, _scaled_c(color, 0.8), (x, y), int(pr), 1)
                    pygame.draw.circle(surface, _scaled_c(color, 0.4), (x, y),
                                       int(pr + u(4)), 1)

                # Auswahl-Bogen (rotierend, doppelseitig)
                if sel:
                    a0 = math.radians((elapsed * 140) % 360)
                    ar = r + u(6)
                    for off in (0.0, math.pi):
                        pygame.draw.arc(surface, WHITE,
                                        (x - ar, y - ar, ar * 2, ar * 2),
                                        a0 + off, a0 + off + 1.1, 2)

                # Stufen-Pips
                if lvl > 0 or ok:
                    if node["max"] > 1:
                        pr = max(2, u(2.4))
                        gap = pr * 2 + u(2.4)
                        px0 = x - (node["max"] * gap) // 2 + gap // 2
                        py = y + int(r * 1.30) + u(6)
                        for i in range(node["max"]):
                            c = ring if i < lvl else (30, 36, 48)
                            pygame.draw.circle(surface, c, (int(px0 + i * gap), py), pr)

                # Name: gekaufte/freischaltbare/gewaehlte Knoten (Nebel: gesperrte anonym)
                if lvl > 0 or ok or sel:
                    below = (y - r) >= top or (y >= (top + bottom) / 2)
                    ly = y + int(r * 1.30) + u(20) if below else y - int(r * 1.30) - u(8)
                    col = WHITE if sel else (WHITE if lvl > 0 else _mix(color, WHITE, 0.25))
                    text(surface, _short(node["name"], 13), F(9), col, (x, ly),
                         "midtop" if below else "midbottom")

            # Pfad-Label am aeussersten Knoten der Sparte
            far = max(branch["nodes"], key=lambda n: self._tiers.get(branch["id"], {}).get(n["id"], 0))
            lx, ly, _lr = self.nodes[far["id"]]
            vx, vy = lx - self.core[0], ly - self.core[1]
            d = math.hypot(vx, vy) or 1
            lx = int(min(W - m - u(58), max(m + u(58), lx + vx / d * u(30))))
            ly = int(min(bottom - u(8), max(top + u(8), ly + vy / d * u(26))))
            neon_text(surface, _short(branch["name"], 16), F(10), branch["color"],
                      (lx, ly), "center", 1)

        # ---- NEXUS-KERN ----
        cx, cy = self.core
        pulse = 1 + 0.07 * math.sin(elapsed * 2.2)
        cr = int(u(22) * pulse)
        glow = radial_glow(CYAN, int(u(30) * pulse))
        surface.blit(glow, glow.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_ADD)
        pygame.draw.circle(surface, (8, 20, 34), (cx, cy), cr)
        pygame.draw.circle(surface, CYAN, (cx, cy), cr, 3)
        pygame.draw.circle(surface, CYAN, (cx, cy), max(3, int(cr * 0.45)))
        pygame.draw.circle(surface, WHITE, (cx, cy), max(2, int(cr * 0.20)))
        for k in range(8):
            a = math.radians(elapsed * 40 + k * 45)
            pygame.draw.line(surface, CYAN_SOFT,
                             (cx + math.cos(a) * cr * 1.25, cy + math.sin(a) * cr * 1.25),
                             (cx + math.cos(a) * cr * 1.55, cy + math.sin(a) * cr * 1.55), 2)
        a0 = math.radians((elapsed * 90) % 360)
        pygame.draw.arc(surface, _mix(CYAN, WHITE, 0.4),
                        (cx - cr * 1.8, cy - cr * 1.8, cr * 3.6, cr * 3.6),
                        a0, a0 + 1.2, 2)
        text(surface, "NEXUS-KERN", F(10), CYAN, (cx, cy + int(cr * 1.9)), "midtop")

        # ---- Kauf-Bursts ----
        alive = []
        for bx, by, t0, color in self.bursts:
            t0 += dt
            if t0 < 0.75:
                k = t0 / 0.75
                rr = int(u(8) + k * u(85))
                ga = radial_glow(_mix(color, WHITE, 0.5), int(26 * (1 - k) + 8))
                surface.blit(ga, ga.get_rect(center=(bx, by)), special_flags=pygame.BLEND_ADD)
                pygame.draw.circle(surface, _mix(color, WHITE, k),
                                   (bx, by), rr, max(2, u(3 - int(k * 2))))
                for i in range(6):
                    an = math.radians(i * 60 + k * 90)
                    d1 = rr * (0.55 + 0.25 * math.sin(i * 2.1))
                    p1 = (bx + math.cos(an) * d1 * 0.75, by + math.sin(an) * d1 * 0.75)
                    p2 = (bx + math.cos(an) * d1, by + math.sin(an) * d1)
                    pygame.draw.line(surface, color, p1, p2, max(1, u(1)))
                alive.append([bx, by, t0, color])
        self.bursts = alive

        # ---- Hinweis (nur ohne Auswahl) ----
        if not self.selected and self._sheet_t <= 0.0:
            hint = "Knoten antippen, um Details zu sehen"
            if W > H:
                text(surface, hint, F(10), MUTED, (W // 2, top + u(4)), "midtop")
            else:
                text(surface, hint, F(10), MUTED, (W // 2, bottom - u(16)), "midbottom")

        # ---- Info-Sheet (Slide-In) ----
        self.train_rect = None
        self.close_rect = None
        self.sheet_rect = None
        show_id = self.selected or (self._sheet_last if self._sheet_t > 0.0 else None)
        if show_id:
            target = 1.0 if self.selected else 0.0
            self._sheet_t = min(1.0, self._sheet_t + dt * 5.0) if self.selected \
                else max(0.0, self._sheet_t - dt * 5.0)
            if self._sheet_t <= 0.0 and not self.selected:
                self._sheet_last = None
                return {"train": None, "close": None}
            t = 1.0 - (1.0 - self._sheet_t) ** 3      # ease-out cubic
            node = branch = None
            for br in branches:
                for nd in br["nodes"]:
                    if nd["id"] == show_id:
                        branch, node = br, nd
            if node:
                from skill_tree import effect_text
                landscape = W > H
                if landscape:
                    sw = min(int(W * 0.40), W - u(320))
                    sw = max(sw, u(300))
                    sh = bottom - top
                    rx = W - sw - u(14)
                    ry = top
                    xoff = int((1 - t) * (sw + u(30)))
                else:
                    sw = W - u(24)
                    sh = int(H * 0.27)
                    rx = u(12)
                    ry = H - sh - u(10)
                    xoff = 0
                    yoff = int((1 - t) * (sh + u(24)))
                rect = pygame.Rect(rx + xoff, ry + (yoff if not landscape else 0), sw, sh)
                self.sheet_rect = rect
                # Transluzentes Panel (Netzwerk bleibt rechts erkennbar), gecacht
                bkey = (rect.w, rect.h)
                sbg = self._sheet_bg if getattr(self, "_sheet_bg_key", None) == bkey else None
                if sbg is None:
                    sbg = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                    sbg.fill((4, 9, 18, 214))
                    pygame.draw.rect(sbg, (255, 255, 255, 14),
                                     rect.inflate(-u(8), -u(8)).move(-rect.x, -rect.y),
                                     1, border_radius=u(10))
                    self._sheet_bg = sbg
                    self._sheet_bg_key = bkey
                surface.blit(sbg, rect.topleft)
                pygame.draw.rect(surface, branch["color"], rect, 2, border_radius=u(14))
                pad = u(14)
                lvl = skills.level_of(node["id"])
                ok, reason = skills.unlock_info(node["id"])
                cost = skills.cost_of(node["id"])
                cores_ok = cores >= cost
                neon_text(surface, node["name"], F(14), branch["color"],
                          (rect.x + pad, rect.y + u(12)), "topleft", 1)
                text(surface, f"STUFE {lvl}/{node['max']}", F(11), WHITE,
                     (rect.x + pad, rect.y + u(36)))
                for i in range(node["max"]):
                    px = rect.x + pad + u(84) + i * u(14)
                    pygame.draw.circle(surface, GREEN if i < lvl else (30, 36, 48),
                                       (int(px), int(rect.y + u(42))), max(3, u(4)))
                desc_f = F(10)
                max_w = rect.width - pad * 2 - (u(8) if landscape else u(10))
                y = rect.y + u(58)
                used = 0
                for ln2 in wrap_text(node["desc"], desc_f, max_w)[:3]:
                    text(surface, ln2, desc_f, MUTED, (rect.x + pad, y + used))
                    used += int(desc_f.get_height() * 1.2)
                y2 = y + used + u(6)
                if lvl > 0:
                    text(surface, f"Aktuell: {effect_text(node['id'], lvl)}", desc_f,
                         CYAN_SOFT, (rect.x + pad, y2))
                    y2 += int(desc_f.get_height() * 1.25)
                if lvl < node["max"]:
                    text(surface, f"Naechste: {effect_text(node['id'], lvl + 1)}", desc_f,
                         WHITE, (rect.x + pad, y2))
                    y2 += int(desc_f.get_height() * 1.25)
                    cost_col = GREEN if cores_ok else RED
                    text(surface, f"Kosten: {cost} Data Cores", F(11), cost_col,
                         (rect.x + pad, y2))
                else:
                    text(surface, "MAXIMAL AUSGEBAUT", F(11), GREEN, (rect.x + pad, y2))
                # TRAIN-Button
                tw, th = u(150), u(52)
                if landscape:
                    trect = pygame.Rect(rect.right - tw - u(14),
                                        rect.bottom - th - u(14), tw, th)
                else:
                    trect = pygame.Rect(rect.right - tw - u(14),
                                        rect.bottom - th - u(14), tw, th)
                self.train_rect = trect
                can = ok and cores_ok and lvl < node["max"]
                sub = "" if can else ("MAX" if lvl >= node["max"] else "GESPERRT")
                btn = Btn("train", trect, "TRAIN", sub, accent=branch["color"], enabled=can)
                if can:
                    pa = 0.5 + 0.5 * math.sin(elapsed * 4.0)
                    pulse_rect = trect.inflate(int(u(4) + u(3) * pa), int(u(4) + u(3) * pa))
                    pygame.draw.rect(surface, _scaled_c(branch["color"], 0.35 + 0.3 * pa),
                                     pulse_rect, 2, border_radius=u(12))
                draw_btn(surface, btn)
                if not ok and lvl < node["max"]:
                    text(surface, reason, F(9), RED, (trect.centerx, trect.y - u(12)), "midtop")
                # Close-X
                cs = max(u(30), u(26))
                crect = pygame.Rect(rect.right - cs - u(8), rect.y + u(8), cs, cs)
                self.close_rect = crect
                pygame.draw.rect(surface, (10, 16, 28), crect, border_radius=u(8))
                pygame.draw.rect(surface, MUTED, crect, 2, border_radius=u(8))
                ccx, ccy = crect.center
                pygame.draw.line(surface, WHITE, (ccx - u(6), ccy - u(6)),
                                 (ccx + u(6), ccy + u(6)), 2)
                pygame.draw.line(surface, WHITE, (ccx + u(6), ccy - u(6)),
                                 (ccx - u(6), ccy + u(6)), 2)
        return {"train": self.train_rect, "close": self.close_rect}
