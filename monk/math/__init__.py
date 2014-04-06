#
import pyximport
pyximport.install(setup_args={"include_dirs": '.', 'options': {
                  'build_ext': {}}}, reload_support=False)
