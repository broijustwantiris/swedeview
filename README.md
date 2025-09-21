# swedeview

`swedeview` is a lightweight, terminal-based YouTube client written in Python. It allows you to search for, browse, and play videos directly from your command line.

## Features

  - **TUI (Terminal User Interface):** A responsive and intuitive interface built with the `curses` library.
  - **Video Search:** Search for YouTube videos and browse results directly in the terminal.
  - **Watch History:** Keeps a log of recently watched videos for easy access.
  - **Watch Later List:** Save videos to a playlist to watch them later.
  - **Non-blocking Operations:** All network-heavy tasks (fetching video data) are run in the background using threading, ensuring the UI remains fast and responsive.
  - **Seamless Playback:** Uses `yt-dlp` to fetch video streams and `mpv` for high-quality video playback.

## Dependencies

  - **Python 3.6+**
  - **yt-dlp:** A command-line program to download videos from YouTube.
  - **mpv:** A free, open-source, and cross-platform media player.
  - **`curses`:** A Python library for creating terminal applications (usually comes with Python).

You can install the Python dependencies using pip:

```bash
pip install yt-dlp
```

You'll also need to have `mpv` installed on your system. Most package managers have it:

```bash
# On Arch Linux
sudo pacman -S mpv

# On Debian/Ubuntu
sudo apt-get install mpv

# On Fedora
sudo dnf install mpv
```

## Usage

1.  Save the script as `swedeview.py`.
2.  Make the script executable: `chmod +x swedeview.py`.
3.  Run the script from your terminal:

<!-- end list -->

```bash
./swedeview.py
```

## Configuration

`swedeview` saves your history and watch later list in a hidden directory in your home folder.

  - **History:** `~/.local/share/swedeview/history.log`
  - **Watch Later:** `~/.local/share/swedeview/watch_later.log`
