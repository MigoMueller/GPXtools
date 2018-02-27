### GPX tools
### M.Mueller@astro.rug.nl, 2018/02/06+

# Tools to view, merge, and manipulate GPX tracks from bike apps.

# TODO: 
# * Develop tool to fill time gaps (think: in Tahuna coverage) with 'filler' file (think: Strava file or files)
# * Overload privacyZone and stravaUpload so as to work from files in memory (ASCII lists?) rather than on the disk.  Parm fileOutput=True or something.
# * in merge / privacyZone: correct bounding box / trip length (Strava keeps correcting them)


import matplotlib.pyplot as plt

import gpxpy.parser as gpxParser
import numpy as np
import astropy.units as u
import glob
import gpxpy
import fiona
import sys

import cartopy.crs as ccrs
from cartopy.io.img_tiles import OSM
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import shapely.geometry as sgeom

import os.path
import requests

class gpxTools:
    plotColors=['black', 'red', 'green', 'blue', 'yellow', 'orange']

    def plotTracks(self, files, osmZoomLevel=10, padding=0.1):
        # ToDo: adapt OSM zoom level automatically
        # Make plot interactive, allow user to zoom, scroll, pan; adapt map bg accordingly
        # Padding: add padding on all four sides so tracks don't end at edge of map.  0.1: 10% padding on all sides.
        if len(files) == 0:
            raise ValueError("gpxTools.plotTracks: need at least one file to work with!")
        if padding < 0:
            raise ValueError("gpxTools.plotTracks: padding value is %f; needs to be non-negative."%padding)
        # Open with fiona:
        # Straightforward to generate shapes, but doesn't retain time information.
        trackShapes=[]
        # extent: bounding box for map plot: minLon, maxLon, minLat, maxLat
        extent=[sys.float_info.max, sys.float_info.min, sys.float_info.max, sys.float_info.min]
        for fn in files:
            tracks=fiona.open(fn, layer='tracks')
            for track in tracks:
                coords=track['geometry']['coordinates']
                shp=sgeom.MultiLineString(coords)
                # shp.bounds has different order than extent...
                if shp.bounds[0]<extent[0]:
                    extent[0] = shp.bounds[0] 
                if shp.bounds[2] > extent[1]:
                    extent[1]=shp.bounds[2]
                if shp.bounds[1] < extent[2]:
                    extent[2] = shp.bounds[1]
                if shp.bounds[3] > extent[3]:
                    extent[3] = shp.bounds[3]
                trackShapes.append(shp)
            # Add padding:
            lonShift=padding*(extent[1]-extent[0])
            extent[0]=extent[0]-lonShift
            extent[1]=extent[1]+lonShift
            latShift=padding*(extent[3]-extent[2])
            extent[2]=extent[2]-latShift
            extent[3]=extent[3]+latShift
            # Start plotting
            osm=OSM()
            # Following https://ocefpaf.github.io/python4oceanographers/blog/2015/08/03/fiona_gpx/
            ax = plt.axes(projection=osm.crs)
            gl=ax.gridlines(draw_labels=True)
            gl.xlabels_top = gl.ylabels_right = False
            gl.xformatter = LONGITUDE_FORMATTER
            gl.yformatter = LATITUDE_FORMATTER
            ax.set_extent(extent)
            ax.add_image(osm,osmZoomLevel) 
            ## Fiona
            for i, track in enumerate(trackShapes):
                ax.add_geometries(track, crs=ccrs.PlateCarree(), edgecolor=self.plotColors[i % len(self.plotColors)], linewidth=2, facecolor='none')
            plt.tight_layout()
            plt.show()
            return

    ###
    ### Add: check that segments don't overlap in time (not tracks)
    ### Append segments, not tracks
    ### Check if time gaps can be filled using fillers
    def mergeTracks(self, fileNames, outFileName, fillers=[]):
        # Read in files
        gpxes=[]
        for fn in fileNames:
            with open(fn, 'r') as f:
                parser=gpxParser.GPXParser(f)
                parser.parse()
                gpx=parser.gpx
                gpxes.append(gpx)
                print ("Done reading in ", fn)
        # Sort by time
        startTimes=[]
        endTimes=[]
        for gpx in gpxes:
            startTimes.append(gpx.tracks[0].segments[0].points[0].time)
            endTimes.append(gpx.tracks[-1].segments[-1].points[-1].time)
        idx=np.argsort(startTimes)
        gpxesSorted=np.array(gpxes)[idx]
        fnSorted=np.array(files)[idx]
        startTimesSorted=np.array(startTimes)[idx]
        endTimesSorted=np.array(endTimes)[idx]

        # Make sure there's no time overlap between files
        for i in range(len(startTimesSorted)-1):
            if not startTimesSorted[i+1] > endTimesSorted[i]:
                print("Time overlap between files %i and %i"%(i,i+1))
                print(fnSorted[i], fnSorted[i+1])
                print("Endtime of first: ", endTimesSorted[i])
                print("StartTime of second:", startTimesSorted[i+1])
                assert False
        for fn, start, end in zip(fnSorted, startTimesSorted, endTimesSorted):
            print (fn, start, end)

        out=gpxesSorted[0]
        for gpx in gpxesSorted[1:]:
            for track in gpx.tracks:
                out.tracks.append(track)
        output=out.to_xml()
        with open(outFileName, 'w') as out:
            out.write(output)

# ### Geocoding: get coords matching address and vice-versa.
# Get coords of addresses using geopy: https://pypi.python.org/pypi/geopy  -- maybe make that geocoder, instead (actively developed as of Feb 2018)

from geopy.geocoders import Nominatim
def getCoordsFromAddress(address):
    geolocator=Nominatim()
    return geolocator.geocode(address)
def getAddressFromCoords(coordString):
    geolocator=Nominatim()
    return geolocator.reverse(coordString)

#geolocator.geocode('Voorstraat 80, 8715JC ')
#geolocator.reverse('52, 15')
#geolocator.geocode('Kassel')
#geolocator.geocode('Hilo').latitude

class privacyZone:
    def __init__(self, addresses, radii):
        self.radii=[r.to(u.meter).value for r in radii]
        if len(addresses) != len(radii):
            print("Please provide one radius per address / coordinate!")
            print(len(addresses), "addresses / coordinates were passes,")
            print(len(radii), "radii.")
            raise ValueError("gpxTools:privacyZone: nAddresses != nRadii")
        try:
            addresses[0].latitude
            self.coords=addresses # assume coordinates were passed instead of addresses; no need to call Nominatim
            return
        except AttributeError:
            pass # assume addresses were passes
        self.coords=[self.getCoordsFromAddress(add) for add in addresses]
        return
    def isPointTooClose(self, p):
        for coo, r in zip(self.coords, self.radii):
            if p.distance_2d(coo) < r:
                return True
        return False
    
def applyPrivacyZone(inFileName, coordsAddresses, radii, outFileName=None):
    """
    Copy GPX track from inFileName into outFileName, rejecting all waypoints
    within a "privacy zone" defined in arrays (of equal length!)
    "coordsAddresses" (GPS coordinates or unquely resolvable addresses)
    and "radii" (as Astropy Quantities).
    outFileName defaults to inFile_pz.gpx 
    """
    if outFileName is None:
        outFileName=inFileName[:inFileName.index('.gpx')]+'_pz.gpx'
    pz = privacyZone(coordsAddresses, radii)
    with open(inFileName, 'r') as f:
        parser=gpxParser.GPXParser(f)
        parser.parse()
        gpx=parser.gpx
    # Delete points within privacyZone
    for track in gpx.tracks:
        for seg in track.segments:
            ### Watch out: can't pop from a list while iterating (forward!) over it
            ###   (it's not syntactically forbidden, but it messes with indexing)
            ### So, iterating backward.
            for i in range(len(seg.points)-1, -1, -1):
                if pz.isPointTooClose(seg.points[i]):
                    seg.points.pop(i)
    with open(outFileName, 'w') as out:
        out.write(gpx.to_xml())
    return

def getGpxFromTahuna(linkFileName, outFileName='track.gpx'):
    """
    linkFileName = link to GPX track page generated by Tahuna app
    Download GPX track to file outFileName.
    M.Mueller@astro.rug.nl, 2018/02/19
    """
    if not os.path.isfile(linkFileName):
        raise ValueError("Can't open "+linkFileName)
    if os.path.isfile(outFileName):
        raise ValueError("Output file "+outFileName+" already exists!")
    url1 = open(linkFileName).read().strip()
    trackUrl=None
    with requests.get(url1) as r:
        lines=r.text.split('\n')
        for line in lines:
            # Extract download URL from first line containing href and ?uniqueid
            if ('?uniqueid' in line) and ('href' in line):
                # URL sits between ""
                trackUrl=line.split('"')[1]
                break
    if trackUrl is None:
        raise ValueError("Couldn't find URL pointing to track in file linked from %s"%linkFileName)
    out=open(outFileName, 'w')
    # requests.get takes care of uncompressing content:
    with requests.get(trackUrl) as r: 
        for line in r:
            out.write(line.decode())
    return
    



