from setuptools import setup, find_packages

setup(
    name="fandango",
    version="0.1",
    packages = find_packages(),
    description="Simplify the configuration of big Tango control systems",
    long_description="Simplify the configuration of big Tango control systems; "
    "implementing the behavior of Jive (configuration) and/or Astor (deployment) "
    "tools in methods that could be called from scripts using regexp and "
    "wildcards.",
    author = "Sergi Rubio",
    author_email = "srubio@cells.es",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
    ],
    platforms=[ "Linux,Windows XP/Vista/7/8" ],
    install_requires=['PyTango>=8'])
