import json
import random


class QuestionManager:
    def __init__(self, file_path="data/questions.json"):
        with open(file_path, "r", encoding="utf-8") as file:
            self.questions = json.load(file)

    def get_categories(self):
        return sorted(list(set(q["category"] for q in self.questions)))

    def get_questions(self, category, difficulty):
        filtered = [
            q for q in self.questions
            if q["category"] == category and q["difficulty"] == difficulty
        ]
        random.shuffle(filtered)
        return filtered