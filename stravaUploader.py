### Tool to upload GPX tracks to Strava (for a single user)
### M.Mueller@astro.rug.nl, 2018/02/20
### Save 'client ID' including password into file 'client.secret'
### and/or read-write token into file 'token'
### Strava uses OAuth2 for authentification.
### If valid token is present in file 'token', everthing is straightforward.
### Otherwise, the code will open Strava in a browser window for user to grant permission (if needed); the token will then be saved locally.
###
### Main routine: constructor, like so:
### stravaUploader(gpxFileName, activityName='test', commute=True)

## To do:
## * instead of ASCII file, move token into OS keyring (import keyring or something)

from stravalib import Client
from stravalib.exc import AccessUnauthorized, ActivityUploadFailed
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer 
import urllib.parse as urlparse
import os
import time

class stravaUploader():
    """ 
    Upload GPX track to Strava.
    M.Mueller@astro.rug.nl, 2018/02/20
    For authentification, used some code from 
    https://github.com/ryanbaumann/Strava-Stream-to-CSV/blob/master/strava-to-csv.py
    (ported it to Python3, and used a trick to avoid global variables)
    """
    tokenFile='token' # read-write access to athlete's data
    clientIDfile = 'client.secret' # IDs my software: clientID,secret (separated by comma)
    port = 5000
    redirectHost='localhost'
    
    def authenticateFromToken(self, token=None):
        """Connect client to token, return whether or not that succeeded"""
        if token is None:
            if not os.path.isfile(self.tokenFile):
                return False        
            token=open(self.tokenFile).read().strip()
        try:
            self.client.access_token=token
            dummy=self.client.get_athlete().weight # will fail if token invalid
            return True
        except AccessUnauthorized:
            print("Couldn't authenticate using token!")
            return False
        except Exception as e:
            print("Something unexpected went wrong during authenticating (?)")
            print(e.__class__)
            print(str(e))
            raise
        
    def getAccessToken(self,code):
        """
        Use temp code retrieved from web request to get access token, save to file.
        """
        #print("Requesting access token")
        access_token = self.client.exchange_code_for_token(client_id=self.cl_id,
                                                    client_secret=self.cl_secret, code=code)
        if not self.authenticateFromToken(access_token):
            raise ValueError("Access token just obtained doesn't appear to work!")
        print("Writing token to file")
        open(self.tokenFile, 'w').write(access_token+'\n')
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
            code = urlparse.parse_qs(urlparse.urlparse(self.path).query)['code'][0]
            self.wfile.write('Success!  Requesting permanent access token.\n'.encode())
            try:
                self.stravaUploaderInstance.getAccessToken(code)
                self.wfile.write('Success!  Now upload track.\n'.encode())
            except Exception as e:
                print("Something went wrong:")
                print(e)
                print(e.__class__)
                ## Any cleaning up to do?  Close HTTP server or something?
                raise
            return    
    def getUserConsent(self):
        """Obtain and save an access token, user permitting."""
        # Read in client ID and password:
        self.cl_id,self.cl_secret=open(self.clientIDfile).read().strip().split(',')
        redirectUrl='http://'+self.redirectHost+':%d/authorized' % self.port
        authorize_url = self.client.authorization_url(client_id=self.cl_id, redirect_uri=redirectUrl, scope='view_private,write')
        httpd = self.StravaServer((self.redirectHost, self.port), self.StravaAuthHandler, self)
        dummy=webbrowser.open(authorize_url)
        httpd.handle_request()  
        # This should obtain and save token, and authenticate self.client
        return
    def __init__(self, inputFileName, activityName=None, commute=None, private=None):
        self.client=Client()
        if not self.authenticateFromToken():
            self.getUserConsent()
        try:
            fileObject=open(inputFileName,'r')
        except:
            # file couldn't be opened for reading
            raise
        try:
            returnValue=self.client.upload_activity(fileObject, data_type='gpx', activity_type='ride', private=True)
            print("Track uploaded to Strava, processing")
        except ActivityUploadFailed as e:
            print("Strava upload failed:")
            print(e)
            return
        except Exception as e:
            print(e)
            print(e.__class__)  
            raise
        while not returnValue.is_complete:
            print('.')
            time.sleep(1)
            returnValue.poll()
        if returnValue.is_error:
            print ('Upload failed!')
            return
        print('Upload succeeded!')
        activityID = returnValue.activity_id
        self.client.update_activity(activityID, name=activityName, commute=commute, private=private)
        webbrowser.open('https://www.strava.com/activities/%i'%activityID)
        return

