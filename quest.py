# quest.py
import json
import os
import random
from constants import DATA_FILE

class Quest:
    def __init__(self, name, quest_type, subtype, target_value, reward, completed=False):
        self.name = name
        self.quest_type = quest_type      # "main", "side", "task_list"
        self.subtype = subtype          # 1 = pomodoros, 2 = minutes
        self.target_value = target_value
        self.reward = reward
        self.completed = completed
        self.progress = 0

    def to_dict(self):
        return {
            "name": self.name,
            "quest_type": self.quest_type,
            "subtype": self.subtype,
            "target_value": self.target_value,
            "reward": self.reward,
            "completed": self.completed,
            "progress": self.progress
        }

    @staticmethod
    def from_dict(data):
        q = Quest(
            data["name"],
            data["quest_type"],
            data["subtype"],
            data["target_value"],
            data["reward"],
            data.get("completed", False)
        )
        q.progress = data.get("progress", 0)
        return q

class QuestManager:
    def __init__(self):
        self.quests = []
        self.current_quest = None
        self.load()

    def add_quest(self, name, quest_type, subtype):
        """Create a new quest with random target based on type."""
        if quest_type == "main":
            if subtype == 1:
                n = random.randint(1, 2)
                reward = 2 * 30 * n
                target = n
            else:
                t = random.choice([60, 90, 120, 150, 180])
                reward = 2 * t
                target = t
        elif quest_type == "side":
            if subtype == 1:
                n = random.randint(1, 4)
                reward = int(1.5 * 30 * n + 0.5)  # round up
                target = n
            else:
                t = random.choice([30, 45, 60, 75, 90])
                reward = int(1.5 * t + 0.5)
                target = t
        else:  # task_list
            if subtype == 1:
                n = random.randint(1, 5)
                reward = 30 * n
                target = n
            else:
                t = random.choice([15, 20, 30, 40, 45])
                reward = t
                target = t

        quest = Quest(name, quest_type, subtype, target, reward)
        self.quests.append(quest)
        self.save()
        return quest

    def get_current_quest(self):
        # Priority: main > side > task_list
        for qtype in ["main", "side", "task_list"]:
            for q in self.quests:
                if q.quest_type == qtype and not q.completed:
                    self.current_quest = q
                    return q
        self.current_quest = None
        return None

    def complete_current(self):
        if self.current_quest:
            self.current_quest.completed = True
            self.save()
            return self.current_quest.reward
        return 0

    def reset_all_completed(self):
        for q in self.quests:
            q.completed = False
            q.progress = 0
        self.save()

    def save(self):
        data = {
            "quests": [q.to_dict() for q in self.quests]
        }
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            self.quests = [Quest.from_dict(q) for q in data.get("quests", [])]
        except Exception as e:
            print(f"Error loading quests: {e}")
            self.quests = []