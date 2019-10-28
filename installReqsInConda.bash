#!/bin/bash

## Call with flag -y for all installs to be non-interactive.
## Otherwise, user gets to agree to all conda installs.

flag=
while getopts ":y" opt; do
  case $opt in
    y)
	flag='-y'
      ;;
    \?)
	echo "Invalid option: -$OPTARG" >&2
	exit 1
      ;;
  esac
done

source $(conda info --base)/etc/profile.d/conda.sh

conda activate root
conda install nb_conda $flag
# for kernels to appear in Jupyter notebooks
conda create --name gpx python=3 matplotlib ipykernel jupyter ipython lxml cartopy fiona $flag
# ipykernel: so this env shows up in Jupyter notebook
# lxml: speeds up gpxpy
# fiona: Pythonic IO-lib for geo data formats including gpx, shapes only (time info is forgotten).
conda activate gpx
if [ "$?" -eq "0" ]
then
    conda install -c conda-forge gpxpy $flag
    # support GPX files
    conda install -c conda-forge geopy $flag
    # retrieve coords of addresses
    pip install stravalib
    # Strava
fi
