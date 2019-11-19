#!/usr/bin/env python

from GPXtools import stravaAtHome
import os

# set to any GPS file you wish to upload
testFile = '20180606_163314.gpx'
assert os.path.isfile(testFile)
parmsFile = 'parms.yaml'

strava = stravaAtHome( parmsFile, batchmode=False, checkAccessAlwaysThorough=True )
if not strava.checkScopes() :
    ## User didn't grant necessary scopes (or no permissions at all)
    print( "You didn't provide the required authorizations, quit." )
    assert False
if strava.ensureAccess() :
    strava.uploadFile( testFile, activityName='test', activityType='ride' )
else :
    print( "Somehow we don't seem to have Strava access anymore..." )
    ## Don't see how we could ever get here, seeing we've just
    ## authenticated above, but you never know



