from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
from PIL import Image, ImageTk, ImageDraw
from scipy import ndimage


APP_TITLE = "Corridor Slayer | PNG Sprite Extractor"
SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def estimate_background(rgb: np.ndarray, border_width: int = 5) -> np.ndarray:
    """Estimate background RGB from a thin strip around the image edges."""
    h, w, _ = rgb.shape
    b = max(1, min(border_width, h // 4 or 1, w // 4 or 1))
    edge = np.concatenate([
        rgb[:b, :, :].reshape(-1, 3),
        rgb[-b:, :, :].reshape(-1, 3),
        rgb[:, :b, :].reshape(-1, 3),
        rgb[:, -b:, :].reshape(-1, 3),
    ], axis=0)
    # Quantize colors so anti-aliased edge noise does not dominate.
    quantized = (edge // 16) * 16
    packed = quantized[:, 0] * 65536 + quantized[:, 1] * 256 + quantized[:, 2]
    values, counts = np.unique(packed, return_counts=True)
    key = values[np.argmax(counts)]
    return np.array([(key >> 16) & 255, (key >> 8) & 255, key & 255], dtype=np.float32)


def remove_background_and_find_objects(
    image: Image.Image,
    tolerance: float = 38.0,
    min_area: int = 180,
    edge_band: int = 5,
    close_gap: int = 2,
):
    """Return RGBA image with inferred background removed and object bounding boxes."""
    rgba = image.convert("RGBA")
    arr = np.array(rgba)
    rgb = arr[:, :, :3].astype(np.float32)
    original_alpha = arr[:, :, 3]
    bg = estimate_background(rgb, edge_band)

    # Euclidean RGB distance from inferred background.
    distance = np.sqrt(np.sum((rgb - bg[None, None, :]) ** 2, axis=2))
    foreground = (distance > tolerance) & (original_alpha > 8)

    # Close tiny gaps, then remove small speckles.
    if close_gap > 0:
        structure = np.ones((close_gap * 2 + 1, close_gap * 2 + 1), dtype=bool)
        foreground = ndimage.binary_closing(foreground, structure=structure)
    foreground = ndimage.binary_fill_holes(foreground)

    labels, count = ndimage.label(foreground)
    objects = ndimage.find_objects(labels)
    boxes = []
    clean_alpha = np.where(foreground, original_alpha, 0).astype(np.uint8)

    for label_id, slc in enumerate(objects, start=1):
        if slc is None:
            continue
        y_slice, x_slice = slc
        component = labels[slc] == label_id
        area = int(component.sum())
        if area < min_area:
            clean_alpha[slc][component] = 0
            continue
        y0, y1 = y_slice.start, y_slice.stop
        x0, x1 = x_slice.start, x_slice.stop
        boxes.append((x0, y0, x1, y1, area))

    # Preserve original RGB while replacing alpha with extracted mask.
    out = arr.copy()
    out[:, :, 3] = clean_alpha
    return Image.fromarray(out, "RGBA"), sorted(boxes, key=lambda b: (b[1], b[0])), tuple(int(v) for v in bg)


def safe_stem(path: Path) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in path.stem).strip("_") or "image"


class SpriteExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1040x760")
        self.root.minsize(850, 620)

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.tolerance = tk.IntVar(value=38)
        self.min_area = tk.IntVar(value=180)
        self.edge_band = tk.IntVar(value=5)
        self.padding = tk.IntVar(value=8)
        self.current_image = None
        self.current_path = None
        self.preview_photo = None
        self.preview_result = None

        self._build_ui()

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Corridor Slayer – automatische PNG-Aufbereitung",
                  font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="Hintergrund an den Bildrändern erkennen • Objekte ausschneiden • transparente PNGs exportieren",
            wraplength=900
        ).pack(anchor="w", pady=(4, 12))

        folders = ttk.LabelFrame(outer, text="Ordner", padding=10)
        folders.pack(fill="x")
        ttk.Label(folders, text="Eingabe").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(folders, textvariable=self.input_dir).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(folders, text="Durchsuchen…", command=self.choose_input).grid(row=0, column=2, padx=(8, 0))
        ttk.Label(folders, text="Ausgabe").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(folders, textvariable=self.output_dir).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(folders, text="Durchsuchen…", command=self.choose_output).grid(row=1, column=2, padx=(8, 0))
        folders.columnconfigure(1, weight=1)

        settings = ttk.LabelFrame(outer, text="Erkennung einstellen", padding=10)
        settings.pack(fill="x", pady=10)
        self._slider(settings, "Hintergrund-Toleranz", self.tolerance, 5, 120, 0, 0)
        self._slider(settings, "Mindestgröße (Pixel)", self.min_area, 10, 3000, 0, 1)
        self._slider(settings, "Randstreifen (Pixel)", self.edge_band, 1, 20, 1, 0)
        self._slider(settings, "Zusätzlicher Rand um Sprite (Pixel)", self.padding, 0, 40, 1, 1)

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="Ausgewähltes Bild prüfen", command=self.preview).pack(side="left")
        ttk.Button(actions, text="Alle Bilder verarbeiten", command=self.process_all).pack(side="left", padx=8)
        self.status = tk.StringVar(value="Wähle einen Eingabeordner mit PNGs aus.")
        ttk.Label(actions, textvariable=self.status).pack(side="left", padx=10)

        preview_frame = ttk.LabelFrame(outer, text="Vorschau", padding=8)
        preview_frame.pack(fill="both", expand=True)
        self.preview_label = ttk.Label(preview_frame, text="Hier erscheint die Vorschau.")
        self.preview_label.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(outer, height=5)
        self.listbox.pack(fill="x", pady=(8, 0))
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

    def _slider(self, parent, label, variable, low, high, row, col):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, sticky="ew", padx=8, pady=4)
        ttk.Label(frame, text=label).pack(anchor="w")
        scale = ttk.Scale(frame, from_=low, to=high, orient="horizontal",
                          command=lambda v, var=variable: var.set(round(float(v))))
        scale.set(variable.get())
        scale.pack(fill="x")
        ttk.Label(frame, textvariable=variable).pack(anchor="e")
        parent.columnconfigure(col, weight=1)

    def choose_input(self):
        path = filedialog.askdirectory(title="Ordner mit deinen PNGs auswählen")
        if path:
            self.input_dir.set(path)
            if not self.output_dir.get():
                self.output_dir.set(str(Path(path) / "sprites_export"))
            self.refresh_files()

    def choose_output(self):
        path = filedialog.askdirectory(title="Ausgabeordner auswählen")
        if path:
            self.output_dir.set(path)

    def files(self):
        folder = Path(self.input_dir.get())
        if not folder.is_dir():
            return []
        return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED)

    def refresh_files(self):
        self.listbox.delete(0, tk.END)
        for p in self.files():
            self.listbox.insert(tk.END, p.name)
        self.status.set(f"{len(self.files())} Bild(er) gefunden.")
        if self.files():
            self.listbox.selection_set(0)
            self.preview()

    def _on_select(self, _event):
        self.preview()

    def selected_path(self):
        selected = self.listbox.curselection()
        files = self.files()
        if selected and selected[0] < len(files):
            return files[selected[0]]
        return files[0] if files else None

    def preview(self):
        path = self.selected_path()
        if not path:
            messagebox.showwarning("Kein Bild", "Wähle zuerst einen Ordner mit Bilddateien.")
            return
        try:
            image = Image.open(path)
            result, boxes, bg = remove_background_and_find_objects(
                image,
                tolerance=self.tolerance.get(),
                min_area=self.min_area.get(),
                edge_band=self.edge_band.get(),
            )
            self.current_image = image
            self.current_path = path
            self.preview_result = (result, boxes, bg)

            # Checkerboard background for transparency preview.
            thumb = result.copy()
            thumb.thumbnail((760, 410))
            checker = Image.new("RGB", thumb.size, (220, 220, 220))
            draw = ImageDraw.Draw(checker)
            cell = 12
            for y in range(0, checker.height, cell):
                for x in range(0, checker.width, cell):
                    if (x // cell + y // cell) % 2:
                        draw.rectangle((x, y, x + cell, y + cell), fill=(245, 245, 245))
            checker.paste(thumb, (0, 0), thumb)
            scale_x = thumb.width / image.width
            scale_y = thumb.height / image.height
            d = ImageDraw.Draw(checker)
            for x0, y0, x1, y1, _area in boxes:
                d.rectangle((int(x0*scale_x), int(y0*scale_y), int(x1*scale_x), int(y1*scale_y)),
                            outline=(0, 220, 255), width=2)
            self.preview_photo = ImageTk.PhotoImage(checker)
            self.preview_label.configure(image=self.preview_photo, text="")
            self.status.set(f"{path.name}: {len(boxes)} Objekt(e), geschätzter Hintergrund RGB {bg}")
        except Exception as exc:
            messagebox.showerror("Fehler beim Öffnen", str(exc))

    def process_all(self):
        files = self.files()
        if not files:
            messagebox.showwarning("Keine Bilder", "Wähle zuerst einen Eingabeordner mit Bildern.")
            return
        output_root = Path(self.output_dir.get().strip())
        if not str(output_root):
            messagebox.showwarning("Ausgabe fehlt", "Bitte einen Ausgabeordner auswählen.")
            return
        output_root.mkdir(parents=True, exist_ok=True)
        padding = self.padding.get()
        report = []

        for path in files:
            try:
                original = Image.open(path).convert("RGBA")
                result, boxes, bg = remove_background_and_find_objects(
                    original,
                    tolerance=self.tolerance.get(),
                    min_area=self.min_area.get(),
                    edge_band=self.edge_band.get(),
                )
                stem = safe_stem(path)
                folder = output_root / stem
                folder.mkdir(parents=True, exist_ok=True)

                # Save full-size transparent image too.
                result.save(folder / f"{stem}_transparent.png")

                for index, (x0, y0, x1, y1, area) in enumerate(boxes, start=1):
                    x0p = max(0, x0 - padding)
                    y0p = max(0, y0 - padding)
                    x1p = min(result.width, x1 + padding)
                    y1p = min(result.height, y1 + padding)
                    crop = result.crop((x0p, y0p, x1p, y1p))
                    # Trim transparent pixels to the actual object plus configured padding.
                    crop.save(folder / f"{stem}_sprite_{index:03d}.png")

                report.append({
                    "source": path.name,
                    "objects": len(boxes),
                    "background_rgb": bg,
                    "files": [f"{stem}_sprite_{i:03d}.png" for i in range(1, len(boxes)+1)],
                })
            except Exception as exc:
                report.append({"source": path.name, "error": str(exc)})

        (output_root / "processing_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self.status.set(f"Fertig: {len(files)} Bild(er) verarbeitet → {output_root}")
        messagebox.showinfo(
            "Verarbeitung abgeschlossen",
            f"{len(files)} Bild(er) verarbeitet.\nAusgabe:\n{output_root}\n\n"
            "Bitte kontrolliere einige Sprites. Bei falscher Erkennung die Toleranz anpassen."
        )


if __name__ == "__main__":
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    SpriteExtractorApp(root)
    root.mainloop()
