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
            "daily_quest_reward_pending": False,
            "daily_quest_completion_popup_shown": False,
            "required_quests": random.randint(1, 5),
            "quests_completed_today": 0,
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
            quests_completed = max(0, int(saved_state.get(
                "quests_completed_today",
                saved_state.get("quests_completed", 0),
            )))
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
            "daily_quest_reward_pending": bool(
                saved_state.get("daily_quest_reward_pending", False)
            ),
            "daily_quest_completion_popup_shown": bool(
                saved_state.get("daily_quest_completion_popup_shown", False)
            ),
            "required_quests": required_quests,
            "quests_completed_today": quests_completed,
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
        self.state["quests_completed_today"] += 1
        reward = 0
        if (
            not self.state["daily_quest_rewarded"]
            and not self.state["daily_quest_reward_pending"]
            and self.state["quests_completed_today"] >= self.state["required_quests"]
        ):
            reward = self.state["required_quests"] * 30
            self.state["daily_quest_reward_pending"] = True

        self._save()
        return reward

    def mark_rewarded(self, date_key):
        """Mark a queued daily bonus as rewarded after its claim is confirmed."""
        if self.state["date"] == date_key:
            self.state["daily_quest_reward_pending"] = False
            self.state["daily_quest_rewarded"] = True
            self.state["daily_quest_completion_popup_shown"] = True
            self._save()

    def mark_completion_popup_shown(self, date_key):
        """Acknowledge a completion notice for a reward already paid."""
        if self.state["date"] == date_key:
            self.state["daily_quest_completion_popup_shown"] = True
            self._save()
