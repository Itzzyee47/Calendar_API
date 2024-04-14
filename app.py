import os,datetime
import flask
import requests
import firebase_admin
from firebase_admin import credentials,db
from flask import render_template, redirect, request,session
from datetime import datetime as dt
from datetime import timedelta as td

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "credentials.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/calendar','https://www.googleapis.com/auth/userinfo.email']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

app = flask.Flask(__name__)

cred = credentials.Certificate("cred.json")
firebase_admin.initialize_app(cred,{"databaseURL":"https://meetingz-f9fd1-default-rtdb.europe-west1.firebasedatabase.app/"})

ref = db.reference("/booked")


# Note: A secret key is included in the sample so that it works.
# If you use this code in your application, replace this with a truly secret
# key. See https://flask.palletsprojects.com/quickstart/#sessions.
app.secret_key = 'moinfoubwsem32kj'


@app.route('/')
def index():
  
  db = ref.get()
  context = {"db":db,"name":"DB_Trys"}
  return flask.render_template("index.html",**context)

@app.route('/t',methods=["post","get"])
def test():
  
  return flask.render_template("test.html")

@app.route('/t2',methods=["post"])
def test2():
  if flask.request.method == "POST":
    data = request.form.to_dict()
    context = {"db":data,"name":"DB_Trys"}
    
    return flask.render_template("test2.html",**context)
  
  return flask.redirect(flask.url_for('test'))

@app.route('/meet',methods=["POST"])
def meet():
  if flask.request.method == "POST":
    date = flask.request.form.get("date")
    email = flask.request.form.get("email")
    duration = td(days=0,  hours=2, minutes=0)
    date_format = '%Y-%m-%dT%H:%M'
    date_obj = dt.strptime(date, date_format)
    endDate = date_obj + duration
    flask.session["date"] = date_obj
    flask.session["endDate"] = endDate
    flask.session["email"] = email
    
  # return f'<h1>The start date: {date_obj}<br> The end date: {endDate}<h1>'
  return flask.redirect(flask.url_for('test_api_request'))


@app.route('/test')
def test_api_request():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    # service = build("calendar", "v3", credentials=creds)
    service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)
    
    start = flask.session["date"]
    end = flask.session["endDate"]
    start = start.strftime('%Y-%m-%dT%H:%M:%S')
    end = end.strftime('%Y-%m-%dT%H:%M:%S')
    email = str(flask.session["email"])
    
    Event = {
            'summary': 'Your meeting has been set',
            'location': 'Buea, Cameroon',
            'description': 'You has been invited to the testing of the google calendar api and oauth over a web server',
            'start': {
                'dateTime': start, 
                'timeZone': 'Europe/London',
            },
            'end': {
                'dateTime': end,
                'timeZone': 'Europe/London',
            },
            'attendees': [
                {'email': email },
                {'email': "jeffyouashi@gmail.com"}
                
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                {'method': 'email', 'minutes': 4 * 60},
                {'method': 'popup', 'minutes': 30},
                ],
            },
            }

    event = service.events().insert(calendarId='primary', body=Event).execute() 
    
    # files = drive.files().list().execute()

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)
    
    context = {"link":event.get('htmlLink'),"date":start, "email":email}
    print("meeting booked sucessfully")
    revoke()
    clear_credentials()
    

    return render_template('meet.html',**context)


@app.route('/authorize')
def authorize():
  # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=['https://www.googleapis.com/auth/calendar'])

  # The URI created here must exactly match one of the authorized redirect URIs
  # for the OAuth 2.0 client, which you configured in the API Console. If this
  # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
  # error.
  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      # include_granted_scopes='true'
      
      )
  
  # Store the state so the callback can verify the auth server response.
  flask.session['state'] = state

  return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
  # Specify the state when creating the flow in the callback so that it can
  # verified in the authorization server response.
  state = flask.session['state']

  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=['https://www.googleapis.com/auth/calendar'], state=state)
  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = flask.request.url
  flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in the session.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  credentials = flow.credentials
  flask.session['credentials'] = credentials_to_dict(credentials)

  return flask.redirect(flask.url_for('test_api_request'))

@app.route('/revoke')
def revoke():
  credentials = google.oauth2.credentials.Credentials(
    **flask.session['credentials'])

  revoke = requests.post('https://oauth2.googleapis.com/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})
  if revoke:
    return "Revoked"
  
def revoke():
  credentials = google.oauth2.credentials.Credentials(
    **flask.session['credentials'])

  revoke = requests.post('https://oauth2.googleapis.com/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})
  if revoke:
    print("Credentials revoked!!")

def clear_credentials():
  if 'credentials' in flask.session:
    del flask.session['credentials']
    print("Credentials cleared!!")

@app.route('/clear')
def clear_credentials():
  # revoke()
  if 'credentials' in flask.session:
    del flask.session['credentials']
    
    
  return 'Done'


def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}


if __name__ == '__main__':
  
  # When running locally, disable OAuthlib's HTTPs verification.
  # ACTION ITEM for developers:
  #     When running in production *do not* leave this option enabled.
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

  # Specify a hostname and port that are set as a valid redirect URI
  # for your API project in the Google API Console.
  app.run('localhost', 8000, debug=True)