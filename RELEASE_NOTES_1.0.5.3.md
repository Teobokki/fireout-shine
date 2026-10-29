# FIREOUT SHINE 1.0.5.3

**Bumper jump fixed.** The jump came from the body pitch. It used to be set straight from the throttle key (±1.2°, and only above 1 m/s), so every key press or release, every AI throttle flip and every stop snapped the car about 5 cm at the bumper in one frame. Braking also tilted the nose the wrong way, up instead of down. The number plates sat on the car root, so they slid against the bumper. Now pitch and roll come from the car's real acceleration through a damped, rate-limited spring: the nose dips when braking and squats when accelerating. The plates move with the body. Per-frame bumper movement dropped from 10 cm to 1.7 cm (smooth), and plate slip dropped from 10 cm to 0.4 mm.

**Controls fix:** A now steers left and D right, with the arrow keys and gamepad stick fixed the same way. The input sign was inverted against the car model.

**ENERASTIC MG EVO SEDAN** is the new default and recommended car, and the FRGARAGE hero. It is parked in Ana and Daniel's carport, ready to drive. It is an original low 4-door fastback: candy-red clearcoat paint, slim swept-back LED headlight units with an icy-blue LED strip along the top edge and twin projector lenses, separate C-shaped LED daytime running lights low in the bumper corners, a vertical-slat grille with an original E badge, splitter, side skirts, rear wing, chrome window line, 10-spoke alloys on low-profile tyres, brake discs and calipers, a visible interior and real wheel arches. There is no underglow.

**Every car was rebuilt** with LED light strips, multi-spoke wheels with discs and calipers, lower stances, glossy clearcoat paint, see-through tinted glass with interiors, round wheel arches and bumpers built into the body. A body-mesh bug that caved in the left-hand side of every car (you could see the seats and passengers through the lower doors) is fixed. Number plates render properly again. Traffic uses LOD models and has more variety in models and colours.

**Graphics modes: RTX and EX HD.** The mode is auto-detected on first launch: NVIDIA RTX, AMD RX 6000 or newer, and Intel Arc get RTX; everything else gets EX HD. You can switch in Settings.
- **Both modes look almost the same:** the same models, textures, car paint, lights, live car reflections, city detail and cinematic colour grade (filmic curve, subtle split toning), vignette, film grain, height haze, 4x MSAA, a 24-bit depth buffer with a tighter near/far range, and mipmaps.
- **EX HD only trims small, hard-to-notice costs:** a 128 px reflection cube-map refreshed every second frame (RTX: 256 px every frame), 8x instead of 16x anisotropic filtering, road light pools on far-away cars culled a little earlier, a slightly shorter traffic detail distance and about 8% less distant traffic.

There is no bloom and no glow halos. Car lights now cast light onto the road instead of halo sprites.

**Seasonal FESTIVAL.**
- The season rotates every calendar week: Spring Sakura Festival, Summer Night Race, Autumn Momiji Drift, Winter Snow Run.
- Each season has 3 events (a race, a photo challenge, and a drive-to or collect), with map markers and yen or paint rewards.
- A live feed shows event cards, plus "New car unlocked", "Event completed" and "Skill chain".
- A FESTIVAL phone app shows a progress bar and a countdown to the next season.
- New events can arrive from events.json on GitHub, with built-in events as the fallback.
- Light seasonal particles: soft petals, leaves and snowflakes.

**City:** realistic vending machines, parked bicycles, bollards and A-frame shop boards.

Per-user install, no admin. ©2026 EX Inc./HYPERION DIGITAL ©2026
