import os
import curses
import yt_dlp
import json
import re
import threading
import time

# --- Configuration ---
HOME_DIR = os.path.expanduser("~")
APP_DIR = os.path.join(HOME_DIR, ".local", "share", "swedeview")
HISTORY_FILE = os.path.join(APP_DIR, "history.log")
WATCH_LATER_FILE = os.path.join(APP_DIR, "watch_later.log")

# --- Global State for Background Tasks ---
background_task = {'status': 'idle', 'result': None}
background_task_lock = threading.Lock()

# --- Helper for Background Threading ---
def run_in_background(func, *args):
    """Starts a function in a new thread, updating a global status."""
    def wrapper():
        try:
            result = func(*args)
            with background_task_lock:
                background_task['result'] = result
        except Exception as e:
            with background_task_lock:
                background_task['result'] = {'error': str(e)}
        finally:
            with background_task_lock:
                background_task['status'] = 'finished'

    with background_task_lock:
        background_task['status'] = 'running'
        background_task['result'] = None

    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()

# --- Core Functions ---

def play_video(screen, video_id):
    """Plays a video and provides a post-playback menu."""
    screen.clear()
    screen.addstr(0, 0, "Fetching video info... Please wait.")
    screen.refresh()

    try:
        ydl_opts = {'quiet': True, 'dump_single_json': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            channel_name = info.get('channel')
            video_title = info.get('title')
    except Exception as e:
        screen.clear()
        screen.addstr(0, 0, f"Error: {e}")
        screen.getch()
        return

    curses.endwin()
    os.system(f"mpv 'https://www.youtube.com/watch?v={video_id}'")
    curses.doupdate()

    action_menu = [
        ("Add to Watch Later", lambda: add_to_watch_later(screen, video_id, video_title)),
        ("Go back", lambda: None),
        ("Exit", lambda: exit())
    ]

    while True:
        action_index = display_menu(screen, [(item[0],) for item in action_menu], f"Finished video by {channel_name}:")
        if action_index is not None and action_index < len(action_menu) - 1:
            action_menu[action_index][1]()
            if action_index != 0:
                break
        elif action_index is not None and action_index == len(action_menu) - 1:
            break
        elif action_index is None:
            break

def add_to_watch_later(screen, video_id, video_title):
    """Adds a video to the watch later playlist."""
    try:
        with open(WATCH_LATER_FILE, "a") as f:
            f.write(f"{video_id} {video_title}\n")
        screen.clear()
        screen.addstr(0, 0, "Added to Watch Later playlist!")
    except Exception as e:
        screen.clear()
        screen.addstr(0, 0, f"Error adding to playlist: {e}")
    screen.getch()

def browse_watch_later(screen):
    """Browses and plays videos from the watch later playlist."""
    if not os.path.exists(WATCH_LATER_FILE) or os.stat(WATCH_LATER_FILE).st_size == 0:
        screen.clear()
        screen.addstr(0, 0, "Watch Later playlist is empty.")
        screen.getch()
        return

    with open(WATCH_LATER_FILE, "r") as f:
        playlist = [(line.strip().split(" ", 1)[1], line.strip().split(" ", 1)[0]) for line in f if line.strip()]

    menu_items = playlist + [("Go back", None)]
    selected_index = display_menu(screen, menu_items, "Select a video from Watch Later:")

    if selected_index is not None and selected_index < len(playlist):
        video_id = playlist[selected_index][1]
        play_video(screen, video_id)

def search_videos(screen):
    """Performs a YouTube video search in the background."""
    screen.clear()
    screen.addstr(0, 0, "Enter video search term (press Enter to search, Esc to go back):")
    curses.echo()
    search_term = screen.getstr().decode('utf-8')
    curses.noecho()

    if not search_term:
        return

    def perform_search():
        ydl_opts = {'quiet': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{search_term}", download=False)
            return info.get('entries', [])

    run_in_background(perform_search)
    return 'video_search_pending'

def browse_history(screen):
    """Browses and plays videos from history."""
    if not os.path.exists(HISTORY_FILE) or os.stat(HISTORY_FILE).st_size == 0:
        screen.clear()
        screen.addstr(0, 0, "History is empty.")
        screen.getch()
        return

    with open(HISTORY_FILE, "r") as f:
        history = [(line.strip().split(" ", 1)[1], line.strip().split(" ", 1)[0]) for line in f if line.strip()]

    history = list(reversed(history))

    menu_items = history + [("Go back", None)]
    selected_index = display_menu(screen, menu_items)

    if selected_index is not None and selected_index < len(history):
        video_id = history[selected_index][1]
        play_video(screen, video_id)


# --- TUI Library Wrapper ---

def display_menu(screen, items, title="Select an option:"):
    """Generic menu display function for items with (label, value) pairs."""
    selected_row = 0
    max_rows = curses.LINES - 4

    while True:
        screen.clear()
        screen.addstr(0, 0, title)

        start_index = max(0, selected_row - max_rows + 1)
        end_index = min(len(items), start_index + max_rows)

        for i in range(start_index, end_index):
            label = items[i][0]
            if i == selected_row:
                screen.addstr(i - start_index + 1, 2, f"> {label}", curses.A_REVERSE)
            else:
                screen.addstr(i - start_index + 1, 2, f"  {label}")

        screen.refresh()
        key = screen.getch()

        if key == curses.KEY_UP and selected_row > 0:
            selected_row -= 1
        elif key == curses.KEY_DOWN and selected_row < len(items) - 1:
            selected_row += 1
        elif key == ord('\n'):
            return selected_row
        elif key == 27:
            return None

def main(screen):
    """Main application loop."""
    os.makedirs(APP_DIR, exist_ok=True)

    menu_items = [
        ("Search for a video", search_videos),
        ("View history", browse_history),
        ("Watch Later", browse_watch_later),
        ("Exit", lambda s: exit())
    ]

    current_state = 'main_menu'

    while True:
        if current_state == 'main_menu':
            selected_index = display_menu(screen, [(item[0],) for item in menu_items])
            if selected_index is not None:
                new_state = menu_items[selected_index][1](screen)
                if isinstance(new_state, str) and new_state.endswith('_pending'):
                    current_state = new_state

        elif current_state.endswith('_pending'):
            screen.clear()
            if current_state == 'video_search_pending':
                screen.addstr(0, 0, "Searching for videos...")
            else:
                screen.addstr(0, 0, "Loading... Please wait.")
            screen.refresh()

            with background_task_lock:
                task_status = background_task['status']
                task_result = background_task['result']

            if task_status == 'finished':
                if task_result and 'error' in task_result:
                    screen.clear()
                    screen.addstr(0, 0, f"Error: {task_result['error']}")
                    screen.getch()
                else:
                    if current_state == 'video_search_pending':
                        if not task_result:
                            screen.addstr(1, 0, "No videos found.")
                            screen.getch()
                        else:
                            # Add Go Back option to video search results
                            menu_items = [(v['title'], v['id']) for v in task_result] + [("Go back", None)]
                            selected_index = display_menu(screen, menu_items)

                            if selected_index is not None and selected_index < len(task_result):
                                video = task_result[selected_index]
                                with open(HISTORY_FILE, "a") as f:
                                    f.write(f"{video['id']} {video['title']}\n")
                                play_video(screen, video['id'])

                with background_task_lock:
                    background_task['status'] = 'idle'
                current_state = 'main_menu'

            time.sleep(0.1)

if __name__ == "__main__":
    curses.wrapper(main)
