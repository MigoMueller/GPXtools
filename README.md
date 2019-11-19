# GPXtools
Python tools to mess with (bicycle) GPS tracks. Includes stravaAtHome to interface with Strava.

## Installation

#### Pip installation (not recommended)
In principle, it's enough to just run
```bash
pip install .
```
in the directory containing this file (after cloning /downloading this repo from Github).  This assumes you have a working installation of Python3 including pip (which is fairly standard).  Pip should be able to ID and download all dependencies (although they may clash with version requirements by other Python packages you may have installed).

#### Installation within conda (recommended)
For extra safety and convenience, I recommend using a Python environment manager such as Anaconda (https://www.anaconda.com/distribution/).  A convenience script
```bash
installReqsInConda.bash
```
is provided that will create a conda environment 'gpx' containing all packages required by GPXtools.  It will also add the package nb_conda to your conda 'root' environment, allowing you to use the gpx kernel within Jupyter notebooks started from root.

Once the dependencies are installed, GPXtools can be installed using 
```bash
reinstallGPX.sh
```
If GPXtools is installed within a conda environment, remember to always activate it before using GPXtools!
```bash
conda activate
conda activate gpx
```

## Plotting tracks
```python
from GPXtools import gpxTools
tool=gpxTools.gpxTools()
tool.plotTracks(['track1.gpx', track2.gpx'])
```
... will plot two tracks on a map.  Map data will be retrieved from OSM.
The integer zoom level defaults to 10, but can be set manually using the parameter osmZoomLevel.
Work is in progress to let the script figure out an appropriate zoom level dynamically.

## Merging tracks
```python
from GPXtools import gpxTools
tool=gpxTools.gpxTools()
tool.mergeTracks(['track1.gpx','track2.gpx'], 'out.gpx')
```
... outputs a time-ordered GPX file in which the tracks in the input files are merged / concatenated.  There must be no time overlap between tracks.

This is useful to combine tracks taken before and after an extended break / GPS instrument failure.  Another use-case is to combine inbound and outbound legs of commute rides.

## Applying a privacy zone (rejecting track points within some distance around given points)
```python
from GPXtools import gpxTools
from units import unit as u
tool=gpxTools.gpxTools()
addresses=['Grote Markt, Groningen', '1 5th Avenue, New York City']
radii = [u('m')(100), u('mi')(0.2)]
gpxTools.applyPrivacyZone('interContinentalTrack.gpx', addresses, radii)
```

## stravaAtHome
GPXtools includes stravaAtHome, an interface for Strava access based on stravalib (https://github.com/hozn/stravalib) v0.10, which in turn is based on the Strava API v3.  Neither GPXtools nor stravaAtHome are affiliated with Strava in any way!

stravaAtHome includes a full authentication procedure that retrieves, stores, and refreshes Strava access tokens.  On the first run of the tool, users have to manually grant access.  Subsequent runs can be done in batch mode.  

Strava tokens will be saved on your local hard-drive in cleartext, i.e., unencrypted (the location and name of the file are specified by the user).  While stravaAtHome will not send your tokens anywhere, saving them unencrypted is, in principle, a security risk to your Strava account.  _I welcome any suggestions on how to improve this!_  In the meantime, proceed at your own risk.  

Strava authentication requires you to set-up a Strava API client, which is easy!  See https://www.strava.com/settings/api

Strava tokens are tied to your API account.  You can withdraw access to your API account, thereby invalidating all tokens, at any time in your Strava settings.  

#### Uploading tracks to Strava
See sample file `testStravaAtHome.py` along with `parms.yaml`.

#### More Strava goodness
... is under development ...
