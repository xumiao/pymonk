# Need cython to be installed
import pyximport; pyximport.install(setup_args={"include_dirs":'.', 'options': { 'build_ext': { 'compiler': 'mingw32' }}}, reload_support=True)
#@todo add twisted to asynchronize network communication and training handling