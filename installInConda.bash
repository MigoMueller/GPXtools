#!/bin/bash
conda create --name gpx -python=3 astropy matplotlib ipykernel ipython lxml cartopy fiona
# ipykernel: so this env shows up in Jupyter notebook
# lxml: speeds up gpxpy
# fiona: Pythonic IO-lib for geo data formats including gpx, shapes only (time info is forgotten).
source activate gpx
conda install -c conda-forge gpxpy
# support GPX files
conda install -c conda-forge geopy 
# retrieve coords of addresses

source activate root
conda install nb_conda
# for kernels to appear in Jupyter notebooks

source activate gpx
