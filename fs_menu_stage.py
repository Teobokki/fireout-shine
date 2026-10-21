"""Main-menu stage: ANA and DANIEL (in-game Blender models) posed beside the KAGEROU GT-S in the live neon city."""
from fs_vehicle import Car
from fs_people import Person


class _Stub:
    def __init__(self, app):
        self.app = app; self.world = app.world; self.time = 0.0
    def on_impact(self, *a): pass
    def on_car_water(self, *a): pass


class Stage:
    def __init__(self, app):
        g = self.g = _Stub(app)
        save = app.load_save() or {}
        cfg = (save.get("cars") or {}).get("gts", {})
        self.car = Car(g, "gts", -1.2, -40.0, 28.0, tuple(cfg.get("paint", (0.20, 0.22, 0.28))), cfg.get("plate", "SHINE 01"), True, "player")
        self.car.sync(0.0)
        self.ana = Person(g, "ana", 1.9, -42.6, 200.0)
        self.dan = Person(g, "daniel", 3.0, -41.4, 165.0)
        for p in (self.ana, self.dan): p.sync()
        app.task_mgr.add(self._t, "stage-anim")

    def _t(self, task):
        import math
        self.g.time = task.time
        self.ana.model.set_r(math.sin(task.time * 1.3) * 0.8); self.dan.model.set_r(math.sin(task.time * 1.1 + 1) * 0.8)
        return task.cont

    def destroy(self):
        self.g.app.task_mgr.remove("stage-anim")
        self.car.destroy(); self.ana.destroy(); self.dan.destroy()
