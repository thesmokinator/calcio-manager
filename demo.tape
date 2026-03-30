# Calcio Manager — demo recording
#
# Journey: terminal prompt → main menu → 5-step new-game wizard
#          → game hub → squad roster → league table → live match
#
# Requirements:
#   brew install vhs
#   uv sync
#
# Record:
#   vhs demo.tape

Output demo.gif

Set Shell         "zsh"
Set FontSize      14
Set Width         1400
Set Height        800
Set Theme         "Catppuccin Mocha"
Set PlaybackSpeed 1.0
Set TypingSpeed   80ms
Set Padding       0

# ── Launch ───────────────────────────────────────────────────────────────────
Sleep 1s
Type "uv run calcio-manager"
Enter
Sleep 4s

# ── Main Menu ─────────────────────────────────────────────────────────────────
Enter
Sleep 1.5s

# ── Wizard Step 1: Region ─────────────────────────────────────────────────────
Enter
Sleep 2s

# ── Wizard Step 2: Province ───────────────────────────────────────────────────
Enter
Sleep 2s

# ── Wizard Step 3: Comune ─────────────────────────────────────────────────────
Enter
Sleep 2s

# ── Wizard Step 4: Team customization ────────────────────────────────────────
Enter
Sleep 7s

# ── Wizard Step 5: Tournament preview ────────────────────────────────────────
Sleep 2s
Enter
Sleep 5s

# ── Game Hub ──────────────────────────────────────────────────────────────────
Sleep 2s

Type "r"
Sleep 3s

Escape
Sleep 500ms
Type "l"
Sleep 3s

Escape
Sleep 500ms
Type "p"
Sleep 500ms
Space
Sleep 10s
