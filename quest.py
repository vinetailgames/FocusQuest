# quest.py
import json
import math
import os
import random
from constants import DATA_FILE

class Quest:
    def __init__(self, task_name, quest_type, subtype, target_value, reward, description, completed=False, tasks=None, source_tasks=None):
        self.task_name = task_name
        self.quest_type = quest_type
        self.subtype = subtype
        self.target_value = target_value
        self.reward = reward
        self.description = description
        self.completed = completed
        self.progress = 0
        self.tasks = tasks or []
        self.source_tasks = list(source_tasks if source_tasks is not None else self.tasks)

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
            "tasks": self.tasks,
            "source_tasks": self.source_tasks
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
            data.get("tasks", []),
            data.get("source_tasks")
        )
        q.progress = data.get("progress", 0)
        return q

class QuestManager:
    def __init__(self):
        self.quests = []
        self.task_catalog = []
        self.coin_amount = 0
        self.quests_paused = False
        self.load()

    def _make_quest_variant(self, task_name, quest_type):
        """Create a random main or side quest while preserving its category."""
        if quest_type not in ("main", "side"):
            return None

        subtype = random.choice([1, 2])
        if quest_type == "main":
            if subtype == 1:
                target = random.randint(1, 2)
                reward = 2 * 30 * target
                description = f"Must complete {target} pomodoros of {task_name}"
            else:
                target = random.randrange(60, 181, 5)
                reward = 2 * target
                description = f"Must complete {target} minutes of {task_name}"
        elif subtype == 1:
            target = random.randint(1, 4)
            reward = math.ceil(1.5 * 30 * target)
            description = f"Must complete {target} pomodoros of {task_name}"
        else:
            target = random.randrange(30, 91, 5)
            reward = math.ceil(1.5 * target)
            description = f"Must complete {target} minutes of {task_name}"

        return Quest(
            task_name=task_name,
            quest_type=quest_type,
            subtype=subtype,
            target_value=target,
            reward=reward,
            description=description
        )

    @staticmethod
    def _clean_task_names(task_names):
        if isinstance(task_names, str):
            task_names = task_names.splitlines()
        return [task.strip() for task in task_names if task.strip()]

    def _make_task_list_quest(self, tasks):
        task_names = list(tasks)
        subtype = random.choice([1, 2])
        if subtype == 1:
            target = len(task_names)
            reward = 30 * target
            description = f"Must complete {target} tasks"
        else:
            target = random.randrange(15, 46, 5)
            reward = target
            description = f"Must complete {target} minutes of tasks"

        return Quest(
            task_name="Task List",
            quest_type="task_list",
            subtype=subtype,
            target_value=target,
            reward=reward,
            description=description,
            tasks=task_names.copy(),
            source_tasks=task_names
        )

    def _generate_task_list_quests(self, tasks):
        """Randomly distribute each saved task into one batch of up to five."""
        task_pool = self._clean_task_names(tasks)
        random.shuffle(task_pool)
        generated = []
        while task_pool:
            task_count = min(random.randint(1, 5), len(task_pool))
            batch = task_pool[:task_count]
            del task_pool[:task_count]
            generated.append(self._make_task_list_quest(batch))
        return generated

    def add_task_list(self, tasks):
        """Save task lines and add randomized batches to the current quest round."""
        task_names = self._clean_task_names(tasks)
        if not task_names:
            return []

        self.task_catalog.extend(task_names)
        generated = self._generate_task_list_quests(task_names)
        self.quests.extend(generated)
        self.save()
        return generated

    def replace_task_catalog(self, tasks):
        """Replace the saved task list and rebuild its current-round quests."""
        self.task_catalog = self._clean_task_names(tasks)
        self.quests = [quest for quest in self.quests if quest.quest_type != "task_list"]
        generated = self._generate_task_list_quests(self.task_catalog)
        self.quests.extend(generated)
        random.shuffle(self.quests)
        self.save()

    def add_quest(self, task_name, quest_type):
        """Add a main/side quest; task lists are created with add_task_list."""
        task_name = task_name.strip()
        if not task_name:
            return None
        if quest_type == "task_list":
            generated = self.add_task_list([task_name])
            return generated[0] if generated else None

        quest = self._make_quest_variant(task_name, quest_type)
        if quest is None:
            return None
        self.quests.append(quest)
        self.save()
        return quest

    def _start_new_iteration(self):
        """Reroll main/side goals and repartition saved tasks for a new round."""
        previous_order = tuple(id(quest) for quest in self.quests)
        main_side_quests = [
            quest for quest in self.quests
            if quest.quest_type in ("main", "side")
        ]
        for quest in main_side_quests:
            new_variant = self._make_quest_variant(quest.task_name, quest.quest_type)
            while (new_variant.subtype, new_variant.target_value) == (quest.subtype, quest.target_value):
                new_variant = self._make_quest_variant(quest.task_name, quest.quest_type)
            quest.subtype = new_variant.subtype
            quest.target_value = new_variant.target_value
            quest.reward = new_variant.reward
            quest.description = new_variant.description
            quest.completed = False
            quest.progress = 0
            quest.tasks = []
            quest.source_tasks = []

        self.quests = main_side_quests + self._generate_task_list_quests(self.task_catalog)
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

    def toggle_quests_paused(self):
        self.quests_paused = not self.quests_paused
        self.save()
        return self.quests_paused

    def set_current_quest(self, index):
        if 0 <= index < len(self.quests):
            quest = self.quests.pop(index)
            self.quests.insert(0, quest)
            self.save()

    def shuffle_quests(self):
        """Randomize quest order without changing goals or quest categories."""
        if len(self.quests) < 2:
            return False

        previous_order = tuple(id(quest) for quest in self.quests)
        random.shuffle(self.quests)
        if tuple(id(quest) for quest in self.quests) == previous_order:
            self.quests[0], self.quests[1] = self.quests[1], self.quests[0]
        self.save()
        return True

    def add_progress(self, amount):
        if self.quests_paused:
            return 0
        q = self.get_current_quest()
        if not q:
            return 0
        q.progress += amount
        if q.progress >= q.target_value:
            return self._complete_quest(q)
        self.save()
        return 0

    def complete_task(self, task_index):
        if self.quests_paused:
            return False
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
                # Minute goals can finish by time or by checking off every listed task.
                if not q.tasks:
                    self._complete_quest(q)
                else:
                    self.save()
            return True
        return False

    def delete_quest(self, index):
        if 0 <= index < len(self.quests):
            quest = self.quests[index]
            if quest.quest_type == "task_list":
                for task in quest.source_tasks:
                    try:
                        self.task_catalog.remove(task)
                    except ValueError:
                        pass
            del self.quests[index]
            self.save()

    def edit_quest(self, index, new_task_name):
        if 0 <= index < len(self.quests):
            q = self.quests[index]
            if q.quest_type not in ("main", "side"):
                return
            q.task_name = new_task_name
            if q.subtype == 1:
                q.description = f"Must complete {q.target_value} pomodoros of {new_task_name}"
            else:
                q.description = f"Must complete {q.target_value} minutes of {new_task_name}"
            self.save()

    def reset_all(self):
        self.quests.clear()
        self.task_catalog.clear()
        self.coin_amount = 0
        self.quests_paused = False
        self.save()

    def save(self):
        data = {
            "coin_amount": self.coin_amount,
            "task_catalog": self.task_catalog,
            "quests_paused": self.quests_paused,
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
            self.quests_paused = bool(data.get("quests_paused", False))
            loaded_quests = [Quest.from_dict(q) for q in data.get("quests", [])]
            migrated_task_lists = "task_catalog" not in data
            loaded_iteration_complete = bool(loaded_quests) and all(q.completed for q in loaded_quests)
            if migrated_task_lists:
                self.task_catalog = [
                    quest.task_name for quest in loaded_quests
                    if quest.quest_type == "task_list"
                ]
                self.quests = [
                    quest for quest in loaded_quests
                    if quest.quest_type != "task_list"
                ]
                self.quests.extend(self._generate_task_list_quests(self.task_catalog))
            else:
                self.task_catalog = self._clean_task_names(data.get("task_catalog") or [])
                self.quests = loaded_quests

            if (self.quests and all(q.completed for q in self.quests)) or (
                migrated_task_lists and loaded_iteration_complete
            ):
                self._start_new_iteration()
            elif migrated_task_lists:
                self.save()
        except Exception as e:
            print(f"Error loading save: {e}")
            self.quests = []
            self.task_catalog = []
            self.coin_amount = 0
            self.quests_paused = False
