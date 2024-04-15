import os,datetime,time
import flask
import requests
import firebase_admin
from flask_cors import CORS
from firebase_admin import credentials,db,firestore
from flask import render_template, redirect, request,session,jsonify
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
CORS(app)

cred = credentials.Certificate("cred.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
ref = db.collection('booked')

def addToDb(subject):
  try:
      ref.document(str(subject["email"])).set(subject)
      print('Data sucessfully added to the database')
      return 200
  except Exception as e:
    return 'An error occured!!'+str(e), 404
  
def InDb(subject):
    if ref.document(str(subject['email'])).get().exists():
      return True
    else:
      return False



# key. See https://flask.palletsprojects.com/quickstart/#sessions.
app.secret_key = 'moinfoubwsem32kj'


# @app.route('/')
# def index():
  
#   #db = ref.get()
#   context = {"name":"DB_Trys"}
#   return flask.render_template("index.html",**context)

# # test routes.......................
# @app.route('/t',methods=["post","get"])
# def test():
#   data = ref.order_by('email', direction=firestore.Query.ASCENDING).get()
#   dataA = []
#   for doc in data:
#             dataA.append(doc.to_dict())
#   context = {"data":dataA,"name":"Zyee's"}
#   return flask.render_template("test.html",**context)

# # test routes.......................
# @app.route('/t2',methods=["post"])
# def test2():
#   if flask.request.method == "POST":
#     data = request.form.to_dict()
#     data["status"] = False
#     #db = ref.get()
#     addToDb(data)
#     context = {"db":data,"name":db}
    
#     return flask.render_template("test2.html",**context)
  
#   return flask.redirect(flask.url_for('test'))

@app.route('/meet',methods=["POST"])
def meet():
  if flask.request.method == "POST":
    # Compute and store values in session..
    data = request.form.to_dict()
    data["status"] = False
    date = flask.request.form.get("date")
    email = flask.request.form.get("email")
    duration = td(days=0,  hours=2, minutes=0)
    date_format = '%Y-%m-%dT%H:%M'
    date_obj = dt.strptime(date, date_format)
    endDate = date_obj + duration
    flask.session["date"] = date_obj
    flask.session["endDate"] = endDate
    flask.session["email"] = email
    flask.session["data"] = data
    
  # return f'<h1>The start date: {date_obj}<br> The end date: {endDate}<h1>'
  return flask.redirect(flask.url_for('test_api_request'))


@app.route('/booked')
def test_api_request():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    # service = build("calendar", "v3", credentials=creds)
    service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)
    # Convert the necessary event values to strings...
    start = flask.session["date"]
    end = flask.session["endDate"]
    start = start.strftime('%Y-%m-%dT%H:%M:%S')
    end = end.strftime('%Y-%m-%dT%H:%M:%S')
    email = str(flask.session["email"])
    
    Event = {
            'summary': 'Meeting with Competent Property Group Ltd',
            'location': 'Buea, Cameroon',
            'description': 'You has been invited to a meeting with real estate experts of Competent Property Group Ltd.',
            'start': {
                'dateTime': start, 
                'timeZone': 'Africa/Douala',
            },
            'end': {
                'dateTime': end,
                'timeZone': 'Africa/Douala',
            },
            'organizer': [
                {'email': 'ebongloveis@gmail.com'},
            ],
            'attendees': [
                {'email':'joeltabe3@gmail.com'},
                {'email': "jeffyouashi@gmail.com"},
                {'email': email }
                
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                {'method': 'email', 'minutes': 4 * 60},
                {'method': 'popup', 'minutes': 30},
                ],
            },
            }

    try: 
      event = service.events().insert(calendarId='primary', body=Event).execute() 

      flask.session['credentials'] = credentials_to_dict(credentials)
      context = {"link":event.get('htmlLink'),"date":start, "email":email}
      eV = event.get('htmlLink')
      
      data = flask.session["data"]
      addToDb(data)
      print("meeting booked sucessfully")
      
      delayed_function(60)
      
      return jsonify(eV,start), 202
    except Exception as e:
      return 'An error occured'+str(e), 404

@app.route('/getEvents',methods=["get"])
def getE():
  data = ref.order_by('email', direction=firestore.Query.ASCENDING).get()
  dataA = []
  for doc in data:
    dataA.append(doc.to_dict())
            
  return dataA, 200

@app.route('/updateEvent/<string:id>',methods=["PATCH"])
def updateE(id):
  update = {'status':True}
  try:
      ref.document(id).update(update)

      return f'Sucessfully updated', 200
  except Exception as e:
    return f'An error occured : {e}', 500
  
@app.route('/deleteEvent/<string:id>', methods=["DELETE"])
def delete_event(id):
  try:
      # Delete the document with the provided ID
      ref.document(id).delete()
      # If the deletion is successful, return a success message with a 200 status code
      return 'Successfully deleted', 200
  except Exception as e:
      # If an error occurs during the deletion process, return an error message with a 500 status code
      return f'An error occurred: {e}', 500


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
    
def delayed_function(delay_seconds):# a function that calls another function only after a set amount of time..
    time.sleep(delay_seconds)
    clear_UserCredentials()
    
def clear_UserCredentials():
    revoke()  #revokes access to the users google calendar...
    clear_credentials()  #make it so if the user wishs to set another meeting he or she must login again..

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

  # Specify a hostname and port that are set as a valid redirect URI
  # for your API project in the Google API Console.
  app.run('localhost', 8000, debug=True)