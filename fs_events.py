"""v1.0.5.3 SEASONAL EVENTS + live feed.
- 4 seasons rotate by real calendar week (ISO week % 4): SPRING -> SUMMER -> AUTUMN -> WINTER.
- each season: 3 events (a race, a photo challenge, a drive-to / collect), each with a map marker and a reward (yen or a car paint).
- a sliding notification feed (top-right) shows event cards and small notices (New car unlocked / Event completed / Skill chain).
- works offline from the date; optionally reads events.json from GitHub main (Teobokki/fireout-shine) so new events arrive without a
  rebuild, with a fallback to the built-in events.  Light seasonal look: sakura petals, autumn leaves, snow (alpha-blended, no glow)."""
import json, math, random, threading, time, datetime, urllib.request
from panda3d.core import CardMaker, NodePath, TextNode, TransparencyAttrib
from direct.gui.DirectGui import DirectFrame, DGG
import fs_ui as U

REMOTE = "https://raw.githubusercontent.com/Teobokki/fireout-shine/main/events.json"
SEASONS = ["spring", "summer", "autumn", "winter"]
SNAME = {"spring": "SPRING", "summer": "SUMMER", "autumn": "AUTUMN", "winter": "WINTER"}
SCOL = {"spring": (1.0, 0.62, 0.78, 1), "summer": (0.35, 0.85, 1.0, 1), "autumn": (1.0, 0.55, 0.18, 1), "winter": (0.80, 0.90, 1.0, 1)}
ICON = {"race": "R", "photo": "P", "drive": "D", "collect": "C"}

# built-in events (targets are snapped to the nearest road at runtime). tlimit: race time limit (s)
BUILTIN = {
    "spring": {"title": "SPRING SAKURA FESTIVAL", "events": [
        {"id": "sp_drive", "kind": "drive", "title": "SAKURA FESTIVAL", "line": "Drive to Hanami Park under the cherry blossoms", "x": 300, "y": -220, "reward": {"yen": 6000}},
        {"id": "sp_photo", "kind": "photo", "title": "HANAMI PHOTO", "line": "Take a phone photo at the Shinko Tower plaza", "x": 0, "y": 0, "tower": True, "reward": {"paint": "SAKURA PEARL", "col": [0.98, 0.62, 0.74]}},
        {"id": "sp_race", "kind": "race", "title": "PETAL SPRINT", "line": "Reach the beach road in under 75 s", "x": 520, "y": -80, "start": [436, -300], "tlimit": 75, "reward": {"yen": 12000}}]},
    "summer": {"title": "SUMMER NIGHT RACE", "events": [
        {"id": "su_race", "kind": "race", "title": "SUMMER NIGHT RACE", "line": "Downtown to Hikari Beach in under 90 s", "x": 540, "y": -60, "start": [40, -40], "tlimit": 90, "reward": {"yen": 15000}},
        {"id": "su_photo", "kind": "photo", "title": "FIREWORKS PHOTO", "line": "Snap a photo at Hikari Beach", "x": 560, "y": -40, "reward": {"paint": "MATSURI BLUE", "col": [0.05, 0.30, 0.85]}},
        {"id": "su_collect", "kind": "collect", "title": "FESTIVAL LANTERNS", "line": "Collect 5 lanterns around the crossing", "x": 20, "y": 30, "n": 5, "reward": {"yen": 8000}}]},
    "autumn": {"title": "AUTUMN MOMIJI DRIFT", "events": [
        {"id": "au_drive", "kind": "drive", "title": "MOMIJI DRIVE", "line": "Drive up to the stadium boulevard", "x": 503, "y": 232, "reward": {"yen": 6000}},
        {"id": "au_collect", "kind": "collect", "title": "MOMIJI LEAVES", "line": "Collect 5 red leaves in the Sakura district", "x": 360, "y": -250, "n": 5, "reward": {"paint": "MOMIJI RED", "col": [0.72, 0.10, 0.04]}},
        {"id": "au_race", "kind": "race", "title": "AUTUMN MOMIJI DRIFT", "line": "Hospital to the tower in under 70 s", "x": 0, "y": 0, "tower": True, "start": [-150, 100], "tlimit": 70, "reward": {"yen": 14000}}]},
    "winter": {"title": "WINTER SNOW RUN", "events": [
        {"id": "wi_race", "kind": "race", "title": "WINTER SNOW RUN", "line": "Home to the stadium in under 95 s", "x": 503, "y": 232, "start": [436, -300], "tlimit": 95, "reward": {"yen": 16000}},
        {"id": "wi_photo", "kind": "photo", "title": "ILLUMINATION PHOTO", "line": "Take a photo at the Shinko Tower", "x": 0, "y": 0, "tower": True, "reward": {"paint": "FROST WHITE", "col": [0.92, 0.94, 0.98]}},
        {"id": "wi_drive", "kind": "drive", "title": "HOT SPRING TRIP", "line": "Drive to the hospital hill road", "x": -150, "y": 100, "reward": {"yen": 7000}}]},
}


def season_now(now=None):
    d = (now or datetime.datetime.now()).date()
    wk = d.isocalendar()[1]; yr = d.isocalendar()[0]
    idx = (yr * 53 + wk) % 4
    nxt = d + datetime.timedelta(days=7 - d.weekday())           # next Monday 00:00 = next season
    start = nxt - datetime.timedelta(days=7)
    return SEASONS[idx], datetime.datetime.combine(start, datetime.time()), datetime.datetime.combine(nxt, datetime.time())


def valid(data):
    try:
        for s in SEASONS:
            ev = data[s]["events"]
            if not (1 <= len(ev) <= 6): return False
            for e in ev:
                if e["kind"] not in ICON or not isinstance(e["title"], str) or not isinstance(e["reward"], dict): return False
                float(e["x"]); float(e["y"])
        return True
    except Exception:
        return False


class Feed:
    """sliding notification cards in the top-right corner."""
    def __init__(self, g):
        self.g = g; self.cards = []; self.queue = []
        self.root = DirectFrame(parent=g.app.a2dTopLeft, frameColor=(0, 0, 0, 0), pos=(0, 0, 0))     # left column, under the portraits (minimap stays clear)

    def push(self, title, line="", reward="", icon="!", col=(1, 1, 1, 1), small=False):
        self.queue.append((title, line, reward, icon, col, small))

    def _make(self, title, line, reward, icon, col, small):
        h = 0.065 if small else 0.115; w = 0.58
        outer = DirectFrame(parent=self.root, frameColor=(0, 0, 0, 0), relief=DGG.FLAT)
        f = DirectFrame(parent=outer, frameColor=(0.04, 0.04, 0.06, 0.88), frameSize=(-w, 0, -h, 0), relief=DGG.FLAT); f.set_x(w)
        DirectFrame(parent=f, frameColor=col, frameSize=(-w, -w + 0.012, -h, 0), relief=DGG.FLAT)
        ic = DirectFrame(parent=f, frameColor=(col[0] * 0.35, col[1] * 0.35, col[2] * 0.35, 1), frameSize=(-w + 0.03, -w + 0.03 + h - 0.03, -h + 0.015, -0.015), relief=DGG.FLAT)
        U.text(f, icon, (-w + 0.015 + h / 2, -h / 2 - 0.018), 0.05 if not small else 0.032, fg=col)
        x0 = -w + h + 0.03
        U.text(f, title, (x0, -0.042 if not small else -0.04), 0.034 if not small else 0.028, fg=col, align=TextNode.A_left)
        if line and not small: U.text(f, line, (x0, -0.072), 0.024, font=U.FONT_PLAIN, align=TextNode.A_left, wrap=19)
        if reward: U.text(f, reward, (-0.02, -0.042 if not small else -0.04), 0.026, fg=U.GOLD, align=TextNode.A_right, font=U.FONT_PLAIN)
        return {"f": outer, "h": h, "t": 0.0, "dur": 3.2 if small else 5.5, "x": -0.7}

    def update(self, dt):
        if self.queue and len(self.cards) < 4:
            self.cards.append(self._make(*self.queue.pop(0)))
        y = -0.42
        for c in list(self.cards):
            c["t"] += dt
            tgt = 0.03 if c["t"] < c["dur"] else -0.75
            c["x"] += (tgt - c["x"]) * min(1.0, dt * 9.0)
            c["f"].set_pos(c["x"], 0, y); y -= c["h"] + 0.015
            if c["t"] > c["dur"] + 0.6:
                c["f"].destroy(); self.cards.remove(c)

    def destroy(self):
        self.root.destroy()


class Particles:
    """light seasonal look around the camera: sakura petals / autumn leaves / snow. alpha-blended, never additive."""
    def __init__(self, g, season):
        self.g = g; app = g.app; self.np = app.render.attach_new_node("season-fx"); self.parts = []
        col = {"spring": (1.0, 0.72, 0.82, 0.9), "autumn": (0.85, 0.32, 0.08, 0.95), "winter": (0.95, 0.97, 1.0, 0.85)}.get(season)
        if col is None: return
        tex = self.shape_tex(season)
        cm = CardMaker("p"); s = 0.035 if season == "winter" else 0.05; cm.set_frame(-s, s, -s, s)
        for _ in range(70):         # v1.0.5.3: fewer, smaller, soft-edged leaf/petal/flake shapes (were hard squares)
            q = self.np.attach_new_node(cm.generate()); q.set_texture(tex)
            q.set_color(col[0] * random.uniform(0.8, 1.0), col[1] * random.uniform(0.8, 1.0), col[2], col[3] * random.uniform(0.6, 0.9))
            q.set_two_sided(True); self.parts.append([q, random.uniform(-18, 18), random.uniform(-18, 18), random.uniform(0, 14), random.uniform(0, 6.28), random.uniform(0.6, 1.4)])
        self.np.set_transparency(TransparencyAttrib.M_alpha); self.np.set_light_off(); self.np.set_shader_off(1); self.np.set_depth_write(False); self.np.set_bin("fixed", 40)
        self.fall = 1.6 if season == "winter" else 0.9

    @staticmethod
    def shape_tex(season, n=64):
        from panda3d.core import PNMImage, Texture
        im = PNMImage(n, n, 4); im.fill(1, 1, 1); im.alpha_fill(0)
        for j in range(n):
            for i in range(n):
                u, v = (i + 0.5) / n * 2 - 1, (j + 0.5) / n * 2 - 1
                if season == "winter":
                    d = math.hypot(u, v); a = max(0.0, 1 - d) ** 1.5                         # soft round flake
                else:
                    w = 0.5 * (1 - v * v) * (0.75 if season == "autumn" else 1.0)          # almond leaf / petal
                    if season == "spring" and v > 0.75: w *= max(0.0, 1 - 6 * (0.06 - abs(u)) if abs(u) < 0.06 else 1)   # petal notch
                    d = abs(u) / max(w, 1e-3); a = max(0.0, min(1.0, (1 - d) * 6)) if abs(v) < 1 else 0
                    if season == "autumn" and abs(u) < 0.03: a *= 0.6                        # leaf vein
                im.set_alpha(i, j, a)
        t = Texture("season-shape"); t.load(im); t.set_wrap_u(Texture.WM_clamp); t.set_wrap_v(Texture.WM_clamp)
        t.set_minfilter(Texture.FT_linear_mipmap_linear); return t

    def update(self, dt, t):
        if not self.parts: return
        cam = self.g.app.camera.get_pos(self.g.app.render)
        for p in self.parts:
            q, x, y, z, ph, sp = p
            z -= dt * self.fall * sp; ph += dt * 1.7
            if z < -1.5: z = 14.0; x = random.uniform(-20, 20); y = random.uniform(-20, 20)
            p[3] = z; p[4] = ph
            q.set_pos(cam[0] + x + math.sin(ph) * 0.6, cam[1] + y + math.cos(ph * 0.7) * 0.5, max(0.05, cam[2] - 3 + z))
            q.set_hpr(ph * 60, ph * 40, ph * 25)

    def destroy(self):
        self.np.remove_node()


class Events:
    def __init__(self, g, saved=None):
        self.g = g; self.data = BUILTIN; self.source = "built-in"
        self.done = dict(saved.get("done", {})) if isinstance(saved, dict) else {}
        self.paints = list(saved.get("paints", [])) if isinstance(saved, dict) else []
        self.feed = Feed(g); self.active = None; self.tokens = []; self.mk = g.app.render.attach_new_node("event-markers")
        self.season, self.s0, self.s1 = season_now(); self.fx = Particles(g, self.season)
        self.chain = 0; self.chain_t = 0.0; self._drift_t = 0.0
        self.build_markers()
        self.feed.push("Season: %s" % SNAME[self.season], self.data[self.season]["title"] + " is live", "", "*", SCOL[self.season])
        for e in self.events(): 
            if not self.is_done(e): self.feed.push(e["title"], e["line"], self.reward_txt(e), ICON[e["kind"]], SCOL[self.season]); break
        threading.Thread(target=self._fetch, daemon=True).start()

    # ---------------------------------------------------------------- data
    def _fetch(self):
        try:
            req = urllib.request.Request(REMOTE + "?t=%d" % int(time.time() // 600), headers={"User-Agent": "FIREOUT-SHINE"})
            d = json.loads(urllib.request.urlopen(req, timeout=6).read().decode("utf-8"))
            if valid(d): self._remote = d
        except Exception:
            pass

    def events(self):
        return self.data[self.season]["events"]

    def key(self, e):
        return "%s:%s" % (self.s0.strftime("%Y%m%d"), e["id"])

    def is_done(self, e):
        return bool(self.done.get(self.key(e)))

    @staticmethod
    def reward_txt(e):
        r = e["reward"]
        return ("\u00a5%s" % format(int(r["yen"]), ",")) if "yen" in r else ("PAINT: %s" % r.get("paint", "NEW"))

    def target(self, e):
        x, y = float(e["x"]), float(e["y"])
        if e.get("tower"):
            try:
                tx, ty, _ = self.g.world.tower_top; x, y = tx, ty - 26
            except Exception: pass
        try:
            rx, ry = self.g.world.nearest_road_point(x, y)[:2]; return rx, ry
        except Exception:
            return x, y

    # ---------------------------------------------------------------- markers (flat solid ring + label, no glow beams)
    def build_markers(self):
        for ch in self.mk.get_children(): ch.remove_node()
        self.tokens = []
        for e in self.events():
            if self.is_done(e): continue
            x, y = self.target(e) if e["kind"] != "race" else self._road(*e["start"])
            n = self.mk.attach_new_node("ev"); n.set_pos(x, y, 0.06)
            col = SCOL[self.season]
            seg = 40
            from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomTriangles, Geom, GeomNode
            vd = GeomVertexData("r", GeomVertexFormat.get_v3c4(), Geom.UH_static); vw = GeomVertexWriter(vd, "vertex"); cw = GeomVertexWriter(vd, "color")
            tri = GeomTriangles(Geom.UH_static)
            for k in range(seg + 1):
                a = k / seg * 6.2832
                for rr in (4.6, 5.4):
                    vw.add_data3(math.cos(a) * rr, math.sin(a) * rr, 0); cw.add_data4(col[0], col[1], col[2], 0.85)
                if k < seg:
                    i = k * 2; tri.add_vertices(i, i + 1, i + 3); tri.add_vertices(i, i + 3, i + 2)
            gm = Geom(vd); gm.add_primitive(tri); gn = GeomNode("ring"); gn.add_geom(gm); n.attach_new_node(gn)
            tn = TextNode("lbl"); tn.set_text("%s  [%s]" % (e["title"], self.reward_txt(e))); tn.set_align(TextNode.A_center)
            if U.FONT: tn.set_font(U.FONT)
            tn.set_text_color(col); tn.set_shadow(0.05, 0.05); tn.set_shadow_color(0, 0, 0, 0.8)
            t = n.attach_new_node(tn); t.set_z(4.2); t.set_scale(1.1); t.set_billboard_point_eye()
            e["_np"] = n
        self.mk.set_transparency(TransparencyAttrib.M_alpha); self.mk.set_light_off(); self.mk.set_shader_off(1); self.mk.set_two_sided(True)
        self.mk.set_depth_offset(2)

    def _road(self, x, y):
        try: return self.g.world.nearest_road_point(x, y)[:2]
        except Exception: return x, y

    def map_points(self):
        """(x, y, col, label) for the minimap / big map"""
        out = []
        for e in self.events():
            if self.is_done(e): continue
            x, y = self.target(e) if e["kind"] != "race" else self._road(*e["start"])
            out.append((x, y, SCOL[self.season], ICON[e["kind"]]))
        return out

    # ---------------------------------------------------------------- progress
    def complete(self, e):
        if self.is_done(e): return
        self.done[self.key(e)] = True; g = self.g; r = e["reward"]
        if "yen" in r:
            try: g.add_cash(int(r["yen"]))
            except Exception: g.cash = g.cash + int(r["yen"])
        else:
            nm = r.get("paint", "EVENT PAINT"); col = tuple(r.get("col", (1, 1, 1)))[:3]
            if nm not in [p[0] for p in self.paints]: self.paints.append([nm, list(col)])
            self.feed.push("New paint unlocked", nm + " (FRGARAGE)", "", "+", (1, 1, 1, 1), small=True)
        self.feed.push("Event completed", e["title"], self.reward_txt(e), "\u2713", U.GOLD)
        g.app.sfx("checkpoint", 0.6)
        if "_np" in e: e["_np"].remove_node(); del e["_np"]
        for t in self.tokens: t.remove_node()
        self.tokens = []; self.active = None
        if all(self.is_done(x) for x in self.events()):
            self.feed.push("Season complete!", SNAME[self.season] + " festival finished", "", "*", SCOL[self.season])
        try: g.save()
        except Exception: pass

    def notify(self, title, line="", small=True):
        self.feed.push(title, line, "", "!", (1, 1, 1, 1), small=small)

    def update(self, dt):
        g = self.g
        self.feed.update(dt); self.fx.update(dt, g.time)
        if getattr(self, "_remote", None) is not None:            # new events from GitHub main (no rebuild)
            d = self._remote; self._remote = None
            if json.dumps(d, sort_keys=True) != json.dumps(self.data, sort_keys=True, default=str):
                self.data = d; self.source = "online"; self.build_markers()
                self.notify("Festival updated", "New seasonal events from HQ")
        s, s0, s1 = season_now()
        if s != self.season:
            self.season, self.s0, self.s1 = s, s0, s1; self.fx.destroy(); self.fx = Particles(g, s); self.build_markers()
            self.feed.push("Season: %s" % SNAME[s], self.data[s]["title"] + " is live", "", "*", SCOL[s])
        if g.blocked() and not getattr(g, "camapp", None): return
        px, py = g.player_pos(); c = g.pcar
        # skill chain: consecutive drifts
        if c is not None and c.drift > 7 and c.speed > 12:
            self._drift_t += dt
            if self._drift_t > 1.2:
                self._drift_t = 0.0; self.chain += 1; self.chain_t = 3.0
                if self.chain >= 2: self.feed.push("Skill chain x%d" % self.chain, "", "+%d" % (self.chain * 50), "~", U.PINK, small=True)
        else:
            self._drift_t = 0.0
        self.chain_t -= dt
        if self.chain_t <= 0: self.chain = 0
        for e in self.events():
            if self.is_done(e): continue
            k = e["kind"]
            if k == "race":
                sx, sy = self._road(*e["start"])
                if self.active is None and c is not None and math.hypot(px - sx, py - sy) < 6:
                    self.active = {"e": e, "t": float(e.get("tlimit", 90))}
                    self.feed.push(e["title"], "GO! Reach the finish in %d s" % int(e.get("tlimit", 90)), "", "R", SCOL[self.season])
                    g.waypoint = self.target(e)
            elif k in ("drive",) and c is not None:
                tx, ty = self.target(e)
                if math.hypot(px - tx, py - ty) < 7: self.complete(e); return
            elif k == "photo":
                tx, ty = self.target(e)
                if getattr(g, "camapp", None) and math.hypot(px - tx, py - ty) < 14 and getattr(g, "_ev_photo", 0) > 0:
                    self.complete(e); return
            elif k == "collect":
                tx, ty = self.target(e)
                if not self.tokens and math.hypot(px - tx, py - ty) < 90 and (self.active is None or self.active["e"] is e):
                    self.spawn_tokens(e, tx, ty); self.active = {"e": e, "t": None, "got": 0}
                for t in list(self.tokens):
                    q = t.get_pos(g.app.render)
                    t.set_h(g.time * 90 % 360)
                    if math.hypot(px - q[0], py - q[1]) < 3.0:
                        t.remove_node(); self.tokens.remove(t); self.active["got"] += 1
                        self.feed.push("%s %d/%d" % (e["title"], self.active["got"], e.get("n", 5)), "", "", "C", SCOL[self.season], small=True)
                        if not self.tokens: self.complete(e); return
        g._ev_photo = 0
        a = self.active
        if a is not None and a.get("t") is not None:
            a["t"] -= dt; e = a["e"]; tx, ty = self.target(e)
            g.big.setText("%d" % max(0, math.ceil(a["t"]))) if a["t"] < 10 else None
            if c is not None and math.hypot(px - tx, py - ty) < 8:
                g.big.setText(""); self.complete(e)
            elif a["t"] <= 0:
                g.big.setText(""); self.active = None; self.feed.push("Event failed", e["title"] + " - try again", "", "x", (1, 0.4, 0.4, 1), small=True)

    def spawn_tokens(self, e, tx, ty):
        col = SCOL[self.season]; n = int(e.get("n", 5))
        cm = CardMaker("tok"); cm.set_frame(-0.6, 0.6, -0.6, 0.6)
        for k in range(n):
            a = k / n * 6.2832 + 0.4; r = 18 + 10 * (k % 2)
            x, y = self._road(tx + math.cos(a) * r, ty + math.sin(a) * r)
            q = self.mk.attach_new_node(cm.generate()); q.set_pos(x, y, 1.3); q.set_color(col[0], col[1], col[2], 0.95); q.set_two_sided(True)
            self.tokens.append(q)

    def photo_taken(self):
        self.g._ev_photo = 1.0

    def save(self):
        keep = {k: v for k, v in self.done.items() if k[:8] >= (self.s0 - datetime.timedelta(days=35)).strftime("%Y%m%d")}
        return {"done": keep, "paints": self.paints}

    # ---------------------------------------------------------------- phone page
    def page(self, root, cx, top, btn, W):
        s = self.season; col = SCOL[s]
        W("FESTIVAL", 0.29, 0.05, fg=col, font=U.FONT)
        W("Season: %s  -  %s" % (SNAME[s], self.data[s]["title"]), 0.345, 0.024, fg=col)
        now = datetime.datetime.now(); tot = (self.s1 - self.s0).total_seconds(); left = max(0, (self.s1 - now).total_seconds())
        done = sum(1 for e in self.events() if self.is_done(e)); n = len(self.events())
        bw = 0.22
        DirectFrame(parent=root, frameColor=(0.2, 0.2, 0.25, 1), frameSize=(cx - bw, cx + bw, top - 0.395, top - 0.38), relief=DGG.FLAT)
        DirectFrame(parent=root, frameColor=col, frameSize=(cx - bw, cx - bw + 2 * bw * done / max(1, n), top - 0.395, top - 0.38), relief=DGG.FLAT)
        W("%d/%d events   next season in %dd %02dh %02dm" % (done, n, left // 86400, (left % 86400) // 3600, (left % 3600) // 60), 0.425, 0.021)
        y = 0.47
        for e in self.events():
            st = "DONE" if self.is_done(e) else self.reward_txt(e)
            W("[%s] %s  -  %s" % (ICON[e["kind"]], e["title"], st), y, 0.022, fg=(0.6, 0.6, 0.6, 1) if self.is_done(e) else (1, 1, 1, 1))
            W(e["line"], y + 0.03, 0.017, wrap=22)
            if not self.is_done(e):
                tgt = self.target(e) if e["kind"] != "race" else self._road(*e["start"])
                btn("GO", (lambda t=tgt: (setattr(self.g, "waypoint", t), self.g.toast("Waypoint set"))), y + 0.065, w=0.05)
            y += 0.115
        W("events: %s" % self.source, 0.8, 0.016, fg=(1, 1, 1, 0.5))

    def destroy(self):
        self.feed.destroy(); self.fx.destroy(); self.mk.remove_node()
