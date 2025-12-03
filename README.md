# Claude Bouncing Star Screensaver

A fullscreen animated screensaver featuring Claude's asterisk logo with DVD-style bouncing, physics-based googly eyes, and a REST API for external manipulation.

## Features

- **DVD-style bouncing** - Classic screensaver physics with wall collision detection
- **QRS cardiac heartbeat pulse** - 4-second cycle with main beat and T-wave echo, pulses scale up to 108%
- **Googly eyes with physics** - Optional eyes that react to:
  - Gravity (pupils fall down relative to star rotation)
  - Centrifugal force during fast spins
  - Heartbeat pulses (subtle upward nudge)
  - Wall collisions (pupils jump on impact)
- **Effect conflict resolution** - spin_out and drill cancel each other to prevent conflicts
- **REST API** - Flask server for external manipulation via HTTP

## Installation

### macOS

```bash
brew install cairo
pip install -r requirements.txt
```

### Windows

Cairo requires GTK runtime libraries on Windows:

1. Download GTK3 runtime installer from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
2. Run **gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe** (or latest version)
3. The installer handles PATH automatically
4. Restart your terminal and run:

```bash
pip install -r requirements.txt
```

**Alternative (using MSYS2):**
```bash
# In MSYS2 terminal
pacman -S mingw-w64-x86_64-cairo
pip install -r requirements.txt
```

### Linux (Debian/Ubuntu)

```bash
sudo apt-get install libcairo2-dev
pip install -r requirements.txt
```

### Linux (Fedora)

```bash
sudo dnf install cairo-devel
pip install -r requirements.txt
```

## Usage

```bash
# Fullscreen (default)
python claude_screensaver.py

# Windowed mode (for testing)
python claude_screensaver.py --windowed

# Custom API port (default: 9099)
python claude_screensaver.py --port 8080
```

Press **ESC** or **Q** to quit.

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/status` | Current star state (position, rotation, effects, etc.) |
| POST | `/api/manipulate_star` | Apply manipulation effect |
| POST | `/api/reset` | Reset to default state |

### Manipulation Actions

| Action | Duration | Description |
|--------|----------|-------------|
| `shrink` | 15s | Shrink star to 20% size |
| `spin_out` | ~5s | Ramp rotation speed over 2s, then gradual decay |
| `drill` | 3s | Stationary rapid spin (10 deg/frame) |
| `corner_trap` | 10s | Lock to nearest corner with jitter effect |
| `color` | 15s | Change star color (param: `color`) |
| `opacity` | 15s | Change transparency (param: `opacity`) |
| `googly_eyes` | Toggle | Enable/disable googly eyes (param: `enabled`) |
| `reset` | Instant | Reset all effects to default |

### Examples

```bash
# Enable googly eyes
curl -X POST http://localhost:9099/api/manipulate_star \
  -H "Content-Type: application/json" \
  -d '{"action": "googly_eyes", "parameters": {"enabled": true}}'

# Shrink the star
curl -X POST http://localhost:9099/api/manipulate_star \
  -H "Content-Type: application/json" \
  -d '{"action": "shrink"}'

# Spin out effect
curl -X POST http://localhost:9099/api/manipulate_star \
  -H "Content-Type: application/json" \
  -d '{"action": "spin_out"}'

# Drill (stationary spin)
curl -X POST http://localhost:9099/api/manipulate_star \
  -H "Content-Type: application/json" \
  -d '{"action": "drill"}'

# Corner trap
curl -X POST http://localhost:9099/api/manipulate_star \
  -H "Content-Type: application/json" \
  -d '{"action": "corner_trap"}'

# Change color to red
curl -X POST http://localhost:9099/api/manipulate_star \
  -H "Content-Type: application/json" \
  -d '{"action": "color", "parameters": {"color": "#ff0000"}}'

# Set opacity to 50%
curl -X POST http://localhost:9099/api/manipulate_star \
  -H "Content-Type: application/json" \
  -d '{"action": "opacity", "parameters": {"opacity": 0.5}}'

# Ghost combo (white + transparent + eyes + tiny)
curl -X POST http://localhost:9099/api/manipulate_star -H "Content-Type: application/json" -d '{"action": "color", "parameters": {"color": "#ffffff"}}'
curl -X POST http://localhost:9099/api/manipulate_star -H "Content-Type: application/json" -d '{"action": "opacity", "parameters": {"opacity": 0.5}}'
curl -X POST http://localhost:9099/api/manipulate_star -H "Content-Type: application/json" -d '{"action": "googly_eyes", "parameters": {"enabled": true}}'
curl -X POST http://localhost:9099/api/manipulate_star -H "Content-Type: application/json" -d '{"action": "shrink"}'

# Reset everything
curl -X POST http://localhost:9099/api/reset
```

### Status Response

```json
{
  "position": {"x": 640.0, "y": 360.0},
  "velocity": {"vx": 0.5, "vy": 0.5},
  "scale": 1.0,
  "rotation": 45.0,
  "rotation_speed": 0.5,
  "color": "#c04015",
  "opacity": 1.0,
  "effect_active": null,
  "corner_trapped": false,
  "eyes_enabled": false,
  "heartbeat_pulse": 0.0,
  "wall_impact": 0.0,
  "display_size": {"width": 1280, "height": 720}
}
```

## Technical Details

### Animation Constants

- **Target FPS**: 60
- **Base star size**: 240px
- **Default color**: `#c04015` (Claude orange)
- **Default velocity**: 0.5 px/frame (x and y)
- **Default rotation**: 0.5 deg/frame

### Heartbeat Cycle (4 seconds)

- **0-12.5%**: Main QRS beat (sine wave pulse)
- **12.5-20%**: T-wave echo (25% amplitude)
- **20-100%**: Rest period

### Eye Physics

- **Gravity**: 0.008 (pulls pupils down in local space)
- **Friction**: 0.96 (damping factor)
- **Spin threshold**: 2.0 deg/frame (centrifugal force activates above this)
- **Heartbeat kick**: 0.0069 (subtle upward nudge during pulse)
- **Wall impact**: 0.02 initial, decays at 0.85/frame

## License

MIT
