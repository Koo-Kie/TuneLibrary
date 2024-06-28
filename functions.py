import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import tempfile, requests, os, pygame, io, queue, threading, sqlite3, uuid, random


client_id = "2501f685127240bbac54361f6e27cdb4"
client_secret = "f4b9e38d931b4260aefe719f79091127"

client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def search_music(search_term, limit=10, queue=None):

  results = sp.search(q=search_term, type="track", limit=limit)

  tracks = []
  for item in results["tracks"]["items"]:

    track = {
      "name": item["name"],
      "duration": f"{item['duration_ms'] // 60000:02d}:{item['duration_ms'] % 60000 // 1000:02d}",
      "artists": [artist["name"] for artist in item["artists"]],
      "album": item["album"]["name"],
      "preview_url": item["preview_url"],
      "spotify_url": item["uri"],
    }

    if item["album"]["images"]:
      track["cover_url"] = item["album"]["images"][0]["url"]
    else:
      track["cover_url"] = None

    tracks.append(track)

  if queue:
    queue.put(tracks)
    
  return tracks

def get_featured_songs():
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Get featured playlists
    playlists = sp.featured_playlists(limit=10)

    # Get random playlist
    random_playlist = random.choice(playlists['playlists']['items'])

    # Get tracks from the random playlist
    tracks = sp.playlist_tracks(random_playlist['id'], limit=4)

    featured_songs = []
    for track in tracks['items']:
        song = {}
        song['name'] = track['track']['name']
        song['artist'] = track['track']['artists'][0]['name']
        song['popularity'] = track['track']['popularity']
        song['duration'] = convert_duration(track['track']['duration_ms'])
        song['cover_url'] = track['track']['album']['images'][0]['url']  # Cover image URL
        if 'preview_url' in track['track']:
            song['preview_url'] = track['track']['preview_url']  # Preview URL if exists
        else:
            song['preview_url'] = None
        featured_songs.append(song)

    return featured_songs

def get_discover_songs():
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Search for discover playlists
    playlists = sp.search(q='discover', type='playlist', limit=4)

    # Choose a random playlist
    random_playlist = random.choice(playlists['playlists']['items'])

    # Get tracks from the random playlist
    tracks = sp.playlist_tracks(random_playlist['id'], limit=4)

    discover_songs = []
    for track in tracks['items']:
        song = {}
        song['name'] = track['track']['name']
        song['artist'] = track['track']['artists'][0]['name']
        song['popularity'] = track['track']['popularity']
        song['duration'] = convert_duration(track['track']['duration_ms'])
        song['cover_url'] = track['track']['album']['images'][0]['url']  # Cover image URL
        if 'preview_url' in track['track']:
            song['preview_url'] = track['track']['preview_url']  # Preview URL if exists
        else:
            song['preview_url'] = None
        discover_songs.append(song)

    return discover_songs


def convert_duration(duration_ms):
    seconds = duration_ms / 1000
    minutes = seconds // 60
    seconds %= 60
    return '{:02d}:{:02d}'.format(int(minutes), int(seconds))

def create_temp_image(image_data):
    if image_data is not None:
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}"
        
        cache_folder = os.path.join(os.getcwd(), 'cache')
        
        if not os.path.exists(cache_folder):
            os.makedirs(cache_folder)
        
        path = os.path.join(cache_folder, filename)
        
        with open(path, 'wb') as f:
            f.write(image_data)
        
        return path 
    else:
        return None


def download_image(url):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None 
    


class MusicPlayer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.stop_flag = False
        self._current_song = None
        self._pygame_init = False
        self.is_paused = False

    def play_song(self, song_url):
        if self._current_song: 
            self.queue.put(("stop", None))
        self.queue.put(("play", song_url))


    def set_volume(self, volume):
        self.queue.put(("volume", volume/100))

    def pause(self):
        self.queue.put(("pause", None))

    def stop(self):
        self.queue.put(("stop", None))

    def terminate(self):
        self.stop_flag = True
        self.queue.put(("stop", None))

    def run(self):
        while not self.stop_flag:
            command, arg = self.queue.get()

            if command == "play":
                self._play_song(arg)
            elif command == "volume":
                self._set_volume(arg)
            elif command == "pause":
                self._pause()
            elif command == "stop":
                self._stop()

    def _play_song(self, song_url):
        try:
            response = requests.get(song_url, stream=True)
            response.raise_for_status()

            sound_file = io.BytesIO(response.content)
            if not self._pygame_init:
                pygame.mixer.init()
                self._pygame_init = True

            if pygame.mixer.get_busy():
                pygame.mixer.stop()

            self.sound = pygame.mixer.Sound(sound_file)
            self.sound.play(fade_ms=1500)

            self._current_song = song_url

        except Exception as e:
            print(f"Error playing song: {e}")

    def _set_volume(self, volume):
        try:
            self.sound.set_volume(volume)
        except:
            pass

    def _pause(self):
        if self.is_paused:
          pygame.mixer.unpause()
          self.is_paused = False
        else:
            pygame.mixer.pause()
            self.is_paused = True

    def _stop(self):
        try:
            pygame.mixer.stop()
        except:
            pass


def create_playlist_table(playlist_name):
    conn = sqlite3.connect('playlists.db')
    c = conn.cursor()

    playlist_table_name = playlist_name.replace(" ", "_").lower()
    c.execute("CREATE TABLE IF NOT EXISTS {} (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, author TEXT, length TEXT, image BLOB, preview TEXT, rating TEXT)".format(playlist_table_name))

    conn.commit()
    conn.close()


def sanitize_string(input_string):
    # List of symbols to escape
    symbols_to_escape = ["'", '"', '`', '(', ')', '%', '_', '-', '/', '\\', '&', '|', '#', ';']

    # Escape each symbol in the input string
    for symbol in symbols_to_escape:
        input_string = input_string.replace(symbol, '')

    return input_string

def add_entry_to_playlist(playlist_name, entry):
    
    try:
        with open(entry[3], 'rb') as f:
            image_data = f.read()
        conn = sqlite3.connect('playlists.db')
        c = conn.cursor()

        playlist_table_name = playlist_name.replace(" ", "_").lower()
        c.execute("INSERT INTO {} (name, author, length, image, preview) VALUES (?, ?, ?, ?, ?)".format(playlist_table_name), (entry[0], entry[1], entry[2], sqlite3.Binary(image_data), entry[4]))

        conn.commit()
        conn.close()
    except sqlite3.OperationalError as e:
        print(e)

def get_playlists_and_songs():
    conn = sqlite3.connect('playlists.db')
    c = conn.cursor()


    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    playlist_tables = c.fetchall()

    playlists = {}

    for table in playlist_tables:
        playlist_name = table[0].replace("_", " ").title()  
        c.execute("SELECT * FROM {}".format(table[0]))
        songs = c.fetchall()
        playlists[playlist_name] = [song for song in songs]

    conn.close()

    return playlists

def clear_cache():
    try:
        # List all files in the folder
        files = os.listdir('cache')
        
        # Iterate over each file and delete it
        for file in files:
            file_path = os.path.join('cache', file)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")

        print("All files in the folder have been deleted.")
    except Exception as e:
        print("An error occurred:", str(e))
