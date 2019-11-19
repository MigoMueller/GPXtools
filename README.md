# GPXtools
Python tools to mess with (bicycle) GPS tracks 

### Installation
In principle, it should be enough to just run
```
pip install .
```
in the directory containing this file (after cloning this repo from Github).  This assumes you have a working installation of Python3 including pip (which is fairly standard).

For extra safety and convenience, I recommend using a Python environment manager such as Anaconda.  A convenience script
```
installReqsInConda.bash
```
is provided that will create a conda environment 'gpx' containing all packages required by GPXtools.  It will also add the package nb_conda to your conda 'root' environment, allowing you to use the gpx kernel within Jupyter notebooks started from root.
Once the dependencies are installed, GPXtools can be installed using 
```
reinstallGPX.sh
```
If GPXtools is installed within a conda environment, remember to always activate it before using GPXtools!
```
conda activate
conda activate gpx
```

### Plotting tracks
```
from gpxTools import gpxTools
tool=gpxTools()
tool.plotTracks(['track1.gpx', track2.gpx'])
```
... will plot two tracks on a map.  Map data will be retrieved from OSM.
The integer zoom level defaults to 10, but can be set manually using the parameter osmZoomLevel.
Work is in progress to let the script figure out an appropriate zoom level dynamically.

### Merging tracks
```
from gpxTools import gpxTools
tool=gpxTools()
tool.mergeTracks(['track1.gpx','track2.gpx'], 'out.gpx')
```
... outputs a time-ordered GPX file in which the tracks in the input files are merged / concatenated.  There must be no time overlap between tracks.

### Applying a privacy zone (rejecting track points within some distance around given points)
```
from gpxTools import gpxTools
from astropy import units as u
tool=gpxTools()
addresses=['Grote Markt, Groningen', '1 5th Avenue, New York City']
radii = [100*u.m, 12*u.km]
toolmapplyPrivacyZone('interContinentalTrack.gpx', addresses, radii)
```

### Uploading tracks to Strava
See sample file testStravaAtHome.py along with parms.yaml.
Requires you to set up a Strava API client, which is easy!  See https://www.strava.com/settings/api

### More Strava goodness
... is under development ...