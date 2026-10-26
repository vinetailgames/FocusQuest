# quest.py
import json
import os
import random
from constants import DATA_FILE

class Quest:
    def __init__(self, name, quest_type, subtype, target_value, reward, completed=False, tasks=None):
        self.name = name
        self.quest_type = quest_type
        self.subtype = subtype
        self.target_value = target_value
        self.reward = reward
        self.completed = completed
        self.progress = 0
        self.tasks = tasks or []          # for task_list quests

    def to_dict(self):
        return {
            "name": self.name,
            "quest_type": self.quest_type,
            "subtype": self.subtype,
            "target_value": self.target_value,
            "reward": self.reward,
            "completed": self.completed,
            "progress": self.progress,
            "tasks": self.tasks
        }

    @staticmethod
    def from_dict(data):
        q = Quest(
            data["name"],
            data["quest_type"],
            data["subtype"],
            data["target_value"],
            data["reward"],
            data.get("completed", False),
            data.get("tasks", [])
        )
        q.progress = data.get("progress", 0)
        return q

class QuestManager:
    def __init__(self):
        self.quests = []
        self.current_quest = None
        self.coin_amount = 0
        self.load()

    def add_quest(self, name, quest_type, subtype, tasks=None):
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
                reward = int(1.5 * 30 * n + 0.5)
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

        quest = Quest(name, quest_type, subtype, target, reward, tasks=tasks or [])
        self.quests.append(quest)
        self.save()
        return quest

    def get_current_quest(self):
        for qtype in ["main", "side", "task_list"]:
            for q in self.quests:
                if q.quest_type == qtype and not q.completed:
                    self.current_quest = q
                    return q
        self.current_quest = None
        return None

    def add_progress(self, amount):
        q = self.get_current_quest()
        if not q:
            return 0
        q.progress += amount
        if q.progress >= q.target_value:
            q.completed = True
            self.coin_amount += q.reward
            self.save()
            return q.reward
        self.save()
        return 0

    def delete_quest(self, index):
        if 0 <= index < len(self.quests):
            del self.quests[index]
            self.save()

    def edit_quest(self, index, new_name):
        if 0 <= index < len(self.quests):
            self.quests[index].name = new_name
            self.save()

    def reset_all(self):
        self.quests.clear()
        self.coin_amount = 0
        self.save()

    def save(self):
        data = {
            "coin_amount": self.coin_amount,
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
            self.coin_amount = data.get("coin_amount", 0)
            self.quests = [Quest.from_dict(q) for q in data.get("quests", [])]
        except Exception as e:
            print(f"Error loading save: {e}")
            self.quests = []
            self.coin_amount = 0