import json
import os


LEADERBOARD_FILE = "data/leaderboard.json"


def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []

    with open(LEADERBOARD_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_score(name, score, category, difficulty):
    leaderboard = load_leaderboard()

    leaderboard.append({
        "name": name,
        "score": score,
        "category": category,
        "difficulty": difficulty
    })

    leaderboard = sorted(
        leaderboard,
        key=lambda x: x["score"],
        reverse=True
    )[:10]

    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as file:
        json.dump(leaderboard, file, indent=2)