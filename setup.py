from setuptools import setup, find_packages


__version__ = '0.8'

setup(
    name='GPXtools',
    version=__version__,
    author='Migo Mueller',
    author_email='m.mueller@astro.rug.nl',
    install_requires=[
        'numpy',
        'gpxpy',
        'geopy',
        'stravalib',
        'units',
        'matplotlib',
        'fiona',
        'cartopy',
        'shapely',
        'pyyaml'
    ],
    license='LICENSE.txt',
    description='Tools to mess with bicycle GPS tracks.',
    keywords = ['GPS', 'GPX', 'bicycle', 'sport'],
    packages=['GPXtools'],
    classifiers = [
        "Programming Language :: Python :: 3.5",
        "Operating System :: OS Independent"
        #"Intended Audience :: Science/Research/DataAnalysis",
        #"License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        #"Topic :: Scientific/Engineering"
    ],
    include_package_data=True
)
