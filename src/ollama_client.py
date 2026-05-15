import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"


def ask_ollama(prompt: str) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=25
        )
        response.raise_for_status()
        return response.json().get("response", "No response from Ollama.")
    except Exception:
        return "Ollama is not running. Start it with: ollama serve"


def get_hint(question: str, options: list[str]) -> str:
    prompt = f"""
Give a short subtle hint for this quiz question.
Do NOT reveal the answer.

Question: {question}
Options: {options}

Hint:
"""
    return ask_ollama(prompt).strip()


def get_explanation(question: str, correct_answer: str) -> str:
    prompt = f"""
Explain in 2-3 simple sentences why this is the correct answer.

Question: {question}
Correct answer: {correct_answer}
"""
    return ask_ollama(prompt).strip()


def generate_question(category: str, difficulty: str) -> str:
    prompt = f"""
Create one multiple-choice quiz question for category: {category}.
Difficulty: {difficulty}.

Return exactly in this format:
Question: ...
A) ...
B) ...
C) ...
D) ...
Answer: ...
"""
    return ask_ollama(prompt).strip()