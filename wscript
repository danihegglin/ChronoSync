# -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-

VERSION='0.1'
APPNAME='ChronoSync'

from waflib import Configure, Build, Logs

def options(opt):
    opt.load('compiler_c compiler_cxx gnu_dirs')
    opt.load('boost doxygen protoc', tooldir=["waf-tools"])

    syncopt = opt.add_option_group ("ChronoSync Options")

    syncopt.add_option('--debug',action='store_true',default=False,dest='debug',help='''debugging mode''')
    syncopt.add_option('--log4cxx', action='store_true',default=False,dest='log4cxx',help='''Compile with log4cxx''')
    syncopt.add_option('--test', action='store_true',default=False,dest='_test',help='''build unit tests''')

def configure(conf):
    conf.load('compiler_c compiler_cxx gnu_dirs boost')

    if conf.options.debug:
        conf.define ('_DEBUG', 1)
        conf.add_supported_cxxflags (cxxflags = ['-O0',
                                                 '-Wall',
                                                 '-Wno-unused-variable',
                                                 '-g3',
                                                 '-Wno-unused-private-field', # only clang supports
                                                 '-fcolor-diagnostics',       # only clang supports
                                                 '-Qunused-arguments'         # only clang supports
                                                 ])
    else:
        conf.add_supported_cxxflags (cxxflags = ['-O3', '-g'])

    conf.check_cfg(package='libndn.cxx', args=['--cflags', '--libs'], uselib_store='NDNCXX', mandatory=True)
    conf.check_cfg(package='openssl', args=['--cflags', '--libs'], uselib_store='OPENSSL', mandatory=True)

    conf.check_boost(lib='system iostreams test thread')

    if conf.options.log4cxx:
        conf.check_cfg(package='liblog4cxx', args=['--cflags', '--libs'], uselib_store='LOG4CXX', mandatory=True)

    if conf.options._test:
      conf.define('_TEST', 1)

    try:
        conf.load('doxygen')
    except:
        pass

    conf.load('protoc')

def build (bld):
    libsync = bld (
        target="ChronoSync",
        vnum = "1.0.0",
        features=['cxx', 'cxxshlib'],
        source =  bld.path.ant_glob (['src/**/*.cc', 'src/**/*.proto']),
        use = 'BOOST BOOST_IOSTREAMS BOOST_THREAD SSL NDNCXX OPENSSL',
        includes = ['src'],
        )
    
    # Unit tests
    if bld.get_define("_TEST"):
      unittests = bld.program (
          target="unit-tests",
          source = bld.path.ant_glob(['tests/**/*.cc']),
          features=['cxx', 'cxxprogram'],
          use = 'BOOST_TEST ChronoSync',
          includes = ['src'],
          )

    if bld.get_define ("HAVE_LOG4CXX"):
        libsync.use += ' LOG4CXX'
        if bld.get_define("_TEST"):
            unittests.use += ' LOG4CXX'

    bld.install_files (
        dest = "%s/ChronoSync" % bld.env['INCLUDEDIR'], 
        files = bld.path.ant_glob(['src/**/*.h']), 
        cwd = bld.path.find_dir ("src"),
        relative_trick = True,
        )

    bld.install_files (
        dest = "%s/ChronoSync" % bld.env['INCLUDEDIR'], 
        files = bld.path.get_bld().ant_glob(['src/**/*.h']), 
        cwd = bld.path.get_bld().find_dir ("src"),
        relative_trick = True,
        )

    pc = bld (
        features = "subst",
        source='ChronoSync.pc.in',
        target='ChronoSync.pc',
        install_path = '${LIBDIR}/pkgconfig',
        PREFIX       = bld.env['PREFIX'],
        INCLUDEDIR   = "%s/ChronoSync" % bld.env['INCLUDEDIR'],
        VERSION      = VERSION,
        )

# doxygen docs
from waflib.Build import BuildContext
class doxy (BuildContext):
    cmd = "doxygen"
    fun = "doxygen"

def doxygen (bld):
    if not bld.env.DOXYGEN:
        bld.fatal ("ERROR: cannot build documentation (`doxygen' is not found in $PATH)")
    bld (features="doxygen",
         doxyfile='doc/doxygen.conf',
         output_dir = 'doc')

@Configure.conf
def add_supported_cxxflags(self, cxxflags):
    """
    Check which cxxflags are supported by compiler and add them to env.CXXFLAGS variable
    """
    self.start_msg('Checking allowed flags for c++ compiler')

    supportedFlags = []
    for flag in cxxflags:
        if self.check_cxx (cxxflags=[flag], mandatory=False):
            supportedFlags += [flag]

    self.end_msg (' '.join (supportedFlags))
    self.env.CXXFLAGS += supportedFlags
