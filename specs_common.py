# shared PyInstaller config for FIREOUT SHINE
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files
import os, glob
DROP = ('avcodec', 'avformat', 'avutil', 'swresample', 'swscale', 'libp3ffmpeg', 'fmod', 'assimp', 'ptloader',
        'bullet', 'pandaode', 'pandaai', 'vrpn', 'p3vision', 'pandadx9', 'd3dx9', 'cgd3d9', 'pandaphysics', 'pandafx')
BINS = [x for x in collect_dynamic_libs('panda3d') if not any(k in os.path.basename(x[0]).lower() for k in DROP)]
DATAS = collect_data_files('panda3d', includes=['etc/*'])
ASSETS = [(f, 'assets') for f in ('assets/cover.jpg', 'assets/backdrop.jpg', 'assets/icon.ico', 'assets/icon.png', 'assets/ui_font.ttf',
                                  'assets/ui_plain.ttf', 'assets/jp_font.otf')]
ASSETS += [('assets/sfx', 'assets/sfx'), ('assets/voice', 'assets/voice'), ('assets/tex', 'assets/tex')]
ASSETS += [(f, 'assets/models') for f in glob.glob('assets/models/*.bam')]
ASSETS += [(f, 'assets/models') for f in glob.glob('assets/models/*.json')]   # v1.0.3: SELMOTES face patches
HIDDEN = ['panda3d.core', 'panda3d.direct', 'direct.showbase.ShowBase', 'direct.gui.DirectGui', 'direct.filter.CommonFilters',
          'fs_game', 'fs_game_banter', 'fs_world', 'fs_geom', 'fs_vehicle', 'fs_people', 'fs_ai', 'fs_ui', 'fs_data', 'fs_lines',
          'fs_shaders', 'fs_menu_stage', 'fs_weapons']
EXCL = ['matplotlib', 'scipy', 'pandas', 'IPython', 'pytest', 'tkinter', 'PIL', 'cv2', 'wx', 'PyQt5', 'imageio_ffmpeg', 'numpy']
