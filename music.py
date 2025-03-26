import requests
import urllib.parse
from datetime import datetime
import json
from flask import Flask, redirect, request, jsonify, session
from difflib import SequenceMatcher

app = Flask(__name__)
app.secret_key = "8FD892E4FB5F326D2B5F2E2B54BCE"
username = "w6gja4j738jcfwo28lqfyf08b"

CLIENT_ID = '70d399dc6bef46f8a893252b7429c797'
CLIENT_SECRET = '5a265fa61b54499abf13623343d963b3'
REDIRECT_URI = 'http://127.0.0.1:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

TOKEN_FILEPATH = "music-tokens.json"

#Helper Functions (from ChatGPT)
def write_tokens(tokens):
    file = open(TOKEN_FILEPATH, 'w')
    json.dump(tokens, file)
    file.close()

def read_tokens():
    file = open(TOKEN_FILEPATH, 'r')
    tokens = json.load(file)
    file.close()
    return tokens

def get_valid_token():
    tokens = read_tokens()

    if tokens:
        if datetime.now().timestamp() < tokens['expires_at']:
            return tokens["access_token"]
        else:
            refresh_token()
            new_tokens = read_tokens()
            if new_tokens:
                return new_tokens["access_token"]
        
    return None


def refresh_token():
        curr_tokens = read_tokens()
        if not curr_tokens or "refresh_token" not in curr_tokens:
            print("Attempted to refresh token when no token exists, or no refresh_token available")
            return None
        
        req_body = {
            'grant_type' : 'refresh_token',
            'refresh_token' : curr_tokens['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()


        curr_tokens['access_token'] = new_token_info['access_token']
        curr_tokens['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        write_tokens(curr_tokens)

@app.route("/authorize")
def authorize():
    scope = 'playlist-read-private user-read-private user-read-email user-read-playback-state user-modify-playback-state user-read-currently-playing'
    
    params = {
        'client_id' : CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri' : REDIRECT_URI,
        'show_dialog' : True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route("/callback")
def callback():
    if 'error' in request.args:
        return jsonify({'error': request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()
        

        tokens = {
            'access_token' : token_info['access_token'],
            'refresh_token' : token_info['refresh_token'],
            'expires_at' : datetime.now().timestamp() + token_info['expires_in'],
        }
        write_tokens(tokens)

        return jsonify({"message" : "Authentication Successful, tokens saved"})
    return jsonify({"error": "Authorization code not found in request."}), 400

def get_playlists():
    token = get_valid_token()
    
    headers = {
        'Authorization': f"Bearer {token}"
    }
    
    response = requests.get(API_BASE_URL + f"users/{username}/playlists", headers=headers)
    playlists = response.json()  

    return playlists #Returns dict of playlists

def get_playlist_properties(playlist_dict, property, lower):
    names_list = []
    for values in playlist_dict["items"]:
        if(lower):
            names_list.append(values[f'{property}'].lower())
        else:
            names_list.append(values[f'{property}'])
    return names_list

#Want to be able to: search for specific playlists by name (say first command open to open playlist, then say to play song (if specified) or from the top)

#First, get names. Then, from name, check if provided name is in list (to lower first).
#If in, find context_uri based on name
#If a song name is specified, determine offset needed to start at specified song.

#Returns True on successful play, false otherwise
def play_playlist(playlist_name, song_start_name=""):
    playlists = get_playlists()
    
    context_URI =  ""
    playlist_object = None
    data = {}
    token = get_valid_token()
    headers = {
        'Authorization': f"Bearer {token}"
    }

    for values in playlists["items"]:
        if values['name'].lower().strip() == playlist_name.lower().strip():
            playlist_object = values
            context_URI = values['uri']
            break
    else:
        print("Could Not Find Playlist")
        return False
    
    if(song_start_name != ""):
        song_start_uri = ""
        tracks = requests.get(API_BASE_URL + f"playlists/{playlist_object['id']}/tracks", headers=headers).json()
        items = tracks['items']
        for item in items:
            if  song_start_name.lower() in item['track']['name'].lower():
                song_start_uri = item['track']['uri']
                break
        if(song_start_uri != ""):
            data = {
                'context_uri': context_URI,
                'offset' : {
                    'uri': song_start_uri
                }
            }
            response = requests.put(API_BASE_URL + f"me/player/play?device_id={get_device_id()}", json=data, headers=headers)
            if response.status_code == 204:
                print("Playback started successfully.")
                return True
            else:
                print(f"Failed to start playback: {response.status_code}, {response.text}")
                return False
        print("Could Not Find Track Name... Running From Start Of Playlist")

    data = {
            'context_uri': context_URI,
            'offset' : {
                    'position': 0
                }
        }
    response = requests.put(API_BASE_URL + f"me/player/play?device_id={get_device_id()}", json=data, headers=headers)

    #Courtesy of ChatGPT
    if response.status_code == 204:
        print("Playback started successfully.")
        return True
    else:
        print(f"Failed to start playback: {response.status_code}, {response.text}")
        return False

    



#Search API for specific albums and artists and songs/play them (when first command is play and 2nd command is by, then look for albums/songs. Otehrwise, if just one command check if playlist name and play it)
def search_and_play_spotify(query, artist_name=""):
    #Check if playlist
    if(artist_name == ""):
        playlist_names = get_playlist_properties(get_playlists(), 'name', lower=True)
        for name in playlist_names:
            if query.lower() in name and play_playlist(name):
                return
    #No playlist found, resort to looking through albums/artists with API
    #query needs to be song/album name
    #artist_name should be artist name
    token = get_valid_token()

    headers = {
        'Authorization' : f"Bearer {token}"
    }

    if artist_name != "":
        query += f"artist:{artist_name}"
    

    response = requests.get(API_BASE_URL + f"search?q={query}&type=album,track&limit=1", headers=headers)

    if response.status_code == 200:
        response = response.json()
        query_to_check = query.lower().strip()
        if similar(query_to_check, response['albums']['items'][0]['name'].lower().strip()) >= similar(query_to_check, response['tracks']['items'][0]['name'].lower().strip()):
            print("here")
            if not play_album(response['albums']['items'][0]):
                play_song(response['tracks']['items'][0])
        else:
            if not play_song(response['tracks']['items'][0]):
                play_album(response['albums']['items'][0])
        return True
    else:
        print(response.status_code)
        print(response.text)
        return False
    
def play_album(album):
    token = get_valid_token()

    headers = {
        'Authorization' : f"Bearer {token}"
    }
    print(album["uri"])
    data = {
        "context_uri" : album["uri"],
        "offset" : {
            "position" : 0
        }

    }
    response = requests.put(API_BASE_URL + f"me/player/play?device_id={get_device_id()}", json=data, headers=headers)
    if response.status_code == 204:
        print("Playback started successfully.")
        return True
    else:
        print(f"Failed to start playback: {response.status_code}, {response.text}")
        return False

def play_song(song):
    token = get_valid_token()

    headers = {
        'Authorization' : f"Bearer {token}"
    }
    data = {
        "uris" : [f"{song["uri"]}"]
    }
    response = requests.put(API_BASE_URL + f"me/player/play?device_id={get_device_id()}", json=data, headers=headers)
    if response.status_code == 204:
        print("Playback started successfully.")
        return True
    else:
        print(f"Failed to start playback: {response.status_code}, {response.text}")
        return False

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()  

def get_device_id():
    token = get_valid_token()
    headers = {
        'Authorization' : f"Bearer {token}"
    }
    response = requests.get(API_BASE_URL + f"me/player/devices", headers=headers)
    if response.status_code == 200:
        devices = response.json()["devices"]
        for device in devices:
            print(device['name'])
            if(device['name'] == 'iPhone'):
                return device['id']
    else:
        print(f"Error {response.status_code}, Message: {response.text}")


    
if __name__ == "__main__":
    #app.run(debug=True, port=5000)
    #play_playlist("raid the arcade v1")
    search_and_play_spotify("Hol up ")
