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

Click the current quest button to open the quest list. Click **+ Add Quest** and choose a quest category. For a Main or Side quest, enter one task name. For a Task List, enter one task on each line; press **Enter** to start the next line, then click **Confirm**. Blank lines are ignored.

In the quest window, click the gear at the bottom right to open quest options. **Pause Quests** and **Start Quests** take effect immediately. **Shuffle**, **Reset Quests**, and **Delete All** ask for confirmation. Reset Quests clears quest progress and completion while restoring checked-off tasks; Delete All removes quests and the saved task pool but keeps coins. While paused, the current quest display says **Quests paused**, completed study sessions do not add progress, and Task List checkboxes are unavailable.

- **Main quest** — Use this for your main task. Its goal is randomly set to either 1–2 completed study sessions or 60–180 study minutes, in 5-minute increments. Completing it earns 60 coins per Pomodoro, or 2 coins per minute.
- **Side quest** — Use this for side work. Its goal is randomly set to either 1–4 completed study sessions or 30–90 study minutes, in 5-minute increments. Completing it earns 45 coins per Pomodoro, or 1.5 coins per minute, rounded up.
- **Task List** — Use this for smaller tasks. The lines you enter are saved as the task pool. At the start of each quest round, Focus Quest shuffles the pool and splits it into Task List quests containing up to five tasks each. Every task entry is assigned to one quest in that round. Each batch contains the smaller of its random 1–5 task limit and the number of tasks still available. The saved pool is used again in the next round. Each generated quest randomly uses either a task goal or a 15–45 minute goal, in 5-minute increments. Check tasks off in the panel on the right; a quest completes when all its tasks are checked or its minute goal is reached. Task goals earn 30 coins per task; minute goals earn 1 coin per minute.

The timer counts a Pomodoro goal when a study session ends. For minute goals, it counts the configured study-session minutes when that session ends. Break time does not count toward quest progress. Pausing quests prevents completed study sessions from adding progress. When every quest in the current round is complete, Focus Quest keeps the same tasks and categories but randomizes the goals and quest order for the next round.

In the quest list, left-click a quest to bring it to the front. Use the mouse wheel to browse long lists. Right-click a Main or Side quest to edit or delete it. Editing a Task List opens the saved task pool; deleting one removes its assigned tasks from that pool.

### Pomodoro timer

Click the timer button to open its settings. Set the Study and Break durations in minutes, then click **Start**. The timer displays `Study: mm:ss` during study and `Break: mm:ss` during a break.

The **Pause** button pauses or resumes the timer. **Stop** resets it to the start of a Study session without playing the alarm. When a Study session finishes, the alarm sounds, music stops, and the Break countdown starts automatically. When the break ends, the display returns to the full Study duration; start the next session from the timer settings.

### Music

Click **Music** in the lower left to show the available songs. Put `.mp3`, `.ogg`, or `.wav` files in `assets/music` and restart the game for them to appear. Click a song to play it; click the same song again to stop it, or choose another song to switch tracks. Music stays stopped after a timer alarm; start it again from the music list if you want to listen.

### Coins and saved data

Coins are awarded automatically when a quest is completed and appear in the upper left. Your coins, quests, and saved task pool are stored in `data/save.json`.

To bring progress into a fresh install, copy your old `data/save.json` into the new install's `data` folder before launching the game. Updates keep the existing save in place.

Press **Delete** to erase all quests, clear the saved task pool, and reset your coin balance.

### Announcements and updates

Click the bell in the upper left to check announcements. The game checks GitHub every two minutes and announces a newer version from `version.json`. Installing asks for confirmation, closes the game, downloads the GitHub commit archive, extracts only `dist/FocusQuest`, replaces the installed bundle, and relaunches `FocusQuest.exe`. Saved data in the install folder is kept.

To prepare an update, change the `version` value in `version.json`, then run the local build script from the project folder in PowerShell:

```powershell
.\build_release.ps1
```

The script replaces `dist/FocusQuest` with `FocusQuest.exe`, `_internal`, `FocusQuestUpdater.exe`, `version.json`, and an empty default `data/save.json`. Commit and push the version and `dist/FocusQuest` together. The updater downloads that pushed commit and installs the app files beside the currently running EXE while preserving the installed `data` directory, including the user's `save.json`. Keep the EXE, `_internal`, updater, version file, and default save together when distributing the app.
