"""Track the current day's quest challenge and its one-time coin reward."""

import json
import os
import random
from datetime import datetime

from constants import BASE_DIR


DEBUG_FILE = os.path.join(BASE_DIR, "debug.json")


class DailyRewards:
    def __init__(self, debug_file=DEBUG_FILE):
        self.debug_file = debug_file
        today = self._today_key()

        saved_state = self._load()
        if saved_state and saved_state.get("date") == today:
            self.state = self._normalize_state(saved_state, today)
        else:
            self.state = self._new_day_state(today)
        self._save()

    @staticmethod
    def _today_key():
        """Return today's date in the computer's local time zone."""
        return datetime.now().astimezone().date().isoformat()

    @staticmethod
    def _new_day_state(date_key):
        return {
            "date": date_key,
            "daily_quest_initiated": False,
            "daily_quest_rewarded": False,
            "required_quests": random.randint(1, 5),
            "quests_completed": 0,
        }

    @staticmethod
    def _normalize_state(saved_state, date_key):
        try:
            required_quests = int(saved_state.get("required_quests", 0))
        except (TypeError, ValueError):
            required_quests = 0
        if not 1 <= required_quests <= 5:
            required_quests = random.randint(1, 5)

        try:
            quests_completed = max(0, int(saved_state.get("quests_completed", 0)))
        except (TypeError, ValueError):
            quests_completed = 0

        return {
            "date": date_key,
            "daily_quest_initiated": bool(
                saved_state.get("daily_quest_initiated", False)
            ),
            "daily_quest_rewarded": bool(
                saved_state.get("daily_quest_rewarded", False)
            ),
            "required_quests": required_quests,
            "quests_completed": quests_completed,
        }

    def _load(self):
        if not os.path.exists(self.debug_file):
            return None
        try:
            with open(self.debug_file, "r", encoding="utf-8") as file:
                state = json.load(file)
            return state if isinstance(state, dict) else None
        except (OSError, json.JSONDecodeError):
            return None

    def _save(self):
        directory = os.path.dirname(self.debug_file)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.debug_file, "w", encoding="utf-8") as file:
            json.dump(self.state, file, indent=2)

    def check_for_new_day(self):
        """Reset the challenge and daily quest count when local date changes."""
        today = self._today_key()
        if self.state["date"] == today:
            return False

        self.state = self._new_day_state(today)
        self._save()
        return True

    def show_challenge_once(self):
        """Mark today's challenge as initiated and return whether to show it."""
        if self.state["daily_quest_initiated"]:
            return False

        self.state["daily_quest_initiated"] = True
        self._save()
        return True

    def record_quest_completion(self):
        """Record a completed quest and return any newly earned daily coins."""
        self.state["quests_completed"] += 1
        reward = 0
        if (
            not self.state["daily_quest_rewarded"]
            and self.state["quests_completed"] >= self.state["required_quests"]
        ):
            reward = self.state["required_quests"] * 30
            self.state["daily_quest_rewarded"] = True

        self._save()
        return reward
