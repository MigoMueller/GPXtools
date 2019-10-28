#!/bin/bash
conda activate root
conda install nb_conda -y
# for kernels to appear in Jupyter notebooks
conda create --name gpx python=3 astropy matplotlib ipykernel jupyter ipython lxml cartopy fiona -y
# ipykernel: so this env shows up in Jupyter notebook
# lxml: speeds up gpxpy
# fiona: Pythonic IO-lib for geo data formats including gpx, shapes only (time info is forgotten).
conda activate gpx
if [ "$?" -eq "0" ]
then
    conda install -c conda-forge gpxpy -y
    # support GPX files
    conda install -c conda-forge geopy -y
    # retrieve coords of addresses
    pip install stravalib
    # Strava
fi
