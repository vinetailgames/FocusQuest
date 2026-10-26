# quest.py
import json
import math
import os
import random
from collections import Counter
from constants import DATA_FILE

class Quest:
    def __init__(self, task_name, quest_type, subtype, target_value, reward, description, completed=False, tasks=None):
        self.task_name = task_name
        self.quest_type = quest_type
        self.subtype = subtype
        self.target_value = target_value
        self.reward = reward
        self.description = description
        self.completed = completed
        self.progress = 0
        self.tasks = tasks or []

    def to_dict(self):
        return {
            "task_name": self.task_name,
            "quest_type": self.quest_type,
            "subtype": self.subtype,
            "target_value": self.target_value,
            "reward": self.reward,
            "description": self.description,
            "completed": self.completed,
            "progress": self.progress,
            "tasks": self.tasks
        }

    @staticmethod
    def from_dict(data):
        q = Quest(
            data["task_name"],
            data["quest_type"],
            data["subtype"],
            data["target_value"],
            data["reward"],
            data["description"],
            data.get("completed", False),
            data.get("tasks", [])
        )
        q.progress = data.get("progress", 0)
        return q

class QuestManager:
    def __init__(self):
        self.quests = []
        self.coin_amount = 0
        self.load()

    def _make_quest_variant(self, task_name, quest_type, available_task_names=None):
        """Create a random goal while preserving the task name and quest category."""
        if quest_type not in ("main", "side", "task_list"):
            return None

        subtype = random.choice([1, 2])
        tasks = []

        if quest_type == "main":
            if subtype == 1:
                target = random.randint(1, 2)
                reward = 2 * 30 * target
                description = f"Must complete {target} pomodoros of {task_name}"
            else:
                target = random.randrange(60, 181, 5)
                reward = 2 * target
                description = f"Must complete {target} minutes of {task_name}"
        elif quest_type == "side":
            if subtype == 1:
                target = random.randint(1, 4)
                reward = math.ceil(1.5 * 30 * target)
                description = f"Must complete {target} pomodoros of {task_name}"
            else:
                target = random.randrange(30, 91, 5)
                reward = math.ceil(1.5 * target)
                description = f"Must complete {target} minutes of {task_name}"
        else:  # task_list
            task_pool = list(available_task_names) if available_task_names is not None else [task_name]
            if subtype == 1:
                random.shuffle(task_pool)
                target = min(random.randint(1, 5), len(task_pool))
                reward = 30 * target
                description = f"Must complete {target} tasks"
                tasks = task_pool[:target]
            else:
                target = random.randrange(15, 46, 5)
                reward = target
                description = f"Must complete {target} minutes of tasks"
                tasks = task_pool

        return Quest(
            task_name=task_name,
            quest_type=quest_type,
            subtype=subtype,
            target_value=target,
            reward=reward,
            description=description,
            tasks=tasks
        )

    def add_quest(self, task_name, quest_type):
        """Add a quest with a randomly selected goal subtype and target."""
        task_name = task_name.strip()
        if not task_name:
            return None

        available_task_names = [quest.task_name for quest in self.quests]
        if quest_type == "task_list":
            available_task_names.append(task_name)
        quest = self._make_quest_variant(task_name, quest_type, available_task_names)
        if quest is None:
            return None
        self.quests.append(quest)
        self.save()
        return quest

    def _start_new_iteration(self):
        """Reroll goals and order without changing each quest's task or category."""
        previous_order = tuple(id(quest) for quest in self.quests)
        available_task_names = [quest.task_name for quest in self.quests]
        for quest in self.quests:
            new_variant = self._make_quest_variant(
                quest.task_name,
                quest.quest_type,
                available_task_names
            )
            if new_variant is None:
                continue
            while (new_variant.subtype, new_variant.target_value) == (quest.subtype, quest.target_value):
                new_variant = self._make_quest_variant(
                    quest.task_name,
                    quest.quest_type,
                    available_task_names
                )
            quest.subtype = new_variant.subtype
            quest.target_value = new_variant.target_value
            quest.reward = new_variant.reward
            quest.description = new_variant.description
            quest.completed = False
            quest.progress = 0
            quest.tasks = new_variant.tasks

        random.shuffle(self.quests)
        while len(self.quests) > 1 and tuple(id(quest) for quest in self.quests) == previous_order:
            random.shuffle(self.quests)
        self.save()

    def _complete_quest(self, quest):
        earned_reward = quest.reward
        quest.completed = True
        self.coin_amount += earned_reward
        if self.quests and all(item.completed for item in self.quests):
            self._start_new_iteration()
        else:
            self.save()
        return earned_reward

    def get_current_quest(self):
        return next((quest for quest in self.quests if not quest.completed), None)

    def set_current_quest(self, index):
        if 0 <= index < len(self.quests):
            quest = self.quests.pop(index)
            self.quests.insert(0, quest)
            self.save()

    def add_progress(self, amount):
        q = self.get_current_quest()
        if not q:
            return 0
        q.progress += amount
        if q.progress >= q.target_value:
            return self._complete_quest(q)
        self.save()
        return 0

    def complete_task(self, task_index):
        q = self.get_current_quest()
        if q and q.quest_type == "task_list" and 0 <= task_index < len(q.tasks):
            q.tasks.pop(task_index)
            if q.subtype == 1:
                q.progress += 1
                if q.progress >= q.target_value:
                    self._complete_quest(q)
                else:
                    self.save()
            else:
                # Minute goals are completed by timer progress, not by checking off tasks.
                self.save()
            return True
        return False

    def delete_quest(self, index):
        if 0 <= index < len(self.quests):
            del self.quests[index]
            self.save()

    def edit_quest(self, index, new_task_name):
        if 0 <= index < len(self.quests):
            q = self.quests[index]
            q.task_name = new_task_name
            if q.quest_type in ["main", "side"]:
                if q.subtype == 1:
                    q.description = f"Must complete {q.target_value} pomodoros of {new_task_name}"
                else:
                    q.description = f"Must complete {q.target_value} minutes of {new_task_name}"
            self.save()

    def reset_all(self):
        self.quests.clear()
        self.coin_amount = 0
        self.save()

    def _repair_saved_task_lists(self):
        """Replace legacy repeated task rows with distinct available quest tasks."""
        available_tasks = [quest.task_name for quest in self.quests]
        available_counts = Counter(available_tasks)
        changed = False

        for quest in self.quests:
            if quest.completed or quest.quest_type != "task_list" or quest.subtype != 1:
                continue

            target = min(quest.target_value, len(available_tasks))
            expected_remaining = max(0, target - quest.progress)
            current_counts = Counter(quest.tasks)
            has_unavailable_duplicates = any(
                count > available_counts[task_name]
                for task_name, count in current_counts.items()
            )
            if (
                not has_unavailable_duplicates
                and target == quest.target_value
                and len(quest.tasks) == expected_remaining
            ):
                continue

            quest.target_value = target
            quest.reward = 30 * target
            quest.description = f"Must complete {target} tasks"
            if quest.progress >= target:
                quest.completed = True
                quest.tasks = []
                self.coin_amount += quest.reward
            else:
                task_pool = available_tasks.copy()
                random.shuffle(task_pool)
                quest.tasks = task_pool[:expected_remaining]
            changed = True

        return changed

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
            repaired_task_lists = self._repair_saved_task_lists()
            if self.quests and all(q.completed for q in self.quests):
                self._start_new_iteration()
            elif repaired_task_lists:
                self.save()
        except Exception as e:
            print(f"Error loading save: {e}")
            self.quests = []
            self.coin_amount = 0
