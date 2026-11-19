#!/usr/bin/env python3
"""Offline-Pruefung: Sind alle 15 Antriebsstufen korrekt hinterlegt?

Aufruf im Repo-Hauptordner:  python integration_check.py
Ohne pygame werden nur Dateien + Metadaten geprueft; mit pygame wird
zusaetzlich die echte Ladefunktion simuliert.
"""
import json
import os
import sys

FOLDER = os.path.join('antriebe', 'Antriebsgrafiken_LVL1-12')


def main():
    ok = True
    meta = json.load(open(os.path.join(FOLDER, 'meta.json'), encoding='utf-8'))
    n = len(meta['stufen'])
    print(f"meta.json Stufen: {n} -> {sorted(meta['stufen'].keys(), key=int)}")
    if n != 15:
        print('!! meta.json enthaelt nicht 15 Stufen')
        ok = False
    for lvl in range(1, 16):
        p = f'engine_lvl{lvl:02d}'
        need = [
            (FOLDER, f'ebenen/{p}_body_512x384.png', (512, 384)),
            (FOLDER, f'ebenen/{p}_flame_8frames_512x384.png', (512, 3072)),
            (FOLDER, f'ebenen/{p}_glow_8frames_512x384.png', (512, 3072)),
            (FOLDER, f'atlas/{p}_anim_8frames_512x384.png', (512, 3072)),
        ]
        stufe = meta['stufen'].get(str(lvl), {})
        if not stufe:
            print(f'!! LVL {lvl}: fehlt in meta.json')
            ok = False
            continue
        for base, rel, size in need:
            fp = os.path.join(base, rel)
            if not os.path.isfile(fp):
                print(f'!! LVL {lvl}: Datei fehlt: {rel}')
                ok = False
                continue
            try:
                from PIL import Image
                im = Image.open(fp)
                if im.size != size:
                    print(f'!! LVL {lvl}: {rel} hat {im.size} statt {size}')
                    ok = False
            except ImportError:
                pass
        if int(stufe.get('frames', 0)) != 8 or int(stufe.get('fps', 0)) != 12:
            print(f'!! LVL {lvl}: frames/fps nicht 8/12')
            ok = False
    # pygame-Simulation der Ladefunktion
    try:
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        import pygame
        pygame.init()
        pygame.display.set_mode((1, 1))
        print('pygame gefunden: simulierte Ladefunktion...')
        for lvl in range(1, 16):
            p = f'engine_lvl{lvl:02d}'
            body = pygame.image.load(os.path.join(
                FOLDER, 'ebenen', f'{p}_body_512x384.png')).convert_alpha()
            flame = pygame.image.load(os.path.join(
                FOLDER, 'ebenen', f'{p}_flame_8frames_512x384.png')).convert_alpha()
            glow = pygame.image.load(os.path.join(
                FOLDER, 'ebenen', f'{p}_glow_8frames_512x384.png')).convert_alpha()
            assert body.get_size() == (512, 384)
            assert flame.get_width() == 512 and flame.get_height() >= 384 * 8
            assert glow.get_width() == 512 and glow.get_height() >= 384 * 8
        print('pygame-Load: alle 15 Stufen OK')
    except ImportError:
        print('(pygame nicht installiert - nur Datei-/Meta-Pruefung)')
    print('ERGEBNIS:', 'OK' if ok else 'FEHLER GEFUNDEN')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
