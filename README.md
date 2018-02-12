# GPXtools
Tools to mess with bicycle GPS tracks 

### Plotting tracks:
from gpxTools import gpxTools
tool=gpxTools()
tool.plotTracks(['track1.gpx', track2.gpx'])

... will plot two tracks on a map.  Map data will be retrieved from OSM.
The integer zoom level defaults to 10, but can be set manually using the parameter osmZoomLevel.
Work is in progress to let the script figure out an appropriate zoom level dynamically.

### Merging tracks
from gpxTools import gpxTools
tool=gpxTools()
tool.mergeTracks(['track1.gpx','track2.gpx'], 'out.gpx')

... outputs a time-ordered GPX file in which the tracks in the input files are merged / concatenated.  There must be no time overlap between tracks.

### Applying a privacy zone (rejecting track points within some distance around given points)

from gpxTools import gpxTools
from astropy import units as u
tool=gpxTools()
addresses=['Grote Markt, Groningen', '1 5th Avenue, New York City']
radii = [100*u.m, 12*u.km]
toolmapplyPrivacyZone('interContinentalTrack.gpx', addresses, radii)
