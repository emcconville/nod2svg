from setuptools import setup, find_packages
from codecs import open
from os import path

from nod2svg.main import VERSION

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='nod2svg',
    version=VERSION,
    description='Convert Nodal matrix to SVG',
    long_description=long_description,
    url='https://github.com/emcconville/nod2svg',
    author='Eric McConville',
    author_email='emcconville' '@' 'emcconville.com',
    maintainer='Eric McConville',
    maintainer_email='emcconville' '@' 'emcconville.com',
    license='GNU LGPL v3',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Multimedia :: Graphics :: Presentation',
    ],

    keywords='Nodal SVG',

    packages=['nod2svg'],

    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[],
    extras_require={'doc': ['Sphinx >=1.0']},
    package_data={},

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=[('', ['README.rst'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'nod2svg=nod2svg.main:main',
        ],
    },
)