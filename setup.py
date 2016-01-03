from setuptools import setup
from setuptools import find_packages

VERSION = '0.1dev'

requires = [
    'kemmer',
]
tests_require = requires + []

setup(name='dip2svg',
      version=VERSION,
      description='Prettier Schematics for DipTrace',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      entry_points="""\
      [console_scripts]
      dip2svg = dip2svg.main:main
      """)
