"""Track the current day's quest challenge and its one-time coin reward."""

import json
import os
import random
from datetime import datetime

from constants import BASE_DIR


DAILY_REWARDS_FILE = os.path.join(BASE_DIR, "data", "daily_rewards.json")
LEGACY_DEBUG_FILE = os.path.join(BASE_DIR, "debug.json")


class DailyRewards:
    def __init__(self, state_file=DAILY_REWARDS_FILE):
        self.state_file = state_file
        self.migrated_legacy_state = False
        today = self._today_key()

        saved_state = self._load()
        if saved_state and saved_state.get("date") == today:
            self.state = self._normalize_state(saved_state, today)
        else:
            self.state = self._new_day_state(today)
        self._save()
        if self.migrated_legacy_state:
            try:
                os.remove(LEGACY_DEBUG_FILE)
            except OSError:
                pass

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
        paths_to_check = [self.state_file]
        if self.state_file == DAILY_REWARDS_FILE:
            paths_to_check.append(LEGACY_DEBUG_FILE)

        for state_path in paths_to_check:
            if not os.path.exists(state_path):
                continue
            try:
                with open(state_path, "r", encoding="utf-8") as file:
                    state = json.load(file)
                if isinstance(state, dict):
                    self.migrated_legacy_state = (
                        state_path == LEGACY_DEBUG_FILE
                        and self.state_file == DAILY_REWARDS_FILE
                    )
                    return state
            except (OSError, json.JSONDecodeError):
                continue
        return None

    def _save(self):
        directory = os.path.dirname(self.state_file)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as file:
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
