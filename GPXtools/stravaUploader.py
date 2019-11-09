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
    refreshTokenFile='token' # read-write access to athlete's data
    clientIDfile = 'client.secret' # IDs my software: clientID,secret (separated by comma)
    scopesNeeded = ['activity:read_all','activity:write']  # hard-wire for now.  Make more flexible for stand-alone authenticator class?
    port = 5000
    redirectHost='localhost'

    def authenticateFromRefreshToken(self, refreshToken=None):
        """
        Connect client using refresh token, return whether or not that succeeded
        """
        if refreshToken is None:
            if not os.path.isfile(self.refreshTokenFile):
                return False        
            refreshToken=open(self.refreshTokenFile).read().strip()
        try:
            self.refreshAccessToken( refreshToken )
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

    def refreshAccessToken( self, refreshToken=None ):
        """
        Retrieve new access token and save in client.  Save (new?) refresh token in file.
        """
        if refreshToken is None :
            refreshToken = client.token_response['refresh_token']
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
        self.client.token_response = response
        self.client.access_token = self.client.token_response['access_token']
        self.client.token_expires_at = self.client.token_response['expires_at']
        athlete=self.client.get_athlete() # does access token work?
        self.client.authenticated=True
        open(self.refreshTokenFile, 'w').write(self.client.token_response['refresh_token']+'\n')
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
                assert False # think of some better error handling here...
            scope = urlparse.parse_qs(urlparse.urlparse(self.path).query)['scope'][0]
            for s in self.stravaUploaderInstance.scopesNeeded:
                assert s in scope # This, too, needs refinement.....
            self.wfile.write('Success!  Requesting permanent access token.\n'.encode())
            try:
                self.stravaUploaderInstance.getAccessToken(code)
                self.wfile.write('Success!  Now upload track.\n'.encode())
            except Exception as e:
                print("Something went wrong:")
                print(e)
                print(e.__class__)
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
        # Obtain and save refresh token, and authenticate self.client
        return

    
    def __init__(self, inputFileName, activityName=None, commute=None, private=None, batchmode=False):
        # batchmode: won't open web browser, neither to view track, nor to get user consent if no token is present
        self.client=Client()
        # Read in client ID and password:
        self.cl_id,self.cl_secret=open(self.clientIDfile).read().strip().split(',')
        if not self.authenticateFromRefreshToken():
            if batchmode:
                print("No token present in batch mode: Strava upload failed")
                return
            self.getUserConsent()
        try:
            fileObject=open(inputFileName,'r')
        except:
            # file couldn't be opened for reading
            raise
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

