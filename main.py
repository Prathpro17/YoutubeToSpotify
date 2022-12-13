from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError

from urllib import parse
import os


DEVELOPER_KEY = None
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
SPOTIFY_KEY = None
SPOTIFY_USER_ID = None

RED = '\33[31m'
GREEN = '\33[32m'
ITALIC = '\33[3m'
RESET = '\33[m'


def get_playlist_id(playlist_url: str):
    if 'www.youtube.com' in playlist_url:
        return parse.parse_qs(parse.urlparse(playlist_url).query)['list'][0]
    else:
        return str(playlist_url.split('=').pop())

def get_youtube_data(playlist_id: str):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey = DEVELOPER_KEY)
    try:
        res = youtube.playlistItems().list(part = 'snippet', playlistId = playlist_id).execute()

        nextPageToken = res.get('nextPageToken')

        while ('nextPageToken' in res):
            nextPage = youtube.playlistItems().list(
                part = 'snippet',
                playlistId = playlist_id,
                pageToken = nextPageToken
            ).execute()
            
            res['items'] += nextPage['items']
            
            if 'nextPageToken' not in nextPage:
                res.pop('nextPageToken', None)
            else:
                nextPageToken = nextPage['nextPageToken']
        
        return res
    except HttpError:
        print('Playlist not found')
        exit()

def create_playlist(name: str, description: str = None, public: bool = False, collaborative: bool = False):
    playlist = spotify.user_playlist_create(user = spotify.me()['id'], name = name, public = public, collaborative = collaborative, description = description)
    return playlist


if __name__ == "__main__":
    
    if not os.path.exists('./tokens'):
        os.makedirs('./tokens')
    
    try:
        
        spotify = spotipy.Spotify(
            auth_manager = SpotifyOAuth(
                scope = 'playlist-modify-public playlist-modify-private user-read-email user-read-private',
                redirect_uri = 'http://localhost:8080',
                show_dialog = True,
                cache_path = './tokens/token.json'
            )
        )

        playlist_id = get_playlist_id(playlist_url = input('Enter the YouTube playlist\'s link: '))
        youtubedata = get_youtube_data(playlist_id = playlist_id)
        
        playlist = create_playlist(name = 'Autocreated Playlist')

        failed = []
        unsure = []

        for vid in youtubedata['items']:
            vid_name = vid['snippet']['title']
            print(f"YouTube video name: \"{vid_name}\"")
            spotify_name = spotify.search(q = vid_name, type = 'track')
            try:
                spotify_track_name = spotify_name['tracks']['items'][0]['name']
                print(f"Spotify track name: \"{spotify_track_name}\"")
                spotify_uri = spotify_name['tracks']['items'][0]['uri']
                if spotify_track_name in vid_name:
                    spotify.playlist_add_items(playlist_id = playlist['id'], items = [spotify_uri])
                    print(f"{GREEN}Successfully{RESET} added {spotify_track_name}!")
                else:
                    print(f"{RED}Unsure{RESET}: {ITALIC}{spotify_track_name}{RESET} not in {ITALIC}{vid_name}{RESET}")
                    unsure.append(vid_name)
            except IndexError:
                failed.append(vid_name)
                print(f"{RED}Failed to add{RESET} \"{vid_name}\"")
            print()

        if unsure:
            print()
            print(f"The program was {RED}Unsure{RESET} to add {', '.join(f'{ITALIC}{RED}{song_name}{RESET}' for song_name in unsure)} to the playlist..")

        if failed:
            print()
            print(f"{RED}Failed{RESET} to add {', '.join(f'{ITALIC}{RED}{song_name}{RESET}' for song_name in failed)} to the playlist :(")
    
    except SpotifyOauthError:
        print()
        print("Token access denied")
