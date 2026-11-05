"""EX SCREEN RECORDER 2026 - records FIREOUT SHINE's own rendered frames to an H.264 MP4.
Saves finished clips to the player's Downloads folder (%USERPROFILE%/Downloads on Windows).
No microphone. System-sound toggle is offered in the pause UI (off by default); frame capture is
the game view itself and needs no admin rights.
©2026 EX Inc./HYPERION DIGITAL ©2026"""
import os, sys, time, threading, subprocess, shutil, collections
from panda3d.core import Texture, GraphicsOutput

BRAND = "EX SCREEN RECORDER 2026"
FPS = 30
MAX_QUEUE = 24


def downloads_dir():
    """Real Downloads folder (FOLDERID_Downloads on Windows), else ~/Downloads."""
    if os.name == "nt":
        try:
            import ctypes, uuid
            from ctypes import wintypes
            class GUID(ctypes.Structure):
                _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]
            u = uuid.UUID("{374DE290-123F-4565-9164-39C4925E467B}"); g = GUID()
            g.Data1, g.Data2, g.Data3 = u.fields[0], u.fields[1], u.fields[2]
            for i, b in enumerate(u.bytes[8:]): g.Data4[i] = b
            p = ctypes.c_wchar_p()
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(p)) == 0:
                path = p.value; ctypes.windll.ole32.CoTaskMemFree(p)
                if path: return path
        except Exception:
            pass
        return os.path.join(os.environ.get("USERPROFILE") or os.path.expanduser("~"), "Downloads")
    return os.path.join(os.path.expanduser("~"), "Downloads")


def ffmpeg_exe(base=None):
    if base:
        for name in ("ffmpeg/ffmpeg.exe", "ffmpeg/ffmpeg", "ffmpeg.exe"):
            p = os.path.join(base, name)
            if os.path.exists(p): return p
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and os.path.exists(p): return p
    except Exception:
        pass
    return shutil.which("ffmpeg")


class Recorder:
    def __init__(self, app):
        self.app = app
        self.active = False
        self.proc = None; self.thread = None; self.path = None; self.error = None
        self.tex = None; self.start_t = 0.0; self.written = 0; self.size = None; self.fmt = None
        self.q = collections.deque(); self.cv = threading.Condition(); self.closing = False
        self.sys_sound = False          # UI toggle; frame capture is video-only (no mic, no admin)
        self._build_indicator()

    def _build_indicator(self):
        from direct.gui.DirectGui import DirectFrame, DGG
        import fs_ui as U
        a = self.app
        o = self.ind = DirectFrame(parent=a.a2dTopRight, frameColor=(0.05, 0.02, 0.04, 0.7),
                                   frameSize=(-0.62, -0.03, -0.14, -0.02), state=DGG.DISABLED)
        DirectFrame(parent=o, frameColor=(0.9, 0.08, 0.08, 1), frameSize=(-0.595, -0.565, -0.105, -0.055), state=DGG.DISABLED)
        self.ind_txt = U.text(o, "REC 00:00", (-0.30, -0.095), 0.036, fg=(1, 0.25, 0.25, 1), font=U.FONT_PLAIN)
        U.text(o, BRAND, (-0.30, -0.125), 0.018, fg=(1, 0.55, 0.55, 1), font=U.FONT_PLAIN)
        o.hide()
        a.task_mgr.add(self._tick_ind, "ex-screen-rec-ind", sort=55)

    def _tick_ind(self, task):
        if self.active and self.ind is not None and not self.ind.is_hidden():
            e = int(self.elapsed())
            try: self.ind_txt.setText("REC %02d:%02d" % (e // 60, e % 60))
            except Exception: pass
        return task.cont

    def elapsed(self):
        return time.time() - self.start_t if self.active else 0.0

    def start(self, out_dir=None):
        if self.active:
            return True
        exe = ffmpeg_exe(getattr(self.app, "BASE", None))
        if not exe:
            self.error = "ffmpeg not found"; return False
        out_dir = out_dir or downloads_dir()
        try: os.makedirs(out_dir, exist_ok=True)
        except Exception as e:
            self.error = "Downloads folder: %s" % e; return False
        win = self.app.win
        self.tex = Texture("ex-screen-rec")
        try:
            win.add_render_texture(self.tex, GraphicsOutput.RTM_copy_ram, GraphicsOutput.RTP_color)
        except Exception as e:
            self.error = "could not capture the game window (%s)" % e; self.tex = None; return False
        self.exe = exe
        self.path = os.path.join(out_dir, "FIREOUT SHINE Recording %s.mp4" % time.strftime("%Y-%m-%d %H-%M-%S"))
        self.proc = None; self.size = None; self.fmt = None; self.written = 0; self.error = None
        self.q.clear(); self.closing = False
        self.start_t = time.time()
        self.active = True
        try: self.ind.show()
        except Exception: pass
        self.app.task_mgr.add(self._grab, "ex-screen-rec-grab", sort=60)
        return True

    def _open_ffmpeg(self, w, h, pix):
        cmd = [self.exe, "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pix_fmt", pix, "-s", "%dx%d" % (w, h), "-r", str(FPS), "-i", "-",
               "-vf", "vflip,scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart",
               "-metadata", "comment=" + BRAND,
               "-metadata", "title=FIREOUT SHINE Recording", self.path]
        flags = 0x08000000 if os.name == "nt" else 0
        env = {k: v for k, v in os.environ.items() if not (k.upper().startswith("_PYI") or k.upper().startswith("_MEIPASS"))}
        env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                     creationflags=flags, env=env)
        self.thread = threading.Thread(target=self._writer, daemon=True)
        self.thread.start()

    def _grab(self, task):
        if not self.active:
            return task.done
        t = self.tex
        if not t.has_ram_image():
            return task.cont
        w, h = t.get_x_size(), t.get_y_size()
        if self.size is None:
            comps = t.get_num_components()
            if t.get_component_width() != 1 or comps not in (3, 4):
                self.error = "unsupported frame format"; self.stop(); return task.done
            self.size, self.fmt = (w, h), ("bgra" if comps == 4 else "bgr24")
            self._open_ffmpeg(w, h, self.fmt)
        if (w, h) != self.size:
            data = None
        else:
            data = bytes(memoryview(t.get_ram_image()))
        due = int((time.time() - self.start_t) * FPS) + 1 - self.written
        if due <= 0:
            return task.cont
        with self.cv:
            if data is not None and len(self.q) < MAX_QUEUE:
                self.q.append([data, due])
            elif self.q:
                self.q[-1][1] += due
            elif data is not None:
                self.q.append([data, due])
            else:
                self.q.append([None, due])
            self.written += due
            self.cv.notify()
        return task.cont

    def _writer(self):
        last = None
        try:
            while True:
                with self.cv:
                    while not self.q and not self.closing:
                        self.cv.wait(0.5)
                    if not self.q and self.closing:
                        break
                    data, n = self.q.popleft()
                if data is None:
                    data = last
                if data is None:
                    continue
                last = data
                for _ in range(n):
                    self.proc.stdin.write(data)
        except Exception as e:
            self.error = "encoder: %s" % e
        finally:
            try: self.proc.stdin.close()
            except Exception: pass

    def stop_async(self, done):
        if not self.active:
            return False
        self.active = False
        try: self.app.task_mgr.remove("ex-screen-rec-grab")
        except Exception: pass
        try: self.ind.hide()
        except Exception: pass
        res = {}
        def work():
            res["path"] = self._finalise()
        self._detach()
        th = threading.Thread(target=work, daemon=True); th.start()
        def poll(task):
            if th.is_alive():
                return task.cont
            done(res.get("path"))
            return task.done
        self.app.task_mgr.add(poll, "ex-screen-rec-finalise")
        return True

    def _detach(self):
        try: self.app.win.clear_render_textures()
        except Exception: pass
        self.tex = None

    def stop(self, timeout=30):
        if not self.active:
            return None
        self.active = False
        try: self.app.task_mgr.remove("ex-screen-rec-grab")
        except Exception: pass
        try: self.ind.hide()
        except Exception: pass
        self._detach()
        return self._finalise(timeout)

    def _finalise(self, timeout=30):
        self.active = False
        if self.proc is None:
            return None
        with self.cv:
            self.closing = True; self.cv.notify()
        if self.thread: self.thread.join(timeout)
        try: self.proc.wait(timeout)
        except Exception:
            try: self.proc.kill()
            except Exception: pass
            self.error = "encoder timed out"
        ok = self.proc.returncode == 0 and os.path.exists(self.path) and os.path.getsize(self.path) > 0
        if not ok and not self.error:
            try: err = (self.proc.stderr.read() or b"").decode("utf-8", "ignore")[-200:]
            except Exception: err = ""
            self.error = err or "encoder failed"
        self.proc = None
        return self.path if ok else None
