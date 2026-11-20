# CORRIDOR SLAYER

CORRIDOR SLAYER is a Python 2D shooter built with Pygame. The game runtime
supports Python 3.10, 3.11, and 3.12 on Windows. The core runtime dependencies
are listed in `requirements.txt`.

## Windows setup

Install Python 3.12, then open PowerShell in this folder and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

To run the automated checks:

```powershell
python -m unittest discover -s tests -v
python tools/check_bugs.py
python tools/check_campaign.py
python tools/check_economy.py
python tools/check_orientation.py
```

The test and check scripts use temporary files for their own data. They do
not alter the player's save files. `simulate_boss.py` and
`simulate_campaign.py` run combat-balance simulations without opening a game
window.

## Optional features and tools

The intro, victory, and defeat videos use OpenCV (`opencv-python`) when it is
installed, or imageio/ffmpeg as an alternative. Install one backend with
`python -m pip install opencv-python` or
`python -m pip install "imageio[ffmpeg]"`; without a decoder, the game uses
its built-in image or UI fallbacks. Installing `requirements-optional.txt`
provides both backends plus the tools needed by the sprite extractor.
The `tools/sprite_extractor.py` GUI additionally needs Pillow and SciPy,
also listed in `requirements-optional.txt`.

Player saves, preferences, and logs are stored in the operating system's
user-data directory. Existing JSON saves beside the game are copied there the
first time they are loaded; the original files are retained as backups.
