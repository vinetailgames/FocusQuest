# Focus Quest

Focus Quest is a desktop game that turns study sessions and small tasks into quests. Quest goals and rewards are saved between play sessions.

## Set up and run on Windows

### 1. Get Python and the game files

Install Python 3 from the [official Python for Windows downloads](https://www.python.org/downloads/windows/). If the installer offers an **Add Python to PATH** option, select it.

Download or copy the Focus Quest project to your computer. If it came as a ZIP file, extract it first. In the project folder, you should see `main.py`, `quest.py`, `timer.py`, `assets`, and `data`.

### 2. Open a command window in the project folder

1. Open **File Explorer** and open the Focus Quest folder that contains `main.py`.
2. Click the address bar at the top, type `cmd`, and press **Enter**. A Command Prompt opens in that folder.
3. Enter these commands one at a time:

   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   python -m pip install --upgrade pip
   python -m pip install pygame
   ```

The `(.venv)` text at the start of the prompt means the project's private Python environment is active. Focus Quest uses Pygame for its window, graphics, and sound. See [Pygame's installation guide](https://www.pygame.org/wiki/GettingStarted) for more details.

If Windows says `py` is not recognized, use `python` in its place for the first command. If neither command is recognized, install Python again and enable its PATH option.

### 3. Start the game

With the command window still open in the project folder and `(.venv)` active, enter:

```bat
python main.py
```

The game window will open. To play again later, open a command window in the same folder, activate the environment with `.venv\Scripts\activate`, then run `python main.py`.

## How to play

The main screen shows your coins in the upper left, the Pomodoro timer near the top, and the current quest in the upper right.

### Quests

Click the current quest button to open the quest list. Click **+ Add Quest**, enter a task name, choose a quest category, and confirm. The category stays with that quest. Focus Quest chooses its goal type and target automatically, so you do not need to choose Pomodoros or minutes yourself.

- **Main quest** — Use this for your main task. Its goal is randomly set to either 1–2 completed study sessions or 60–180 study minutes, in 5-minute increments. Completing it earns 60 coins per Pomodoro, or 2 coins per minute.
- **Side quest** — Use this for side work. Its goal is randomly set to either 1–4 completed study sessions or 30–90 study minutes, in 5-minute increments. Completing it earns 45 coins per Pomodoro, or 1.5 coins per minute, rounded up.
- **Task List** — Use this for smaller tasks. A task goal randomly selects 1–5 available task names, capped at the number of available tasks; check items off in the panel on the right. It earns 30 coins per checked task. A minutes goal lists the available tasks and completes after 15–45 study minutes, in 5-minute increments; it earns 1 coin per minute.

The timer counts a Pomodoro goal when a study session ends. For minute goals, it counts the configured study-session minutes when that session ends. Break time does not count toward quest progress. When every quest in the current round is complete, Focus Quest keeps the same tasks and categories but randomizes the goals and quest order for the next round.

In the quest list, left-click a quest to bring it to the front. Right-click a quest to edit or delete it.

### Pomodoro timer

Click the timer button to open its settings. Set the Study and Break durations in minutes, then click **Start**. The timer displays `Study: mm:ss` during study and `Break: mm:ss` during a break.

The **Pause** button pauses or resumes the timer. **Stop** resets it to the start of a Study session without playing the alarm. When a Study session finishes, the alarm sounds, music stops, and the Break countdown starts automatically. When the break ends, the display returns to the full Study duration; start the next session from the timer settings.

### Music

Click **Music** in the lower left to show the available songs. Put `.mp3`, `.ogg`, or `.wav` files in `assets/music` and restart the game for them to appear. Click a song to play it; click the same song again to stop it, or choose another song to switch tracks. Music stays stopped after a timer alarm; start it again from the music list if you want to listen.

### Coins and saved data

Coins are awarded automatically when a quest is completed and appear in the upper left. Your coins and quests are saved in `data/save.json`.

Press **Delete** to erase all quests and reset your coin balance.
