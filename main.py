import requests
import re
import regex
import keyboard
import vlc
import tkinter as tk
import pymysql
import animdl
import time

from animdl.core.cli.helpers.searcher import search_animixplay
from animdl.core.cli.http_client import client
from animdl.core.cli.helpers import ensure_extraction
from animdl.core.codebase.providers import get_appropriate

start_episode = 0


def animixplay_search(anime_name):
    nine_anime_results = search_animixplay(session, anime_name)

    search_results = [item for item in nine_anime_results]

    search_buffer = {i['name']: i['anime_url'] for i in search_results}
    print(search_results)
    return search_results


def get_range_conditions(range_string):
    for matches in regex.finditer(r"(?:([0-9]*)[:\-.]([0-9]*)|([0-9]+))", range_string):
        start, end, singular = matches.groups()
        if start and end and int(start) > int(end):
            start, end = end, start
        yield (lambda x, s=singular: int(s) == x) if singular else (
            lambda x: True
        ) if not (start or end) else (
            lambda x, s=start: x >= int(s)
        ) if start and not end else (
            lambda x, e=end: x <= int(e)
        ) if not start and end else (
            lambda x, s=start, e=end: int(s) <= x <= int(e)
        )


def get_check(range_string):
    if not range_string:
        return lambda *args, **kwargs: True
    return lambda x: any(
        condition(x) for condition in get_range_conditions(range_string)
    )


# Keeps player paused until space is pressed again
def pause():
    media_player.pause()
    while True:
        if keyboard.is_pressed("p"):
            media_player.play()
            break


class UserPrompt:
    def __init__(self):
        # Initialization
        self.episode_start_entry = None
        self.episode_end_entry = None
        self.anime = None

        # Beginning of Tkinter Stuff
        self.prompt = tk.Tk()

        # Option Menu Creation
        choices = ['One Piece', 'Naruto']
        self.menu_choice = tk.StringVar(self.prompt)
        self.menu_choice.set('One Piece')

        self.menu = tk.OptionMenu(self.prompt, self.menu_choice, *choices)

        # Option Menu Placement
        self.menu.place(x=200, y=40)

        # Entry
        self.start_entry = tk.Entry(self.prompt, bd=8)
        self.start_entry.place(x=40, y=60)

        self.end_entry = tk.Entry(self.prompt, bd=8)
        self.end_entry.place(x=40, y=130)

        # Entry Labels
        tk.Label(self.prompt, text="Start Episode", font=("Times New Roman", 12)).place(x=40, y=35)
        tk.Label(self.prompt, text="End Episode", font=("Times New Roman", 12)).place(x=40, y=100)

        # Button
        self.button = tk.Button(self.prompt, text="Start", command=self.start_button, width=12, height=3)
        self.button.place(x=200, y=100)

        # Random
        self.prompt.title('Anime Selector')
        self.prompt.geometry("300x200")
        tk.Label(self.prompt, text="Watch Anime", font=("Times Bold", 16)).place(x=20, y=5)

        # Main Loop
        self.prompt.mainloop()

        # Return a list of this format [anime choice, episode start, episode end]

    def start_button(self):
        print("meow")
        self.episode_start_entry = self.start_entry.get()
        self.episode_end_entry = self.end_entry.get()
        self.anime = self.menu_choice.get()
        self.prompt.quit()


def create_episode_string(start, end):
    episode_list = [str(episode_number) for episode_number in range(start, end + 1, 1)]
    return " ".join(episode_list)


def get_episode_title_time(sql_cursor, ep_num):
    stmt = """SELECT TitleTime FROM `OnePiece` WHERE EpNum = %s"""
    sql_cursor.execute(stmt, str(ep_num))
    result = sql_cursor.fetchone()
    return result[0]


def minutes_seconds_to_seconds(time_str):
    m, s = time_str.split(':')
    return int(m)*60 + int(s)

def seconds_to_minutes_seconds(input_time):
    m = int(input_time) // 60
    s = int(input_time) % 60
    print("Meow")
    print(input_time)
    print(m)
    print(s)
    return str(m) + ":" + str(s)


if __name__ == '__main__':
    session = client
    print("Meow")
    connection = pymysql.connect(host='sql3.freesqldatabase.com',
                                 user='sql3506222',
                                 password='lriqksrIhM',
                                 database='sql3506222')
    cursor = connection.cursor()

    # Call class
    user = UserPrompt()

    # Define start values
    name = user.anime
    episodes = create_episode_string(int(user.episode_start_entry), int(user.episode_end_entry))
    results = animixplay_search(name)
    stream_names = {}

    for result in results:
        if result['name'] == name:
            anime_url = result['anime_url']

    print(anime_url)
    print(episodes)
    for stream_url_caller, episode in get_appropriate(session, 'https://animixplay.to/v1/one-piece',
                                                      get_check(episodes)):
        stream_url = list(ensure_extraction(session, stream_url_caller))

        all_stream_urls = requests.get(stream_url[-1]['stream_url']).text
        split_urls = all_stream_urls.splitlines()

        for i in range(0, len(split_urls), 1):
            if re.findall(r"RESOLUTION=1920x1080", split_urls[i]):
                episode_name = name + " " + str(episode) + ".m3u8"
                stream_names[episode] = episode_name
                grabbed_ep = requests.get(split_urls[i + 1])
                open(episode_name, 'wb').write(grabbed_ep.content)
                break

    for key in stream_names:
        print(key)

    for item in stream_names.items():
        print(item)

    '''
    # VLC initializtion
    media_player = vlc.MediaListPlayer()
    player = vlc.Instance()
    # media list
    media_list = player.media_list_new()
    # adding episodes to a queue
    for episode, episode_name in stream_names.items():
        media = player.media_new(episode_name)
        media_player.set_media_list(media_list)
        
    '''
    exit_video = False
    for episode, episode_name in stream_names.items():
        media_player = vlc.MediaPlayer(episode_name)
        playing = True
        play_state = True
        time_showing = False
        media_player.play()
        media_player.toggle_fullscreen()
        media_player.set_time(minutes_seconds_to_seconds(get_episode_title_time(cursor, episode))*1000)
        while playing:
            if keyboard.is_pressed("space"):
                if play_state:
                    media_player.pause()
                    play_state = False
                    time.sleep(.5)
                else:
                    media_player.play()
                    play_state = True
                    time.sleep(.5)
            if keyboard.is_pressed("esc"):
                media_player.pause()
                media_player.stop()
                playing = False
                exit_video = True
                time.sleep(.5)
                break
            if keyboard.is_pressed("n"):
                media_player.pause()
                media_player.stop()
                playing = False
                time.sleep(.5)
            if keyboard.is_pressed("t"):
                time_showing = True
                cur_time = seconds_to_minutes_seconds(media_player.get_time()/1000)
                media_player.video_set_marquee_int(vlc.VideoMarqueeOption.Enable, 1)
                media_player.video_set_marquee_int(vlc.VideoMarqueeOption.Size, 30)  # pixels
                media_player.video_set_marquee_int(vlc.VideoMarqueeOption.Position, 6)
                media_player.video_set_marquee_string(vlc.VideoMarqueeOption.Text, vlc.str_to_bytes(cur_time))
                media_player.toggle_teletext()
                time.sleep(.5)
            if keyboard.is_pressed("c"):
                media_player.video_set_marquee_string(vlc.VideoMarqueeOption.Text, vlc.str_to_bytes(None))
                media_player.toggle_teletext()
                time.sleep(.5)
            if keyboard.is_pressed("left"):
                media_player.set_time(media_player.get_time()-5000)
                time.sleep(.5)
            if keyboard.is_pressed("right"):
                media_player.set_time(media_player.get_time()+5000)
                time.sleep(.5)
            if keyboard.is_pressed("up"):
                media_player.set_time(media_player.get_time()+1)
                time.sleep(.2)
        if time_showing:
            cur_time = seconds_to_minutes_seconds(media_player.get_time() / 1000)
            media_player.video_set_marquee_string(vlc.VideoMarqueeOption.Text, vlc.str_to_bytes(cur_time))
        if exit_video:
            break

'''
python -m pip install -r requirements.txt
python main.py
'''