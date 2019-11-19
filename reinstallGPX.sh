#!/bin/bash

# M.Mueller@astro.rug.nl, 2018/03/06
# Reinstall package GPXtools from a local directory.
# Assumes it's installed within a conda environment as below.

## Change as appropriate for your machine!
environmentName=gpx
moduleName=GPXtools
sourceDir=$HOME/git/GPXtools

source $(conda info --base)/etc/profile.d/conda.sh
conda activate $environmentName
if [ "$?" -ne "0" ]; then
    echo "Couldn't activate conda environment!"
    exit -1
fi 
pip uninstall $moduleName -y
if [ "$?" -ne "0" ]; then
    echo "Uninstalling "$moduleName" failed"
    exit -2
fi 
cd $sourceDir
if [ "$?" -ne "0" ]; then
    echo "Couldn't cd to "$sourceDir
    exit -3
fi 
pip install .
