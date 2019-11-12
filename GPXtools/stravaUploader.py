### Tool to upload GPX tracks to Strava (for a single user)
### M.Mueller@astro.rug.nl, 2018/02/20
### Save 'client ID' including password into file 'client.secret'
### and/or read-write token into file 'token'
### Strava uses OAuth2 for authentification.
### If valid token is present in file 'token', everything is straightforward.
### Otherwise, the code will open Strava in a browser window for user to grant permission (if needed); the token will then be saved locally.
###
### Main routine: constructor, like so:
### stravaUploader(gpxFileName, activityName='test', commute=True)

### Update 2019/11/09+: update to stravalib 0.6,
### Strava no longer accepts "forever tokens" but access / refresh tokens.
### Store access token in RAM, refresh token in file.

from stravalib import Client
from stravalib.exc import AccessUnauthorized, ActivityUploadFailed
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer 
import urllib.parse as urlparse
import os
import time
#import datetime # for downloads from Strava
#from lxml import etree # for extensions (sensors etc.)

class stravaUploader():
    """ 
    Upload GPX track to Strava.
    M.Mueller@astro.rug.nl, 2018/02/20
    For authentification, used some code from 
    https://github.com/ryanbaumann/Strava-Stream-to-CSV/blob/master/strava-to-csv.py
    (ported it to Python3, and used a trick to avoid global variables)
    Update 2019/11/09+, M.Mueller@astro.rug.nl:
      new Strava authentication scheme using access tokens and refresh tokens.
    """
    ### let these be defined in constructor:
    tokenFile='token' # access token; expiry date; refresh token
    clientIDfile = 'client.secret' # IDs my software: clientID,secret (separated by comma)
    scopesNeeded = ['activity:read_all','activity:write']  # hard-wire for now.  Make more flexible for stand-alone authenticator class?
    port = 5000
    redirectHost='localhost'

    tokenDictKeys = ['access_token', 'expires_at', 'refresh_token']
    
    def authenticateFromFile( self ):
        """
        Connect client using refresh token, return whether or not that succeeded
        """
        if not os.path.isfile(self.tokenFile):
            return False
        dummy = open(self.tokenFile).read().strip().split()
        assert len(dummy) == 3
        dummy[1] = int(dummy[1]) # expires_at is int (seconds since epoch)
        self.client.access_token = dummy[0]
        self.tokenDict = {}
        for k,v in zip(self.tokenDictKeys,dummy) :
            self.tokenDict[k]=v
        ### Check if access_token is valid for at least another hour
        if self.tokenDict['expires_at'] - time.time() > 3600 : # time in seconds since epoch
            ## future: if thoroughCheck do check
            print( 'access token should be good, still' )
            return True
        try:
            print( 'Refreshing access token' )
            self.refreshAccessToken( )
            ## throughCheck (see above)
            dummy=self.client.get_athlete().weight # will fail if token invalid
            return True
        except AccessUnauthorized:
            print("Couldn't authenticate using refresh token!")
            return False
        except Exception as e:
            print("Something unexpected went wrong during authenticating (?)")
            print(e.__class__)
            print(str(e))
            raise

    def refreshAccessToken( self ):
        """
        Retrieve new access token and save in client.  Save (new?) refresh token in file.
        """
        refreshToken = self.tokenDict['refresh_token']
        self.updateTokens( self.client.refresh_access_token( \
            client_id=self.cl_id, client_secret=self.cl_secret, \
            refresh_token=refreshToken ))
        return

    def updateTokens( self, response ):
        """ 
        Update access token, refresh token, and expiry date in self.client. 
        Save refresh token to file.
        Argument response assumed to be dictionary with three elements 'access_token', 'refresh_token', 'expires_at'
        """
        #print( 'Updating tokens in client')
        self.tokenDict = response
        self.client.access_token = self.tokenDict['access_token']
        athlete=self.client.get_athlete() # does access token work?
        outputText = "%s %i %s"%(response['access_token'], response['expires_at'], response['refresh_token'])
        open(self.tokenFile, 'w').write(outputText+'\n')
        return

    def getAccessToken(self, code):
        """
        Use temp code retrieved from web request to get access token and refresh token.
        Write refresh token to file.
        """
        #print("Requesting new tokens")
        self.updateTokens( self.client.exchange_code_for_token(
            client_id=self.cl_id, client_secret=self.cl_secret, code=code))
        return

    
    ## The trick to have the HTTP server populate the 'instance' inside the handler is copied from
    ## https://stackoverflow.com/questions/18444395/basehttprequesthandler-with-custom-instance#26724272
    class StravaServer(HTTPServer):
        def __init__(self,server_address, RequestHandlerClass,stravaUploaderInstance):
            HTTPServer.__init__(self,server_address,RequestHandlerClass)
            RequestHandlerClass.stravaUploaderInstance=stravaUploaderInstance
            return
    class StravaAuthHandler(BaseHTTPRequestHandler):
        """ Deal with web traffic to redirect URL (redirected from Strava, URL contains temp code)"""
        stravaUploaderInstance=None
        def do_HEAD (self):
            return self.do_GET()
        def do_GET(self):
            # Return to browser that it's safe to stop waiting, close window
            self.send_response(200)
            self.end_headers()
            self.wfile.write('Requested temporary access token from Strava.\n'.encode())
            #Get the API code for Strava
            try :
                code = urlparse.parse_qs(urlparse.urlparse(self.path).query)['code'][0]
            except KeyError :
                self.wfile.write("Access was denied by user".encode())
                self.stravaUploaderInstance.client.access_token = None
                return
            scope = urlparse.parse_qs(urlparse.urlparse(self.path).query)['scope'][0]
            self.stravaUploaderInstance.scopesGranted = scope
            self.wfile.write('Success!  Requesting permanent refresh token.\n'.encode())
            try:
                self.stravaUploaderInstance.getAccessToken(code)
                self.wfile.write('Strava authentication successful.\n'.encode())
            except Exception as e:
                print("Something went wrong:")
                print(e)
                print(e.__class__)
                self.wfile.write( (e.__str__()+'\n').encode() )
                ## Any cleaning-up to do?  Close HTTP server or something?
                raise
            return

    
    def getUserConsent(self):
        """
        Obtain and save an access token, user permitting.
        """
        redirectUrl='http://'+self.redirectHost+':%d/authorized' % self.port
        authorize_url = self.client.authorization_url(client_id=self.cl_id, redirect_uri=redirectUrl, scope=self.scopesNeeded)
        httpd = self.StravaServer((self.redirectHost, self.port), self.StravaAuthHandler, self)
        dummy=webbrowser.open(authorize_url)
        httpd.handle_request()
        if self.client.access_token is None :
            # User denied authorization (see StravaAuthHandler.do_GET)
            print( "Please authorize this tool to access your Strava data; it won't work otherwise" )
            raise RuntimeError( 'Authorization denied' )
        return

    
    def __init__( self, inputFileName, activityName=None, commute=None, private=None, batchmode=False, checkAccessAlwaysThorough=False ):
        # batchmode: won't open web browser, neither to view track, nor to get user consent if no token is present
        # checkAccessAlwaysThorough: when checking access, try to actually
        #   connect to Strava.  If False (and not set in calls to method
        #   ensureAccess), access_token is only checked locally,
        #   against its expiry date.
        #
        # !!!!!!!!
        # TO BE IMPLEMENTED 
        # !!!!!!!!
        #
        self.checkAccessAlwaysThorough=checkAccessAlwaysThorough
        self.client=Client()
        self.batchmode = batchmode
        # Read in client ID and password:
        self.cl_id,self.cl_secret=open(self.clientIDfile).read().strip().split(',')
        if not self.authenticateFromFile():
            if batchmode:
                print("No token present in batch mode: Strava authentication failed")
                return
            try :
                self.getUserConsent()
            except RuntimeError as e :
                print( e )
                return
            for s in self.scopesNeeded :
                if s not in self.scopesGranted :
                    print( "Insufficient permissions granted: "+self.scopesGranted+", but need "+",".join(self.scopesNeeded) )
                    print( "Consider deleting file ", self.tokenFile )
                    return
        try:
            fileObject=open(inputFileName,'r')
        except:
            print( "Input file %s couldn't be opened for reading"%inputFileName )
            return
        try:
            returnValue=self.client.upload_activity(fileObject, data_type='gpx', activity_type='ride', private=True)
            print("Track uploaded to Strava, processing")
            while not returnValue.is_complete:
                print('.')
                time.sleep(1)
                returnValue.poll()
        except ActivityUploadFailed as e:
            print("Strava upload failed:")
            print(e)
            return
        except Exception as e:
            print(e)
            print(e.__class__)  
            raise
        if returnValue.is_error:
            print ('Upload failed!') # Can we ever get here?
            return
        print('Upload succeeded!')
        activityID = returnValue.activity_id
        self.client.update_activity(activityID, name=activityName, commute=commute, private=private)
        if not batchmode:
            webbrowser.open('https://www.strava.com/activities/%i'%activityID)
        return

