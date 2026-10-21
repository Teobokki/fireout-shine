"""On-foot characters: ANA & DANIEL (playable duo) and pedestrians (same v2 skin texture set, varied outfits)."""
import math, os, random
from panda3d.core import NodePath, Filename, TextNode, SamplerState
import fs_shaders

_models = {}
PED_TOPS = [(0.85, 0.85, 0.88), (0.12, 0.12, 0.14), (0.75, 0.2, 0.3), (0.2, 0.45, 0.7), (0.9, 0.7, 0.2), (0.3, 0.6, 0.4), (0.6, 0.4, 0.75)]
PED_BOTTOMS = [(0.1, 0.12, 0.25), (0.15, 0.15, 0.16), (0.55, 0.5, 0.42), (0.6, 0.08, 0.08), (0.85, 0.82, 0.75), (0.25, 0.3, 0.2)]
PED_HAIR = [(1, 1, 1), (0.6, 0.6, 0.6), (2.2, 1.6, 1.1), (3.0, 2.6, 1.8), (1.6, 0.8, 0.5), (0.4, 0.4, 0.45)]


OUTFITS = [("default", "DEFAULT", "Tank top, red slacks, sneakers"), ("crop", "CROP TOP", "White fitted crop top, red slacks, sneakers"), ("bikini", "BIKINI", "Coral two-piece swimsuit, flip-flops"),
           ("police", "POLICE", "TOKYO NEON PD uniform: shirt, cap, badge, boots")]
def load(app, who, outfit="default"):
    key = who if outfit == "default" else who + "_" + outfit
    if key not in _models:
        fn = ("daniel" if who == "daniel" else "heroine") + ("" if outfit == "default" else "_" + outfit) + ".bam"
        p = os.path.join(app.BASE, "assets", "models", fn)
        if not os.path.exists(p): p = os.path.join(app.BASE, "assets", "models", "heroine.bam" if who != "daniel" else "daniel.bam"); outfit = "default"
        if who == "daniel" and not os.path.exists(p):
            p = os.path.join(app.BASE, "assets", "models", "heroine.bam")
        m = app.loader.load_model(Filename.from_os_specific(p)); fix_uv(m); _models[key] = m
    return _models[key].copy_to(NodePath(who))


def fix_uv(m):
    """glTF exports the UV set as 'texcoord.0'; rename it to the default 'texcoord' so the shader's p3d_MultiTexCoord0 sees it."""
    from panda3d.core import GeomVertexFormat, GeomVertexArrayFormat, InternalName
    src = InternalName.make("texcoord.0"); dst = InternalName.get_texcoord()
    for gn in m.find_all_matches("**/+GeomNode"):
        node = gn.node()
        for i in range(node.get_num_geoms()):
            g = node.modify_geom(i); vd = g.modify_vertex_data(); fmt = vd.get_format()
            if not fmt.has_column(src): continue
            nf = GeomVertexFormat(fmt)
            for a in range(nf.get_num_arrays()):
                arr = nf.modify_array(a)
                if arr.has_column(src):
                    c = arr.get_column(src)
                    nc, nt, ct, st = c.get_num_components(), c.get_numeric_type(), c.get_contents(), c.get_start()
                    arr.remove_column(src); arr.add_column(dst, nc, nt, ct, st)
            vd.unclean_set_format(GeomVertexFormat.register_format(nf))


def tex(app, name):
    t = app.loader.load_texture(Filename.from_os_specific(os.path.join(app.BASE, "assets", "tex", name)))
    t.set_minfilter(SamplerState.FT_linear_mipmap_linear)
    return t


class Person:
    def __init__(self, game, who="ana", x=0.0, y=0.0, h=0.0, ped=False):
        self.g = game; app = game.app; self.app = app; self.who = who
        self.x, self.y, self.h = x, y, h
        self.vx = self.vy = 0.0
        self.phase = 0.0; self.knock = 0.0; self.health = 100.0; self.in_car = None; self.hidden = False
        self.np = app.render.attach_new_node("person"); self.ped = ped
        self.outfit = getattr(game, "outfit", "default") if who == "ana" and not ped else "default"
        if who == "ana" and self.outfit != "default" and not os.path.exists(os.path.join(app.BASE, "assets", "models", "heroine_%s.bam" % self.outfit)): self.outfit = "default"
        self.build_model()
        self.np.set_pos(x, y, 0.0); self.np.set_h(h)

    def set_outfit(self, outfit):
        if outfit == self.outfit: return
        self.outfit = outfit; self.model.remove_node(); self.build_model()

    def build_model(self):
        app = self.app; who = self.who; ped = self.ped
        base = "daniel" if who == "daniel" else "ana"
        m = load(app, base, self.outfit); m.reparent_to(self.np); m.set_h(180); self.model = m
        suf = "_daniel" if base == "daniel" and os.path.exists(os.path.join(app.BASE, "assets", "tex", "skin_c_daniel.png")) else ""
        if self.outfit != "default" and os.path.exists(os.path.join(app.BASE, "assets", "tex", "skin_c_%s.png" % self.outfit)):
            suf = "_" + self.outfit
        fs_shaders.apply(m, app, gloss=0.15, sheen=0.4)
        sk = m.find("**/skin")
        if not sk.is_empty():
            sk.set_texture(tex(app, "skin_c%s.png" % suf), 1)
            fs_shaders.apply(sk, app, gloss=0.22, tex=True, nmap=tex(app, "skin_n%s.png" % suf), sheen=0.8)
        ey = m.find("**/eyes")
        if not ey.is_empty():
            ey.set_texture(tex(app, "eye_c%s.png" % suf), 1); fs_shaders.apply(ey, app, gloss=0.9, tex=True)
        sh = m.find("**/tank")
        if base == "daniel" and not sh.is_empty():
            sh.set_texture(tex(app, "floral.png"), 1); fs_shaders.apply(sh, app, gloss=0.1, tex=True, sheen=0.5)
        hr = m.find("**/hair")
        if not hr.is_empty():
            fs_shaders.apply(hr, app, gloss=0.35, sheen=0.3); hr.set_two_sided(True)
            hr.set_transparency(0); hr.set_depth_write(True); hr.set_depth_offset(2); hr.set_bin("opaque", 5)
        self.legL = m.find("**/legL"); self.legR = m.find("**/legR")
        if self.outfit in ("bikini", "swim"):   # bare legs carry the baked skin; flip-flops keep their own material
            for lg in (self.legL, self.legR):
                if lg.is_empty(): continue
                lg.set_texture(tex(app, "skin_c%s.png" % suf), 1)
                fs_shaders.apply(lg, app, gloss=0.22, tex=True, nmap=tex(app, "skin_n%s.png" % suf), sheen=0.8)
                for ff in lg.find_all_matches("**/ff*"): fs_shaders.apply(ff, app, gloss=0.2, sheen=0.3)
        if self.outfit == "police":
            bd = m.find("**/badge")
            if not bd.is_empty(): fs_shaders.apply(bd, app, gloss=0.9, sheen=0.0, emitboost=1.0)
        self.upper = [c for c in m.get_children() if c.get_name() not in ("legL", "legR")]
        if ped:
            rnd = random.Random()
            for nm, pal in (("tank", PED_TOPS), ("straps", None), ("trousers", PED_BOTTOMS), ("hair", PED_HAIR)):
                n = m.find("**/" + nm)
                if n.is_empty(): continue
                if nm == "straps":
                    n.set_shader_input("tint", self._top + (1,)); continue
                c = rnd.choice(pal)
                if nm == "tank": self._top = c
                n.set_shader_input("tint", c + (1,))
                if nm == "trousers":
                    for lg in (self.legL, self.legR):
                        if not lg.is_empty(): lg.set_shader_input("tint", c + (1,))
            sc = rnd.uniform(0.94, 1.04); m.set_scale(sc)

    def walk_anim(self, dt, speed):
        if self.knock > 0:
            return
        k = min(1.0, speed / 5.5)
        self.phase += dt * (4.5 + speed * 1.35)
        a = math.sin(self.phase) * (22 + 14 * k) * min(1.0, speed / 1.2)
        if not self.legL.is_empty(): self.legL.set_p(a)
        if not self.legR.is_empty(): self.legR.set_p(-a)
        bob = abs(math.sin(self.phase)) * 0.035 * min(1.0, speed / 1.5)
        self.model.set_z(bob); self.model.set_p(-k * 6)
        self.model.set_r(math.sin(self.phase) * 1.5 * min(1.0, speed / 2))

    def sync(self, z=0.0):
        self.np.set_pos(self.x, self.y, z + (0.15 if self.g.world.on_sidewalk(self.x, self.y) else 0.0)); self.np.set_h(self.h)

    def knock_down(self, dirx, diry, power):
        self.knock = 2.4
        self.vx += dirx * power; self.vy += diry * power
        self.model.set_p(80); self.model.set_z(0.25)

    def update_knock(self, dt):
        if self.knock > 0:
            self.knock -= dt
            self.x += self.vx * dt; self.y += self.vy * dt
            self.vx *= math.exp(-4 * dt); self.vy *= math.exp(-4 * dt)
            px, py, nx, ny, tag = self.g.world.grid.push_circle(self.x, self.y, 0.35)
            self.x += px; self.y += py
            if self.knock <= 0:
                self.model.set_p(0); self.model.set_z(0); self.vx = self.vy = 0
            return True
        return False

    def seat(self, car, side):
        """place the upper body in a car seat (legs hidden)."""
        self.in_car = car; self.np.reparent_to(car.np)
        sp = car.spec; z = min(-0.55, sp["roof"] - 1.82)
        self.np.set_pos(0.36 * side, -0.15 if car.kind not in ("van", "kei", "ambulance") else 0.9, z); self.np.set_h(0)
        for lg in (self.legL, self.legR):
            if not lg.is_empty(): lg.hide()
        self.model.set_p(0); self.model.set_z(0); self.model.set_r(0)

    def unseat(self, x, y, h):
        self.in_car = None; self.np.reparent_to(self.app.render)
        for lg in (self.legL, self.legR):
            if not lg.is_empty(): lg.show(); lg.set_p(0)
        self.x, self.y, self.h = x, y, h; self.sync()

    def destroy(self):
        self.np.remove_node()


class Ped(Person):
    """sidewalk walker: loops around a block, flees from danger, can speak ambient lines."""
    def __init__(self, game, loop, idx):
        self.loop = loop; self.seg = idx % len(loop); self.t = random.random()
        a = loop[self.seg]; b = loop[(self.seg + 1) % len(loop)]
        x = a[0] + (b[0] - a[0]) * self.t; y = a[1] + (b[1] - a[1]) * self.t
        Person.__init__(self, game, "ana", x, y, 0.0, ped=True)
        self.speed = random.uniform(1.1, 1.6); self.flee = 0.0; self.dir = 1 if random.random() < 0.5 else -1
        self.talk_cd = random.uniform(2, 10)
        self.offset = random.uniform(-0.8, 0.8)

    def update(self, dt, threat):
        if self.update_knock(dt):
            self.sync(); return
        if threat is not None and self.flee <= 0:
            self.flee = 3.0; self.flee_from = threat
        if self.flee > 0:
            self.flee -= dt
            tx, ty = self.flee_from
            dx, dy = self.x - tx, self.y - ty; d = math.hypot(dx, dy) or 1
            vx, vy = dx / d * 5.0, dy / d * 5.0; sp = 5.0
        else:
            a = self.loop[self.seg]; b = self.loop[(self.seg + self.dir) % len(self.loop)]
            dx, dy = b[0] - self.x, b[1] - self.y; d = math.hypot(dx, dy)
            if d < 1.0:
                self.seg = (self.seg + self.dir) % len(self.loop); d = 1
            vx, vy = dx / d * self.speed, dy / d * self.speed; sp = self.speed
        self.x += vx * dt; self.y += vy * dt
        px, py, nx, ny, tag = self.g.world.grid.push_circle(self.x, self.y, 0.35)
        self.x += px; self.y += py
        if sp > 0.1:
            th = math.degrees(math.atan2(-vx, vy))
            dh = (th - self.h + 180) % 360 - 180
            self.h += dh * min(1, dt * 8)
        self.walk_anim(dt, sp); self.sync()
