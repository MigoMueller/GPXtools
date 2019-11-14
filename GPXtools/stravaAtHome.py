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
import yaml
#import datetime # for downloads from Strava
#from lxml import etree # for extensions (sensors etc.)

class stravaAtHome( Client ):
    """ 
    Wrapper around stravalib.Client.
    Implemented authentication for single home users;
    secrets and tokens are stored in plain text, so 
    proceed at your own risk, and never use this tool for sensitive data!
    Methods:
      * checkScopes (did user grant all 'scopes' requested?)
      * uploadGPX
      * downloadGPX (to be implemented)

    Authentication partly based on code from
    https://github.com/ryanbaumann/Strava-Stream-to-CSV/blob/master/strava-to-csv.py

    M.Mueller@astro.rug.nl
    Version history:
    * 0.5: 2018/02/20: make pip installable
    * 0.6: 2018/03/08: improve GPX uploader
    * 0.7: 2019/10/28: update to stravalib 0.6 (refresh tokens)
    * 0.8: 2019/11/15: inherit from stravalib.Client
    """
    port = 5000
    redirectHost='localhost'

    def ensureAccess( self, thoroughCheck=False ):
        """
        Check if access token is fresh, refresh otherwise.
        Returns True if success, False otherwise.
        If thorough check is requested (either through flag here 
        or through override-flag in constructor), then
        check if we're able to actually connect to Strava.
        """
        if self.expires_at - time.time() < self.minTimeLeft :
            # access token is expired or will expire within self.minTimeLeft
            try :
                self.refreshAccessToken( )
            except AccessUnauthorized :
                print("Couldn't authenticate using refresh token!")
                return False
            except Exception as e:
                print("Something unexpected went wrong during authenticating (?)")
                print(e.__class__)
                print(str(e))
                raise
        if not (thoroughCheck or self.checkAccessAlwaysThorough) :
            return True
        # thorough check requested:
        try :
            dummy=self.get_athlete().weight # will fail if token invalid
            return True
        except AccessUnauthorized:
            print("Strava access not authenticated!")
            return False
        except Exception as e:
            print("Something unexpected went wrong during access to Strava (?)")
            print(e.__class__)
            print(str(e))
            raise          

        
    def authenticateFromFile( self, thoroughCheck=False ):
        """
        Read in tokens and expiry date from file, try and authenticate.
        Return value: False if failure, True otherwise
        """
        if not os.path.isfile(self.tokenFile):
            # Token file not present
            return False
        dummy = open(self.tokenFile).read().strip().split()
        assert len(dummy) == 3
        dummy[1] = int(dummy[1]) # expires_at is int (seconds since epoch)
        self.access_token = dummy[0]
        self.expires_at = dummy[1]
        self.refresh_token = dummy[2]
        ### If token present, can't check scopes granted (or can I?).
        ### Assume we have everything we need to prevent false negatives in checkScopes().
        self.scopesGranted = self.scopesNeeded
        return self.ensureAccess( thoroughCheck )


    def refreshAccessToken( self ):
        """
        Retrieve new access token + expiry date from Strava.  
        Save in client and in file.
        """
        try :
            refresh = self.refresh_token
        except :
            # No refresh token provided in file, yet can get here (e.g.: user declined authorization)
            return
        # retrieve from Strava
        response = self.refresh_access_token( \
            client_id=self.cl_id, client_secret=self.cl_secret, \
            refresh_token=self.refresh_token )
        # update in client
        self.updateTokens( response )
        return

    
    def updateTokens( self, response ):
        """ 
        Update access token, refresh token, and expiry date from response.
        Save tokens to file.
        Argument response assumed to be dictionary with three elements 'access_token', 'refresh_token', 'expires_at'
        """
        #print( 'Updating tokens in client')
        self.access_token = response['access_token']
        self.expires_at = response['expires_at']
        self.refresh_token = response['refresh_token']
        #athlete=self.get_athlete() # does access token work?  -- checking elsewhere, not here
        outputText = "%s %i %s"%(response['access_token'], response['expires_at'], response['refresh_token'])
        open(self.tokenFile, 'w').write(outputText+'\n')
        return

    
    def getAccessToken(self, code):
        """
        First Strava authentication (user @ HTTP server): 
        get tokens in exchange for code retrieved from web request.
        """
        #print("Requesting new tokens")
        response = self.exchange_code_for_token(
            client_id=self.cl_id, client_secret=self.cl_secret, code=code)
        self.updateTokens( response )
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
                self.stravaUploaderInstance.access_token = None
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

    
    def getUserConsent( self ):
        """
        Ask user to authorize Strava access using web request; 
        retrieve tokens from server and save them.
        """
        redirectUrl='http://'+self.redirectHost+':%d/authorized' % self.port
        authorize_url = self.authorization_url(client_id=self.cl_id, redirect_uri=redirectUrl, scope=self.scopesNeeded)
        httpd = self.StravaServer((self.redirectHost, self.port), self.StravaAuthHandler, self)
        dummy=webbrowser.open(authorize_url)
        httpd.handle_request()
        if self.access_token is None :
            # User denied authorization (see StravaAuthHandler.do_GET)
            print( "Please authorize this tool to access your Strava data; it won't work otherwise" )
            raise RuntimeError( 'Authorization denied' )
        return


    def readParmFile( self, parmFile ):
        """
        Read in parameter file (YAML format)
        Required:
        * clientIDfile (clientID,clientSecret)
        * tokenFile (will be generated by this tool)
        * scopesNeeded (list; reading requires activity:read_all, writing requires activity:write)
        * [.....]
        Optional:
        * minTimeLeft (min validity [in s] of access token after ensureAccess; default 3,600)

        """
        with open( parmFile, 'r' ) as f:
            try:
                parms = yaml.safe_load( f )
            except yaml.YAMLError as exc:
                print(exc)
                raise
        ## do some error checking: all required keywords present?
        ## Any that we don't want?
        print( parms )
        self.tokenFile = parms['tokenFile']
        self.clientIDfile = parms['clientIDFile']
        self.scopesNeeded = parms['scopesNeeded']
        if 'minTimeLeft' in parms :
            self.minTimeLeft = parms['minTimeLeft']
        else :
            self.minTimeLeft = 3600
        #assert False
        return

    
    def __init__( self, parmFile, batchmode=False, thoroughCheck=True, checkAccessAlwaysThorough=False, **keywords ):
        # batchmode: won't open web browser, neither to view track, nor to get user consent if no token is present
        # thoroughCheck: on first call to ensureAccess (in __init__), try to actually
        #   connect to Strava.  Else, access_token is only checked locally,
        #   against its expiry date.
        # checkAccessAlwaysThorough: all calls to ensureAccess are 'thorough'
        #   (overriding any possible user-provided parameters at call time)
        #
        ### Read in parm file
        self.readParmFile( parmFile )
        self.checkAccessAlwaysThorough=checkAccessAlwaysThorough
        self.batchmode = batchmode
        ## Parse arguments
        # Read in client ID and password:
        self.cl_id,self.cl_secret=open(self.clientIDfile).read().strip().split(',')

        super().__init__( **keywords )  # any extra keywords are passed on to stravalib.Client
        
        self.access_token=None # will overwrite any access token the user may have provided (that's not how this class is intended to be used, anyway)
        self.expires_at = 0
        if not self.authenticateFromFile( thoroughCheck ):
            if batchmode:
                print("No token present in batch mode: Strava authentication failed")
                return
            try :
                self.getUserConsent()
            except RuntimeError as e :
                print( e )
                return
            self.checkScopes()
        return


    def checkScopes( self ):
        if self.access_token is None :
            return False
        for s in self.scopesNeeded :
            if s not in self.scopesGranted :
                print( "Insufficient permissions granted: "+self.scopesGranted+", but need "+",".join(self.scopesNeeded) )
                print( "Consider deleting file ", self.tokenFile )
                return False
        return True

    
    def uploadGPX( self, inputFileName, activityType=None, activityName=None, commute=None, private=None ) :
        """
        Upload GPX file to Strava, return True if successful.
        If not self.batchmode, show uploaded activity in web browser.
        """
        # self.ensureAccess( thoroughCheck ) ## Leave it to user to ensure access!
        try:
            fileObject=open(inputFileName,'r')
        except:
            print( "Input file %s couldn't be opened for reading"%inputFileName )
            return False
        try:
            returnValue=self.upload_activity(fileObject, data_type='gpx', activity_type=activityType, private=True)
            ## set to private first, change later if requested
            print("Track uploaded to Strava, processing")
            while not returnValue.is_complete:
                print('.')
                time.sleep(1)
                returnValue.poll()
        except ActivityUploadFailed as e:
            print( "Strava upload failed:" )
            print( e )
            return False
        except Exception as e:
            print( e )
            print( e.__class__ )  
            raise
        if returnValue.is_error:
            print ('Upload failed!') # Can we ever get here?
            return False
        print('Upload succeeded!')
        activityID = returnValue.activity_id
        self.update_activity(activityID, name=activityName, commute=commute, private=private)
        if not self.batchmode:
            webbrowser.open('https://www.strava.com/activities/%i'%activityID)
        return True

