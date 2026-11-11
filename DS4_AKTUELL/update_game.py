with open("main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Starte Reparatur (Hintergrund in draw_playing)...")

# Suche nach der Methode "def draw_playing(self):"
found = False
for i, line in enumerate(lines):
    if "def draw_playing(self):" in line:
        # Füge den Hintergrund-Code nach der Methodendefinition ein
        bg_code = [
            "        # --- HINTERGRUND ZEICHNEN (Hier eingefügt, um das Gitter zu überdecken) ---\n",
            "        if not self.idle_mode and hasattr(self, 'bg_chapter_1_part_1') and self.bg_chapter_1_part_1:\n",
            "            combat_bg = self.idle_combat if self.idle_mode else self.pve\n",
            "            if combat_bg.stage_id <= 5: SCREEN.blit(self.bg_chapter_1_part_1, (0, 0))\n",
            "            elif combat_bg.stage_id <= 10: SCREEN.blit(self.bg_chapter_1_part_2, (0, 0))\n",
            "            else: SCREEN.blit(self.bg_chapter_1_part_3, (0, 0))\n",
            "            \n",
            "            overlay_bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)\n",
            "            overlay_bg.fill((0, 0, 0, 50))\n",
            "            SCREEN.blit(overlay_bg, (0, 0))\n",
            "        # -------------------------------------------------------------------------\n"
        ]
        
        # Füge die Zeilen nach der Definition ein (bei i+1)
        lines[i+1:i+1] = bg_code
        found = True
        print("✅ Hintergrund-Logik erfolgreich am Anfang von draw_playing() eingefügt.")
        break

if not found:
    print("⚠️ Konnte 'def draw_playing(self):' nicht finden. Bitte prüfe die main.py.")

with open("main.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("\n🎉 Fertig! Starte jetzt main.py.")