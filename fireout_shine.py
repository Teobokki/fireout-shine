"""ファイアアウト・シャイン / FIREOUT SHINE - neon street racing & police chases in an original night-time Tokyo.
(c)2026 EX Inc./HYPERION DIGITAL (c)2026"""
import os, sys, json, time, math, random, threading, tempfile, urllib.request, shutil, traceback

APP_NAME = "FIREOUT SHINE"
APP_VERSION = "1.0.3"
REPO = "Teobokki/fireout-shine"
UPDATE_URL = "https://raw.githubusercontent.com/%s/main/latest.json" % REPO
RELEASES_URL = "https://github.com/%s/releases/latest" % REPO
COPYRIGHT = "\u00a92026 EX Inc./HYPERION DIGITAL \u00a92026"
PUBLISHER = "EX Inc./HYPERION DIGITAL"

BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
if os.environ.get("FS_DATA_DIR"):
    DATA = os.environ["FS_DATA_DIR"]
elif os.name == "nt":
    DATA = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), APP_NAME)
else:
    DATA = os.path.join(os.path.expanduser("~"), ".fireout-shine")
os.makedirs(DATA, exist_ok=True)


def log_error(msg):
    if isinstance(msg, BaseException): msg = "".join(traceback.format_exception(type(msg), msg, msg.__traceback__))
    try:
        with open(os.path.join(DATA, "error.log"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + str(msg) + "\n")
    except Exception:
        pass


from panda3d.core import loadPrcFileData, Filename
_icon = os.path.join(BASE, "assets", "icon.ico")
loadPrcFileData("", """
window-title FIREOUT SHINE
win-size 1280 720
sync-video true
audio-library-name p3openal_audio
textures-power-2 none
framebuffer-multisample 0
notify-level warning
default-directnotify-level warning
load-display pandagl
want-pstats false
gl-coordinate-system default
""")
if os.environ.get("FS_WINSIZE"):       # test/QA override, e.g. FS_WINSIZE=1920x1080
    loadPrcFileData("", "win-size " + os.environ["FS_WINSIZE"].replace("x", " "))
if os.path.exists(_icon):
    loadPrcFileData("", "icon-filename " + Filename.from_os_specific(_icon).get_fullpath())

from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectFrame, DirectSlider, DGG
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui import DirectGuiGlobals
from panda3d.core import (TextNode, TransparencyAttrib, WindowProperties, PTA_LVecBase3f, Texture, PNMImage, SamplerState,
                          AudioSound, CardMaker, Fog, Vec3, TextureStage, ColorBlendAttrib, InputDevice)
import fs_ui as U
import fs_data as D
from fs_world import World


def vtuple(v):
    out = []
    for p in str(v).strip().lstrip("vV").split("."):
        n = "".join(ch for ch in p if ch.isdigit())
        out.append(int(n) if n else 0)
    return tuple(out + [0] * (3 - len(out)))


def is_portable():
    if not getattr(sys, "frozen", False) or not hasattr(sys, "_MEIPASS"):
        return False
    exe = os.path.normcase(os.path.abspath(sys.executable))
    meipass = os.path.normcase(os.path.abspath(sys._MEIPASS))
    if meipass.startswith(os.path.dirname(exe) + os.sep):
        return False
    la = os.environ.get("LOCALAPPDATA")
    if la and exe.startswith(os.path.normcase(os.path.join(la, "Programs", APP_NAME)) + os.sep):
        return False
    return True


def check_update():
    req = urllib.request.Request(UPDATE_URL + "?t=%d" % time.time(), headers={"User-Agent": "FIREOUT-SHINE/" + APP_VERSION})
    m = json.loads(urllib.request.urlopen(req, timeout=10).read(65536).decode("utf-8"))
    ver = str(m["version"])
    if vtuple(ver) > vtuple(APP_VERSION):
        if is_portable() and m.get("portable_url"):
            return "newer", {"version": ver, "notes": m.get("notes", ""), "link": m["portable_url"], "portable": True}
        return "newer", {"version": ver, "notes": m.get("notes", ""), "link": m.get("installer_url") or m.get("url") or RELEASES_URL}
    return "latest", "You have the latest version (%s)." % APP_VERSION


DEFAULT_SETTINGS = {"tod": "cycle", "master": 0.9, "sfx_volume": 0.8, "music_volume": 0.55, "voice_volume": 0.9, "quality": 1, "rain": False,
                    "buttons": True, "chatter": True, "subtitles": True, "fullscreen": False}
CREDITS = [
    ("FIREOUT SHINE  /  ファイアアウト・シャイン", None),
    ("Published by", PUBLISHER),
    ("Starring", "ANA (アナ)  &  DANIEL"),
    ("Game design, code, world, cars & characters", "EX Inc. - original procedural and scripted-Blender assets"),
    ("Engine", "Panda3D (Modified BSD licence)"),
    ("Fonts", "Exo 2 (SIL Open Font License)  -  Noto Sans CJK JP (SIL Open Font License)"),
    ("English voices (Piper TTS, offline)", "Kristin (LibriVox, public domain)  -  Joe (CC0)  -  LibriTTS-R speakers (CC BY 4.0, Google / Koizumi et al.)"),
    ("Japanese voice (Open JTalk, offline)", "HTS voice \"Mei\" (c) Nagoya Institute of Technology, MMDAgent, CC BY 3.0"),
    ("TTS software", "Piper (MIT)  -  Open JTalk / pyopenjtalk (Modified BSD / MIT)"),
    ("Music & sound effects", "Procedurally generated originals"),
    ("All locations, signs, brands and vehicles are fictional.", None),
    (COPYRIGHT, None),
]


class App(ShowBase):
    VERSION = APP_VERSION
    BASE = BASE

    def __init__(self):
        ShowBase.__init__(self)
        self.disable_mouse()
        self.log_error = log_error
        self.settings = dict(DEFAULT_SETTINGS)
        try:
            self.settings.update(json.load(open(os.path.join(DATA, "settings.json"), encoding="utf-8")))
        except Exception:
            pass
        A = lambda *p: os.path.join(BASE, "assets", *p)
        self.jpfont = U.init_fonts(self.loader, A("ui_font.ttf"), A("ui_plain.ttf"), A("jp_font.otf"))
        U.SFX = lambda n: self.sfx(n, 0.5)
        DirectGuiGlobals.setDefaultClickSound(None); DirectGuiGlobals.setDefaultRolloverSound(None)
        DirectGuiGlobals.setDefaultFont(U.FONT_PLAIN) if U.FONT_PLAIN else None
        self.set_background_color(0.01, 0.01, 0.03, 1)
        self.camLens.set_fov(70); self.camLens.set_near_far(0.2, 2400)
        # shared shader inputs
        self.campos = PTA_LVecBase3f.empty_array(1); self.campos_np = self.campos
        self.fogcol = Vec3(0.05, 0.03, 0.09); self.fogden = 0.0032
        self.envtex = self.loader.load_texture(Filename.from_os_specific(A("tex", "env.png")))
        img = PNMImage(4, 4, 3); img.fill(0.5, 0.5, 1.0)
        self.flat_nmap = Texture("flatn"); self.flat_nmap.load(img)
        self.render.set_shader_input("dayk", 0.0); self.render.set_shader_input("fogday", Vec3(0.68, 0.79, 0.90))
        self.render.set_shader_input("sundir", Vec3(0.35, -0.45, 0.82))
        self.envday = self.loader.load_texture(Filename.from_os_specific(A("tex", "sky_day.jpg"))); self.render.set_shader_input("envday", self.envday)
        fog = Fog("fog"); fog.set_color(self.fogcol); fog.set_exp_density(self.fogden); self.render.set_fog(fog); self.fog = fog
        # audio
        self._sfx = {}
        for n in ("engine", "engine_low", "siren", "skid", "wind", "rain", "nitro", "crash", "bump", "checkpoint", "beep", "go", "click",
                  "busted", "win", "heat", "horn", "door", "switch", "dial", "cash",
                  "pistol", "smg", "shotgun", "taser", "swing", "swing_heavy", "hit", "empty"):
            try:
                self._sfx[n] = self.loader.load_sfx(Filename.from_os_specific(A("sfx", n + ".wav")))
            except Exception:
                pass
        self.loops = {}
        for n in ("engine", "engine_low", "siren", "skid", "wind", "rain"):
            try:
                s = self.loader.load_sfx(Filename.from_os_specific(A("sfx", n + ".wav"))); s.set_loop(True); s.set_volume(0); self.loops[n] = s
            except Exception:
                pass
        self.music = {}
        for n in ("music_menu", "music_race"):
            try:
                s = self.loader.load_music(Filename.from_os_specific(A("sfx", n + ".wav"))); s.set_loop(True); self.music[n] = s
            except Exception:
                pass
        self.cur_music = None; self._voices = {}
        try:
            self.voice_index = json.load(open(A("voice", "index.json"), encoding="utf-8"))
        except Exception:
            self.voice_index = {}
        self.tex_cover = self.loader.load_texture(Filename.from_os_specific(A("cover.jpg")))
        self.tex_backdrop = self.loader.load_texture(Filename.from_os_specific(A("backdrop.jpg")))
        self.game = None; self.screen = None; self.overlay = None; self.pause_ui = None; self._upd_result = None
        self.flyover = False; self.fly_t = 0.0
        self.pad = None; self._setup_gamepad()
        self.apply_fullscreen()
        self.exitFunc = self.on_exit
        self.accept("window-event", self._on_window_event)
        self.filters = None
        self.world = None; self.stage = None
        self.task_mgr.add(self._frame, "app-frame", sort=50)
        self.show_splash()
        if os.environ.get("FS_SMOKE") == "money":          # built-in release smoke test (works in the frozen exe; runs a fixed sequence only)
            self.do_method_later(1.0, self._smoke_money, "fs-smoke")
        ts = os.environ.get("FS_TESTSCRIPT")
        if ts and not getattr(sys, "frozen", False):
            self.do_method_later(float(os.environ.get("FS_TESTDELAY", "1")),
                                 lambda t: exec(open(ts).read(), {"app": self, "__name__": "fstest"}) or t.done, "fs-test")

    # ---------------------------------------------------------------- helpers
    def vol(self, kind):
        return float(self.settings.get("master", 0.9)) * float(self.settings.get(kind, 0.8))

    def sfx(self, name, vol=1.0):
        s = self._sfx.get(name)
        if s:
            s.set_volume(vol * self.vol("sfx_volume")); s.play()

    def voice(self, fn, vol=1.0):
        try:
            s = self._voices.get(fn)
            if s is None:
                p = os.path.join(BASE, "assets", "voice", fn)
                if not os.path.exists(p): return
                s = self._voices[fn] = self.loader.load_sfx(Filename.from_os_specific(p))
            s.set_volume(vol * self.vol("voice_volume")); s.play()
        except Exception as e:
            log_error(e)

    def play_music(self, name):
        if self.cur_music == name: return
        for k, s in self.music.items():
            if k != name: s.stop()
        s = self.music.get(name); self.cur_music = name
        if s:
            s.set_volume(self.vol("music_volume") * 0.6); s.play()

    def update_audio(self, game, dt):
        L = self.loops; sv = self.vol("sfx_volume")
        c = game.pcar if game else None
        paused = game is None or game.paused
        if c and not paused:
            sp = c.speed; r = min(1.0, sp / 60.0)
            L.get("engine") and (L["engine"].set_volume(sv * (0.25 + 0.35 * r)), L["engine"].set_play_rate(0.6 + 1.2 * r + 0.2 * abs(c.throttle)))
            L.get("engine_low") and L["engine_low"].set_volume(sv * 0.25 * (1 - r))
            L.get("skid") and L["skid"].set_volume(sv * min(0.6, max(0.0, c.drift - 3.0) * 0.08))
            L.get("wind") and L["wind"].set_volume(sv * r * 0.35)
        else:
            for n in ("engine", "engine_low", "skid", "wind"):
                if n in L: L[n].set_volume(0)
        siren = 0.0
        if game and not paused and game.police:
            px, py = game.player_pos()
            d = min(math.hypot(p.x - px, p.y - py) for p in game.police)
            siren = max(0.0, 1.0 - d / 140.0) * (1.0 if game.heat else 0.0)
        if "siren" in L: L["siren"].set_volume(sv * 0.4 * siren)
        if "rain" in L: L["rain"].set_volume(sv * 0.5 if (game and getattr(game, "home", None) and game.home.get("mode") == "shower") else (sv * 0.35 if self.settings.get("rain") and game and not paused else 0))
        for s in L.values():
            if s.status() != AudioSound.PLAYING: s.play()

    def save_path(self):
        return os.path.join(DATA, "save.json")

    def has_save(self):
        return os.path.exists(self.save_path())

    def write_save(self, d):
        p = self.save_path(); tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: json.dump(d, f, indent=1, ensure_ascii=False)
        os.replace(tmp, p)

    def load_save(self):
        try: return json.load(open(self.save_path(), encoding="utf-8"))
        except Exception: return None

    def save_settings(self):
        try:
            json.dump(self.settings, open(os.path.join(DATA, "settings.json"), "w", encoding="utf-8"), indent=1)
        except Exception as e:
            log_error("settings: %r" % e)

    def apply_fullscreen(self):
        wp = WindowProperties()
        if self.settings.get("fullscreen"):
            wp.set_fullscreen(True); wp.set_size(self.pipe.get_display_width(), self.pipe.get_display_height())
        else:
            wp.set_fullscreen(False); wp.set_size(1280, 720)
        if self.win and hasattr(self.win, "request_properties"):
            self.win.request_properties(wp)

    def set_daylight(self, k, warm=0.0, sun=(0.35, -0.45, 0.82)):
        k = max(0.0, min(1.0, k))
        if self.world is not None: self.world.set_daylight(k, warm)
        self.render.set_shader_input("dayk", k); self.render.set_shader_input("sundir", Vec3(*sun))
        n = Vec3(0.05, 0.03, 0.09); d = Vec3(0.68, 0.76 - 0.06 * warm, 0.88 - 0.16 * warm)
        fc = n * (1 - k) + d * k; self.fog.set_color(fc); self.set_background_color(fc[0], fc[1], fc[2], 1)
        self.fog.set_exp_density(self.fogden * (1 - 0.35 * k))
        dayb = k > 0.5
        if dayb != getattr(self, "_bloom_day", False):
            self._bloom_day = dayb; self.apply_quality()

    def apply_quality(self):
        q = int(self.settings.get("quality", 1))
        try:
            if self.filters is None and q >= 1:
                from direct.filter.CommonFilters import CommonFilters
                self.filters = CommonFilters(self.win, self.cam)
            if self.filters is not None:
                if q >= 1:
                    dayb = getattr(self, "_bloom_day", False)
                    self.filters.set_bloom(blend=(0.3, 0.4, 0.3, 0.0), mintrigger=0.8 if dayb else 0.55, maxtrigger=1.0, desat=0.1,
                                           intensity=(0.35 if dayb else 1.0) * (0.9 if q == 1 else 1.25), size="medium" if q == 1 else "large")
                else:
                    self.filters.del_bloom()
        except Exception as e:
            log_error("bloom: %r" % e); self.filters = None
        self.rain_on(bool(self.settings.get("rain")))

    def rain_on(self, on):
        if on and getattr(self, "rain_np", None) is None:
            cm = CardMaker("rain"); cm.set_frame(-2, 2, -1, 1)
            n = self.render2d.attach_new_node(cm.generate()); n.set_transparency(TransparencyAttrib.M_alpha)
            t = self.loader.load_texture(Filename.from_os_specific(os.path.join(BASE, "assets", "tex", "streak.png")))
            n.set_texture(t); n.set_tex_scale(TextureStage.get_default(), 9, 3); n.set_color(0.7, 0.8, 1.0, 0.18); n.set_bin("fixed", 5)
            n.set_attrib(ColorBlendAttrib.make(ColorBlendAttrib.M_add, ColorBlendAttrib.O_incoming_alpha, ColorBlendAttrib.O_one))
            self.rain_np = n
        elif not on and getattr(self, "rain_np", None) is not None:
            self.rain_np.remove_node(); self.rain_np = None

    def _setup_gamepad(self):
        try:
            devs = self.devices.get_devices(InputDevice.DeviceClass.gamepad)
            if devs:
                self.gp = devs[0]; self.attach_input_device(self.gp, prefix="gp")
                self.pad = {}
                for b, k in (("gp-face_a", "f"), ("gp-face_b", "h"), ("gp-face_y", "c"), ("gp-back", "r"), ("gp-start", "escape"),
                             ("gp-face_x", "e"), ("gp-lshoulder", "q"), ("gp-dpad_up", "t")):
                    self.accept(b, lambda k=k: messenger.send(k))
        except Exception as e:
            log_error("gamepad: %r" % e)

    def _poll_pad(self):
        gp = getattr(self, "gp", None)
        if gp is None or self.pad is None: return
        try:
            def ax(a):
                v = gp.find_axis(a); return v.value if v else 0.0
            self.pad["lx"] = ax(InputDevice.Axis.left_x)
            self.pad["rt"] = max(0.0, ax(InputDevice.Axis.right_trigger)); self.pad["lt"] = max(0.0, ax(InputDevice.Axis.left_trigger))
            if self.game:
                self.game.vb["v_hand"] = gp.find_button("rshoulder").pressed
                self.game.vb["v_nitro"] = gp.find_button("face_x").pressed if False else gp.find_button("rstick").pressed
        except Exception:
            pass

    def _frame(self, task):
        cam = self.camera.get_pos(self.render); self.campos.set_element(0, cam)
        if self.rain_np if hasattr(self, "rain_np") else None:
            self.rain_np.set_tex_offset(TextureStage.get_default(), 0.15 * task.time, 2.2 * task.time)
        self._poll_pad()
        if self.flyover and self.world is not None and self.game is None:
            dt = min(0.05, self.clock.get_dt()); self.fly_t += dt
            if self.stage is not None:
                t = self.fly_t
                self.camera.set_pos(4.5 + math.sin(t * 0.15) * 1.2, -53.5, 1.55 + math.sin(t * 0.21) * 0.15)
                self.camera.look_at(1.4, -41.0, 1.45); self.camLens.set_fov(46)
            else:
                # cinematic avenue flyover: glide up the main street towards the scramble crossing and the tower
                seg = (self.fly_t * 9.0) % 700.0; y = -360.0 + seg
                self.camera.set_pos(-3.0, y, 16 + 9 * math.sin(self.fly_t * 0.1))
                self.camera.look_at(4.0, y + 80, 12.0); self.camLens.set_fov(62)
            self.world.update(dt, self.fly_t)
            self.update_audio(None, dt)
        return task.cont

    def _on_window_event(self, win):
        if win and win.is_closed():
            self.userExit()

    def on_exit(self):
        if self.game:
            try: self.game.save()
            except Exception as e: log_error("save on exit: %r" % e)

    def clear_screen(self):
        if self.screen:
            self.screen.destroy(); self.screen = None

    def new_screen(self, dim=0.0):
        self.clear_screen()
        self.screen = DirectFrame(parent=self.aspect2d, frameColor=(0, 0, 0, dim), frameSize=(-4, 4, -2, 2))
        return self.screen

    # ---------------------------------------------------------------- boot: splash -> intro flyover -> title
    def _img(self, parent, name, pos=(0, 0), scale=(1, 1), alpha=True):
        im = OnscreenImage(parent=parent, image=Filename.from_os_specific(os.path.join(BASE, "assets", *name.split("/"))).get_fullpath(),
                           pos=(pos[0], 0, pos[1]), scale=(scale[0], 1, scale[1]))
        if alpha: im.set_transparency(TransparencyAttrib.M_alpha)
        return im

    def show_splash(self):
        s = self.new_screen(1.0)
        ar = max(self.getAspectRatio(), 1.0)
        im = self._img(s, "tex/splash.jpg", scale=(min(ar, 16 / 9.0), 9 / 16.0 * min(ar, 16 / 9.0)), alpha=False)
        im.set_color_scale(1, 1, 1, 0); im.set_transparency(TransparencyAttrib.M_alpha)
        self._splash = (s, im, 0.0)
        self.accept("escape", self._end_splash); self.accept("enter", self._end_splash); self.accept("mouse1", self._end_splash)
        self.task_mgr.add(self._splash_task, "splash")

    def _splash_task(self, task):
        if not getattr(self, "_splash", None): return task.done
        s, im, _ = self._splash; t = task.time
        if t > 0.3 and self.world is None:
            try:
                self.world = World(self, int(self.settings.get("quality", 1)))
            except Exception:
                log_error(traceback.format_exc()); raise
            self.apply_quality()
        a = min(1.0, t / 0.6) * min(1.0, max(0.0, (3.2 - t) / 0.6))
        if not im.is_empty(): im.set_color_scale(1, 1, 1, a)
        if t > 3.2 and self.world is not None:
            self._end_splash(); return task.done
        return task.cont

    def _end_splash(self):
        if not getattr(self, "_splash", None) or self.world is None: return
        self._splash = None; self.task_mgr.remove("splash")
        for k in ("escape", "enter", "mouse1"): self.ignore(k)
        self.show_intro()

    def show_intro(self):
        s = self.new_screen(0.0); self.flyover = True; self.fly_t = 0.0; self.play_music("music_menu")
        ar = max(self.getAspectRatio(), 1.0)
        top = DirectFrame(parent=s, frameColor=(0, 0, 0, 1), frameSize=(-ar - 1, ar + 1, 0.82, 1.2))
        bot = DirectFrame(parent=s, frameColor=(0, 0, 0, 1), frameSize=(-ar - 1, ar + 1, -1.2, -0.82))
        logo = self._img(s, "tex/logo.png", pos=(0, 0.05), scale=(0.95, 0.95 * 420 / 1900.0))
        jp = U.text(s, D.TITLE_JP, (0, -0.22), 0.07, fg=U.CYAN, font=self.jpfont)
        sub = U.text(s, "%s presents" % PUBLISHER, (0, 0.38), 0.04, fg=(1, 1, 1, 0.85), font=U.FONT_PLAIN)
        skip = U.text(s, "Press any key to skip", (ar - 0.05, -0.92), 0.032, fg=(1, 1, 1, 0.55), align=TextNode.A_right, font=U.FONT_PLAIN)
        for n in (logo,): n.set_color_scale(1, 1, 1, 0)
        self._intro = {"t": 0.0, "logo": logo}
        self.buttonThrowers and self.buttonThrowers[0].node().set_button_down_event("fs-anykey")
        self.accept("fs-anykey", lambda b: self.show_title() if not b.startswith("wheel") else None)
        self.task_mgr.add(self._intro_task, "intro")

    def _intro_task(self, task):
        if not getattr(self, "_intro", None): return task.done
        t = task.time; lg = self._intro["logo"]
        if not lg.is_empty(): lg.set_color_scale(1, 1, 1, max(0.0, min(1.0, (t - 0.8) / 1.0)))
        if t > 7.5: self.show_title(); return task.done
        return task.cont

    def show_title(self):
        self._intro = None; self.task_mgr.remove("intro"); self.show_stage(False)
        self.ignore("fs-anykey")
        s = self.new_screen(0.0); self.flyover = True
        ar = max(self.getAspectRatio(), 1.0)
        dim = DirectFrame(parent=s, frameColor=(0, 0, 0, 0.35), frameSize=(-ar - 1, ar + 1, -1.2, 1.2))
        cov = OnscreenImage(parent=s, image=self.tex_cover, pos=(0, 0, 0.04), scale=(0.9, 1, 0.9))
        b = U.button(s, "PRESS PLAY", (0, -0.86), self.show_menu, w=0.33, h=0.06, col=(0.95, 0.15, 0.5, 1), edge=U.CYAN, scale=0.06)
        self._pp = b
        U.text(s, "v" + APP_VERSION, (-ar + 0.03, -0.96), 0.035, (1, 1, 1, 1), TextNode.A_left, font=U.FONT_PLAIN)
        U.text(s, COPYRIGHT, (ar - 0.03, -0.96), 0.035, (1, 1, 1, 1), TextNode.A_right, font=U.FONT_PLAIN)
        self.task_mgr.add(self._pulse, "pp-pulse")
        self.buttonThrowers and self.buttonThrowers[0].node().set_button_down_event("fs-anykey")
        self.accept("fs-anykey", self._anykey)

    def _anykey(self, btn):
        if btn.startswith("mouse") or btn.startswith("wheel"): return
        self.show_menu()

    def _pulse(self, task):
        if not getattr(self, "_pp", None) or self._pp.is_empty(): return task.done
        self._pp.set_scale(1 + 0.05 * math.sin(task.time * 5))
        return task.cont

    # ---------------------------------------------------------------- main menu
    def show_menu(self):
        self.ignore("fs-anykey"); self._pp = None; self.flyover = True; self.play_music("music_menu")
        s = self.new_screen(0.0)
        ar = max(self.getAspectRatio(), 1.0)
        x = -ar + 0.55
        U.panel(s, -0.45, 0.45, -0.78, 0.78, pos=(x, -0.06))
        self._img(s, "tex/logo.png", pos=(x, 0.6), scale=(0.42, 0.42 * 420 / 1900.0))
        U.text(s, D.TITLE_JP, (x, 0.47), 0.045, fg=U.CYAN, font=self.jpfont)
        # ANA & DANIEL standing by the car in the live neon city
        self.show_stage(True)
        U.text(s, "ANA", (0.12, -0.78), 0.06, fg=(0.4, 0.7, 1, 1)); U.text(s, "DANIEL", (0.62, -0.78), 0.06, fg=(0.5, 1, 0.4, 1))
        has = self.has_save()
        items = [("CONTINUE" if has else "PLAY", lambda: self.start_game(None), U.PINK),
                 ("QUICK RACE", lambda: self.start_game("sprint"), U.PINK),
                 (D.GET_WANTED, lambda: self.start_game("chase"), (0.35, 0.45, 1, 1)),
                 ("FRGARAGE", lambda: self.start_game("garage"), U.CYAN),
                 ("SETTINGS", lambda: self.open_settings(self.show_menu), (0.6, 0.6, 0.7, 1)),
                 ("CREDITS", self.show_credits, (0.6, 0.6, 0.7, 1)),
                 ("CHECK FOR UPDATES", self.start_update_check, (0.6, 0.6, 0.7, 1)),
                 ("QUIT", self.userExit, (0.9, 0.3, 0.3, 1))]
        if has: items.insert(1, ("NEW GAME", self.new_game, U.PINK))
        for i, (t, c, col) in enumerate(items):
            U.button(s, t, (x, 0.32 - i * 0.12), c, w=0.33, h=0.045, edge=col, scale=0.04)
        U.text(s, "v" + APP_VERSION, (-ar + 0.03, -0.96), 0.035, (1, 1, 1, 1), TextNode.A_left, font=U.FONT_PLAIN)
        U.text(s, COPYRIGHT, (ar - 0.03, -0.96), 0.035, (1, 1, 1, 1), TextNode.A_right, font=U.FONT_PLAIN)

    def show_stage(self, on):
        if on:
            try: self.set_daylight(0.0)
            except Exception: log_error(traceback.format_exc())
        if on and self.stage is None:
            from fs_menu_stage import Stage
            try: self.stage = Stage(self)
            except Exception: log_error(traceback.format_exc()); self.stage = None
        elif not on and self.stage is not None:
            self.stage.destroy(); self.stage = None

    def new_game(self, force=False):
        if self.has_save() and not force:
            self._dialog("Start a new game?\nYour current save will be replaced.", [("NEW GAME", lambda: (self._close_dialog(), self.new_game(True))), ("CANCEL", self._close_dialog)])
            return
        try:
            if os.path.exists(self.save_path()): shutil.copy(self.save_path(), self.save_path() + ".bak"); os.remove(self.save_path())
        except Exception: pass
        self.start_game(None)

    def show_credits(self):
        o = DirectFrame(parent=self.aspect2d, frameColor=(0, 0, 0, 0.85), frameSize=(-4, 4, -2, 2), state=DGG.NORMAL)
        U.panel(o, -1.25, 1.25, -0.9, 0.9)
        U.text(o, "CREDITS", (0, 0.78), 0.07, fg=U.PINK)
        for k, w in enumerate(("ana", "daniel")):
            try: self._img(o, "tex/portrait_%s.png" % w, pos=(-1.05 + k * 2.1, 0.7), scale=(0.11, 0.11))
            except Exception: pass
        z = 0.64
        for a, b in CREDITS:
            U.text(o, a, (0, z), 0.036, fg=U.CYAN if b else (1, 1, 1, 1), font=self.jpfont if "ア" in a else None); z -= 0.055
            if b: U.text(o, b, (0, z), 0.03, font=U.FONT_PLAIN, wrap=70); z -= 0.075
        U.button(o, "BACK", (0, -0.82), o.destroy, w=0.2, h=0.045, scale=0.04, hint="Esc")

    def start_game(self, start):
        self.task_mgr.remove("pp-pulse"); self.ignore("fs-anykey")
        s = self.new_screen(1.0); s["frameColor"] = (0.02, 0.01, 0.05, 1)
        U.text(s, "Entering Shinko Ward...", (0, 0.05), 0.07, fg=U.PINK)
        U.text(s, "Tip: F takes any car, Q switches ANA / DANIEL, T opens the phone, hold Tab for the weapon wheel.", (0, -0.1), 0.04, font=U.FONT_PLAIN)
        save = self.load_save()
        self.show_stage(False)
        def go(task):
            from fs_game import Game
            self.flyover = False
            try:
                self.game = Game(self, save, start)
            except Exception:
                log_error(traceback.format_exc()); raise
            self.clear_screen(); self.play_music("music_race")
            return task.done
        self.do_method_later(0.15, go, "start-game")

    def quit_to_title(self):
        self.hide_pause()
        if self.game:
            self.game.destroy(); self.game = None
        self.camLens.set_fov(70); self.flyover = True
        self.show_menu()

    def _smoke_money(self, task):
        out = os.environ.get("FS_SMOKE_OUT", os.path.join(BASE, "docs"))
        log = open(os.path.join(out, "smoke_money.log"), "a", encoding="utf-8")
        def L(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush()
        def shot(n):
            self.graphicsEngine.render_frame(); self.graphicsEngine.render_frame()
            self.win.save_screenshot(Filename.from_os_specific(os.path.join(out, n + ".png"))); L("shot", n)
        st = {"i": 0, "t": 0.0}
        def drive():
            g = self.game; g.vb["v_up"] = True
        def m_try(t):
            m = self.money_ui; m.ent.enterText(t); m.do_add(); L("add", repr(t), "->", m.msg["text"], "cash", self.game.cash)
        steps = [
            (7.0, lambda: (self.show_title(), )), (1.0, self.show_menu), (1.0, lambda: self.start_game(None)),
            (10.0, lambda: setattr(self.game, "intro_t", 0.01)), (1.0, lambda: self.game.enter_car(self.game.own)), (1.0, drive), (2.0, lambda: (L("phone pcar", self.game.pcar is not None), self.game.toggle_phone(), L("phone open", self.game.phone is not None))),
            (1.5, lambda: shot("phone_driving_v102")), (0.2, lambda: (self.game.vb.clear(), self.game.toggle_phone())),
            (1.5, self.show_pause), (0.6, lambda: shot("pause_menu_v102")), (0.3, self.show_add_money),
            (0.3, lambda: [m_try(t) for t in ("-5", "abc", "0", "", "1,000,000")]),
            (0.3, lambda: (self.money_ui.quick(10 ** 9), self.money_ui.quick(10 ** 6), self.money_ui.quick(1000))),
            (0.6, lambda: shot("add_money")), (0.3, lambda: self.money_ui.do_add()),
            (0.5, lambda: m_try("500000000000")), (0.5, lambda: m_try("1")), (0.6, lambda: shot("cash_limit")),
            (0.3, lambda: L("saved", (self.load_save() or {}).get("cash"))),
            (0.3, self.hide_pause), (0.1, lambda: (setattr(self.game, "cash_pop_k", 2.6), self.game.cash_pop.setText("+¥98,997,996,500"))),
            (0.8, lambda: (L("hud", self.game.cash_t["text"]), shot("cash_hud"))), (0.5, lambda: (L("SMOKE OK"), self.userExit())),
        ]
        def run(t):
            try:
                if self.world is None and st["i"] > 2: return t.cont
                st["t"] += globalClock.get_dt()
                if st["i"] < len(steps) and st["t"] >= steps[st["i"]][0]:
                    st["t"] = 0.0; f = steps[st["i"]][1]; st["i"] += 1; f()
            except Exception:
                import traceback; L("ERR", traceback.format_exc()); st["i"] += 1
            return t.cont
        self.task_mgr.add(run, "fs-smoke-run", sort=100)
        return task.done

    # ---------------------------------------------------------------- pause
    def show_pause(self):
        if not self.game or self.pause_ui: return
        g = self.game; g.paused = True
        o = self.pause_ui = DirectFrame(parent=self.aspect2d, frameColor=(0, 0, 0, 0.6), frameSize=(-4, 4, -2, 2), state=DGG.NORMAL)
        U.panel(o, -0.45, 0.45, -0.72, 0.72)
        U.text(o, "PAUSED", (0, 0.58), 0.08, fg=U.PINK); U.text(o, "一時停止", (0, 0.5), 0.04, fg=U.CYAN, font=self.jpfont)
        items = (("RESUME", self.hide_pause), ("ADD MONEY", self.show_add_money), ("MAP", lambda: (self.hide_pause(), g.toggle_map())),
                 ("RESET CAR DAMAGE", lambda: (self.hide_pause(), g.repair_car())),
                 ("SETTINGS", lambda: self.open_settings(None)), ("CONTROLS", self.show_controls), ("PROFILE", self.show_profile),
                 ("SAVE & QUIT TO TITLE", self.quit_to_title), ("QUIT GAME", self.userExit))
        for i, (t, c) in enumerate(items):
            U.button(o, t, (0, 0.43 - i * 0.118), c, w=0.33, h=0.05, scale=0.04, edge=(0.3, 1.0, 0.45, 1) if t == "ADD MONEY" else U.PINK)
        self.accept("escape", self.hide_pause)

    def show_add_money(self):
        """ADD MONEY panel: type an amount or use the quick buttons; total cash is capped at 100,000,000,000."""
        from fs_game import CASH_CAP
        from direct.gui.DirectGui import DirectEntry
        g = self.game
        if not g or getattr(self, "money_ui", None): return
        o = self.money_ui = DirectFrame(parent=self.aspect2d, frameColor=(0, 0, 0, 0.55), frameSize=(-4, 4, -2, 2), state=DGG.NORMAL)
        o.set_bin("gui-popup", 70)
        U.panel(o, -0.78, 0.78, -0.62, 0.62, edge=(0.3, 1.0, 0.45, 1))
        U.text(o, "ADD MONEY", (0, 0.49), 0.075, fg=(0.3, 1.0, 0.45, 1))
        bal = U.text(o, "", (0, 0.31), 0.045, fg=U.GOLD, font=U.FONT_PLAIN)
        U.text(o, "Limit  ¥%s" % format(CASH_CAP, ","), (0, 0.25), 0.03, fg=(0.75, 0.75, 0.8, 1), font=U.FONT_PLAIN)
        U.text(o, "AMOUNT  ¥", (-0.43, 0.115), 0.04, fg=U.PINK, align=TextNode.A_right)
        ent = DirectEntry(parent=o, initialText="", width=13, numLines=1, scale=0.06, pos=(-0.4, 0, 0.11), frameColor=(0.1, 0.08, 0.15, 1),
                          text_fg=(1, 1, 1, 1), entryFont=U.FONT_PLAIN, focus=1, command=lambda t: do_add())
        msg = U.text(o, "", (0, -0.36), 0.036, fg=(1, 1, 1, 1), font=U.FONT_PLAIN, wrap=34)
        o.ent = ent; o.msg = msg
        def upd():
            bal.setText("Cash  ¥%s" % format(g.cash, ","))
        def cur():
            t = ent.get().replace(",", "").replace(" ", "").replace("¥", "").strip()
            return int(t) if t.isdigit() else 0
        def quick(v):
            room = CASH_CAP - g.cash
            n = room if v is None else min(cur() + v, max(room, 0))
            ent.enterText(format(n, ",") if n > 0 else ""); msg.setText("")
        def do_add():
            ok, text = g.add_cash_text(ent.get())
            msg.setText(text); msg["fg"] = (0.3, 1.0, 0.45, 1) if ok else (1.0, 0.45, 0.4, 1)
            if ok: ent.enterText("")
            upd()
        o.do_add = do_add; o.quick = quick
        for k, (lbl, v) in enumerate((("+1K", 1000), ("+100K", 100000), ("+1M", 10 ** 6), ("+1B", 10 ** 9), ("+10B", 10 ** 10), ("MAX", None))):
            U.button(o, lbl, (-0.55 + k * 0.22, -0.06), lambda v=v: quick(v), w=0.09, h=0.045, scale=0.034, edge=U.GOLD if v is None else U.CYAN)
        U.button(o, "CLEAR", (-0.25, -0.2), lambda: (ent.enterText(""), msg.setText("")), w=0.14, h=0.05, scale=0.036)
        U.button(o, "ADD", (0.25, -0.2), do_add, w=0.14, h=0.05, scale=0.04, edge=(0.3, 1.0, 0.45, 1), hint="Enter")
        def close():
            self.money_ui.destroy(); self.money_ui = None; self.accept("escape", self.hide_pause)
        U.button(o, "BACK", (0, -0.52), close, w=0.2, h=0.045, scale=0.04, hint="Esc")
        self.accept("escape", close); o.close = close
        upd()

    def hide_pause(self):
        if getattr(self, "money_ui", None):
            self.money_ui.destroy(); self.money_ui = None
        if self.pause_ui:
            self.pause_ui.destroy(); self.pause_ui = None
        if self.game:
            self.game.paused = False; self.accept("escape", self.game.key_esc)

    def show_controls(self):
        o = DirectFrame(parent=self.aspect2d, frameColor=(0, 0, 0, 0.8), frameSize=(-4, 4, -2, 2), state=DGG.NORMAL)
        U.panel(o, -1.0, 1.0, -0.8, 0.8)
        U.text(o, "CONTROLS", (0, 0.68), 0.07, fg=U.PINK)
        rows = [("W / S  or  Arrows", "Accelerate / brake & reverse  (walk on foot)"), ("A / D  or  Arrows", "Steer"),
                ("Space", "Handbrake (drift)"), ("Shift", "Nitro  /  run on foot"), ("F", "Enter / exit / take any car, ride a taxi"),
                ("Q", "Switch ANA <-> DANIEL"), ("Tab (hold) / wheel", "Weapon wheel / cycle weapons"),
                ("Right / Left mouse", "Aim (over-shoulder) / attack"), ("T  or  Up (on foot)", "Phone (EX IX G9)"), ("E", "Start event / enter FRGARAGE"),
                ("C", "Camera"), ("R", "Reset car"), ("H", "Horn"), ("M", "Map (click to set a waypoint)"), ("Esc", "Menu"),
                ("Gamepad", "Triggers drive, left stick steers, A enter/exit, RB handbrake")]
        for k, (a, b) in enumerate(rows):
            U.text(o, a, (-0.3, 0.58 - k * 0.075), 0.033, fg=U.CYAN, align=TextNode.A_right)
            U.text(o, b, (-0.25, 0.58 - k * 0.075), 0.032, align=TextNode.A_left, font=U.FONT_PLAIN)
        U.button(o, "BACK", (0, -0.72), o.destroy, w=0.2, h=0.045, scale=0.04)

    def show_profile(self):
        g = self.game
        o = DirectFrame(parent=self.aspect2d, frameColor=(0, 0, 0, 0.8), frameSize=(-4, 4, -2, 2), state=DGG.NORMAL)
        U.panel(o, -0.9, 0.9, -0.7, 0.7)
        U.text(o, "PROFILE", (0, 0.58), 0.07, fg=U.PINK)
        for k, w in enumerate(("ana", "daniel")):
            x = -0.45 + k * 0.9
            try: self._img(o, "tex/portrait_%s.png" % w, pos=(x, 0.3), scale=(0.17, 0.17))
            except Exception: pass
            U.text(o, ("ANA  アナ" if w == "ana" else "DANIEL") + ("  (active)" if g.active == w else ""), (x, 0.06), 0.042,
                   fg=(0.4, 0.7, 1, 1) if w == "ana" else (0.5, 1, 0.4, 1), font=self.jpfont)
        lines = ["Cash  ¥%s" % format(g.cash, ","), "Neon tokens  %d / %d" % (len(g.tokens), len(D.TOKENS))]
        for k_, v in g.best.items():
            lines.append("Best %s  %s" % (k_.upper(), g.fmt(v) if isinstance(v, float) else v))
        for nm, v in g.cam_cams.items(): lines.append("Speed camera %s  %d km/h" % (nm, v))
        for k, l in enumerate(lines[:9]): U.text(o, l, (0, -0.06 - k * 0.06), 0.036, font=U.FONT_PLAIN)
        U.button(o, "BACK", (0, -0.62), o.destroy, w=0.2, h=0.045, scale=0.04)

    # ---------------------------------------------------------------- settings
    def open_settings(self, back):
        o = DirectFrame(parent=self.aspect2d, frameColor=(0, 0, 0, 0.75), frameSize=(-4, 4, -2, 2), state=DGG.NORMAL)
        U.panel(o, -0.95, 0.95, -0.85, 0.85)
        U.text(o, "SETTINGS", (0, 0.73), 0.07, fg=U.PINK)
        st = self.settings
        def slider(label, key, z):
            t = U.text(o, "", (-0.45, z - 0.012), 0.038, align=TextNode.A_right, font=U.FONT_PLAIN)
            def upd():
                st[key] = round(float(sl["value"]), 2); t.setText("%s  %d%%" % (label, round(st[key] * 100)))
                if self.cur_music and self.cur_music in self.music: self.music[self.cur_music].set_volume(self.vol("music_volume") * 0.6)
            sl = DirectSlider(parent=o, range=(0, 1), value=st[key], pageSize=0.05, scale=0.38, pos=(0.0, 0, z),
                              frameColor=(0.25, 0.2, 0.35, 1), thumb_frameColor=U.PINK, command=upd)
            upd()
        slider("Master volume", "master", 0.58); slider("Effects", "sfx_volume", 0.48); slider("Music", "music_volume", 0.38)
        slider("Voices", "voice_volume", 0.28)
        def cyc(label, key, opts, z, after=None):
            def f():
                vals = [v for v, _ in opts]; st[key] = vals[(vals.index(st.get(key, vals[0])) + 1) % len(vals)] if st.get(key) in vals else vals[0]
                b.btn["text"] = "%s: %s" % (label, dict(opts)[st[key]])
                if after: after()
            b = U.button(o, "%s: %s" % (label, dict(opts).get(st.get(key), opts[0][1])), (0, z), f, w=0.45, h=0.042, scale=0.036)
        onoff = [(True, "ON"), (False, "OFF")]
        cyc("Graphics quality", "quality", [(0, "LOW"), (1, "MEDIUM"), (2, "HIGH")], 0.15, self.apply_quality)
        cyc("Rain", "rain", onoff, 0.05, self.apply_quality)
        cyc("On-screen buttons", "buttons", onoff, -0.05, lambda: self.game and (setattr(self.game, "btn_state", None), self.game.refresh_buttons()))
        cyc("NPC chatter", "chatter", onoff, -0.15)
        cyc("Subtitles", "subtitles", onoff, -0.25)
        cyc("Fullscreen", "fullscreen", onoff, -0.35, self.apply_fullscreen)
        cyc("Time of day", "tod", [("cycle", "DAY/NIGHT CYCLE"), ("day", "LOCK DAY"), ("night", "LOCK NIGHT")], -0.45)
        U.text(o, "Graphics quality changes the amount of traffic, pedestrians and bloom.", (0, -0.55), 0.03, font=U.FONT_PLAIN, fg=(1, 1, 1, 0.6))
        def done():
            self.save_settings(); o.destroy()
            if back: back()
        U.button(o, "DONE", (0, -0.7), done, w=0.2, h=0.05, scale=0.042, edge=U.CYAN)

    # ---------------------------------------------------------------- dialogs / updates
    def _dialog(self, msg, buttons):
        self._close_dialog()
        o = self.overlay = DirectFrame(parent=self.aspect2d, frameColor=(0, 0, 0, 0.6), frameSize=(-4, 4, -2, 2), state=DGG.NORMAL)
        U.panel(o, -0.9, 0.9, -0.38, 0.38)
        U.text(o, msg, (0, 0.2), 0.045, wrap=34, font=U.FONT_PLAIN)
        n = len(buttons)
        for i, (t, c) in enumerate(buttons):
            U.button(o, t, ((i - (n - 1) / 2) * 0.62, -0.25), c, w=0.28, h=0.05, scale=0.036)

    def _close_dialog(self):
        if self.overlay:
            self.overlay.destroy(); self.overlay = None

    def start_update_check(self):
        self._dialog("Checking for updates...", [])
        def work():
            try: self._upd_result = check_update()
            except Exception as e: self._upd_result = ("error", "Could not check for updates.\n(%s)" % (str(e)[:90]))
        threading.Thread(target=work, daemon=True).start()
        self.task_mgr.add(self._poll_update, "poll-update")

    def _poll_update(self, task):
        r = self._upd_result
        if r is None: return task.cont
        self._upd_result = None
        kind, data = r
        if kind == "newer":
            self._dialog("FIREOUT SHINE %s is available!\n%s\n\nDownload and install it now?" % (data["version"], data["notes"][:160]),
                         [("DOWNLOAD & INSTALL", lambda: (self.download_portable(data["link"]) if data.get("portable") else self.download_install(data["link"]))),
                          ("NOT NOW", self._close_dialog)])
        else:
            self._dialog(data, [("OK", self._close_dialog)])
        return task.done

    def download_install(self, link):
        if not link.lower().endswith(".exe"):
            self._open_browser(link); return
        self._dialog("Downloading update...", [])
        def work():
            try:
                dst = os.path.join(tempfile.gettempdir(), os.path.basename(link.split("?")[0]) or "FIREOUT-SHINE-Setup.exe")
                req = urllib.request.Request(link, headers={"User-Agent": "FIREOUT-SHINE/" + APP_VERSION})
                with urllib.request.urlopen(req, timeout=60) as r, open(dst, "wb") as f: shutil.copyfileobj(r, f)
                self._upd_result = ("install", dst)
            except Exception as e:
                self._upd_result = ("dlerror", (link, str(e)[:90]))
        threading.Thread(target=work, daemon=True).start()
        self.task_mgr.add(self._poll_download, "poll-dl")

    def _poll_download(self, task):
        r = self._upd_result
        if r is None: return task.cont
        self._upd_result = None
        if r[0] == "install":
            try: os.startfile(r[1]); self.userExit()
            except Exception as e:
                self._dialog("Could not start the installer:\n%s" % e, [("OPEN DOWNLOAD PAGE", lambda: self._open_browser(RELEASES_URL)), ("CLOSE", self._close_dialog)])
        else:
            self._dialog("Download failed.\n%s" % r[1][1], [("OPEN DOWNLOAD PAGE", lambda: self._open_browser(RELEASES_URL)), ("CLOSE", self._close_dialog)])
        return task.done

    def download_portable(self, link):
        exe = os.path.abspath(sys.executable); new = exe + ".new"
        self._dialog("Downloading portable update...", [])
        def work():
            try:
                req = urllib.request.Request(link, headers={"User-Agent": "FIREOUT-SHINE/" + APP_VERSION})
                with urllib.request.urlopen(req, timeout=60) as r, open(new, "wb") as f: shutil.copyfileobj(r, f)
                with open(new, "rb") as f: ok = f.read(2) == b"MZ"
                if not ok or os.path.getsize(new) < 5_000_000:
                    os.remove(new); raise IOError("downloaded file is not a valid FIREOUT SHINE executable")
                self._upd_result = ("swap", new)
            except Exception as e:
                try:
                    if os.path.exists(new): os.remove(new)
                except OSError: pass
                self._upd_result = ("dlerror", (link, str(e)[:90]))
        threading.Thread(target=work, daemon=True).start()
        self.task_mgr.add(self._poll_portable, "poll-dl")

    def _poll_portable(self, task):
        r = self._upd_result
        if r is None: return task.cont
        self._upd_result = None
        if r[0] == "swap":
            try: self._launch_swap_helper(os.path.abspath(sys.executable), r[1]); self.userExit()
            except Exception as e:
                log_error("portable update: %r" % e)
                self._dialog("Could not apply the update:\n%s" % str(e)[:90], [("OPEN DOWNLOAD PAGE", lambda: self._open_browser(RELEASES_URL)), ("CLOSE", self._close_dialog)])
        else:
            self._dialog("Download failed.\n%s" % r[1][1], [("OPEN DOWNLOAD PAGE", lambda: self._open_browser(RELEASES_URL)), ("CLOSE", self._close_dialog)])
        return task.done

    def _launch_swap_helper(self, exe, new):
        import subprocess
        pids = [os.getpid()]
        try: pids.append(os.getppid())
        except Exception: pass
        bat = os.path.join(tempfile.gettempdir(), "fireout_update_%d.bat" % os.getpid())
        lines = ["@echo off", "setlocal EnableDelayedExpansion", "set N=0"]
        for p in pids:
            lines += [":w%d" % p, 'tasklist /FI "PID eq %d" 2>NUL | find " %d " >NUL' % (p, p),
                      "if not errorlevel 1 (ping -n 2 127.0.0.1 >NUL & set /a N+=1 & if !N! LSS 120 goto w%d)" % p]
        lines += ["set T=0", ":swap", 'move /Y "%s" "%s" >NUL 2>&1' % (new, exe),
                  "if errorlevel 1 (ping -n 2 127.0.0.1 >NUL & set /a T+=1 & if !T! LSS 60 goto swap)",
                  'start "" "%s"' % exe, '(goto) 2>NUL & del "%~f0"']
        with open(bat, "w", encoding="mbcs" if os.name == "nt" else "utf-8") as f: f.write("\r\n".join(lines) + "\r\n")
        subprocess.Popen(["cmd.exe", "/c", bat], creationflags=0x00000008 | 0x00000200, close_fds=True, cwd=os.path.dirname(exe),
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _open_browser(self, url):
        import webbrowser
        webbrowser.open(url); self._close_dialog()


def main():
    try:
        App().run()
    except SystemExit:
        raise
    except Exception:
        log_error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
