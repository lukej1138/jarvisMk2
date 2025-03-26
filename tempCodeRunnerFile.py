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
        print(values['name'].lower().strip())
        print(playlist_name.lower())
        if values['name'].lower().strip() == playlist_name.lower():
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
            if query.lower() in name:
                name_to_use = name
                play_playlist(name_to_use)
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
        if similar(query, response['albums']['items'][0]['name']) >= similar(query, response['tracks']['items'][0]['name']):
            print("here")
            play_album(response['albums']['items'][0])
        else:
            play_song(response['tracks']['items'][0])
    else:
        print(response.status_code)
        print(response.text)
        return None