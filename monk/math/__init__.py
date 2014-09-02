#
import platform
import pyximport
if platform.system() == 'Windows':
    pyximport.install(setup_args={'include_dirs': '.', 'options': {'build_ext': {'compiler':'mingw32'}}}, reload_support=True)
else:
    pyximport.install(setup_args={"include_dirs": '.', 'options': {'build_ext': {}}}, reload_support=True)