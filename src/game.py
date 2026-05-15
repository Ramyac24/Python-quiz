import pygame
import sys
from src.question_manager import QuestionManager
from src.ollama_client import get_hint, get_explanation, generate_question
from src.leaderboard import save_score, load_leaderboard


WIDTH, HEIGHT = 1000, 700
FPS = 60

BG = (18, 18, 28)
CARD = (34, 34, 52)
WHITE = (245, 245, 245)
YELLOW = (255, 214, 102)
GREEN = (80, 200, 120)
RED = (255, 92, 92)
BLUE = (100, 160, 255)
GRAY = (120, 120, 140)


class Button:
    def __init__(self, text, x, y, w, h, color=BLUE):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=16)
        label = font.render(self.text, True, WHITE)
        screen.blit(
            label,
            label.get_rect(center=self.rect.center)
        )

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)


class QuizGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("AI Fandom Quiz Game")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont("arial", 48, bold=True)
        self.big_font = pygame.font.SysFont("arial", 32, bold=True)
        self.font = pygame.font.SysFont("arial", 24)
        self.small_font = pygame.font.SysFont("arial", 18)

        self.qm = QuestionManager()

        self.state = "menu"
        self.category = None
        self.difficulty = None
        self.questions = []
        self.index = 0
        self.score = 0

        self.feedback = ""
        self.ai_text = ""
        self.timer_seconds = 20
        self.question_start_time = 0

    def wrap_text(self, text, font, max_width):
        words = text.split()
        lines = []
        current = ""

        for word in words:
            test = current + word + " "
            if font.size(test)[0] <= max_width:
                current = test
            else:
                lines.append(current)
                current = word + " "

        lines.append(current)
        return lines

    def draw_text_box(self, text, x, y, w, font, color=WHITE):
        lines = self.wrap_text(text, font, w)
        for i, line in enumerate(lines[:8]):
            rendered = font.render(line, True, color)
            self.screen.blit(rendered, (x, y + i * 28))

    def reset_quiz(self):
        self.questions = self.qm.get_questions(self.category, self.difficulty)
        self.index = 0
        self.score = 0
        self.feedback = ""
        self.ai_text = ""
        self.question_start_time = pygame.time.get_ticks()

        if not self.questions:
            self.questions = [{
                "category": self.category,
                "difficulty": self.difficulty,
                "question": "No questions found. Add more questions in data/questions.json.",
                "options": ["OK", "OK", "OK", "OK"],
                "answer": "OK"
            }]

    def draw_menu(self):
        self.screen.fill(BG)

        title = self.title_font.render("AI Fandom Quiz Game", True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 120)))

        subtitle = self.font.render("Pygame + Ollama powered quiz", True, WHITE)
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 180)))

        buttons = [
            Button("Start Game", 380, 260, 240, 60),
            Button("Leaderboard", 380, 340, 240, 60),
            Button("Quit", 380, 420, 240, 60, RED)
        ]

        for button in buttons:
            button.draw(self.screen, self.font)

        return buttons

    def draw_category_screen(self):
        self.screen.fill(BG)

        title = self.big_font.render("Choose Category", True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 100)))

        buttons = []
        y = 200

        for category in self.qm.get_categories():
            buttons.append(Button(category, 330, y, 340, 60))
            y += 90

        for button in buttons:
            button.draw(self.screen, self.font)

        return buttons

    def draw_difficulty_screen(self):
        self.screen.fill(BG)

        title = self.big_font.render("Choose Difficulty", True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 100)))

        buttons = [
            Button("easy", 380, 220, 240, 60, GREEN),
            Button("medium", 380, 310, 240, 60, BLUE),
            Button("hard", 380, 400, 240, 60, RED)
        ]

        for button in buttons:
            button.draw(self.screen, self.font)

        return buttons

    def draw_quiz_screen(self):
        self.screen.fill(BG)

        q = self.questions[self.index]

        elapsed = (pygame.time.get_ticks() - self.question_start_time) // 1000
        remaining = max(0, self.timer_seconds - elapsed)

        if remaining == 0:
            self.feedback = f"Time up! Correct answer: {q['answer']}"

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (40, 25))

        timer_color = RED if remaining <= 5 else YELLOW
        timer_text = self.font.render(f"Time: {remaining}s", True, timer_color)
        self.screen.blit(timer_text, (820, 25))

        progress = self.font.render(
            f"Question {self.index + 1}/{len(self.questions)}",
            True,
            GRAY
        )
        self.screen.blit(progress, (400, 25))

        pygame.draw.rect(self.screen, CARD, (60, 80, 880, 150), border_radius=20)
        self.draw_text_box(q["question"], 90, 115, 820, self.big_font, WHITE)

        buttons = []
        y = 270

        for option in q["options"]:
            buttons.append(Button(option, 160, y, 680, 55))
            y += 75

        for button in buttons:
            button.draw(self.screen, self.font)

        hint_button = Button("AI Hint", 100, 600, 160, 50, YELLOW)
        explain_button = Button("AI Explain", 300, 600, 180, 50, GREEN)
        next_button = Button("Next", 740, 600, 160, 50)

        hint_button.draw(self.screen, self.font)
        explain_button.draw(self.screen, self.font)
        next_button.draw(self.screen, self.font)

        if self.feedback:
            color = GREEN if "Correct" in self.feedback else RED
            fb = self.font.render(self.feedback, True, color)
            self.screen.blit(fb, fb.get_rect(center=(WIDTH // 2, 545)))

        if self.ai_text:
            pygame.draw.rect(self.screen, CARD, (520, 560, 420, 110), border_radius=16)
            self.draw_text_box(self.ai_text, 540, 575, 380, self.small_font, WHITE)

        return buttons, hint_button, explain_button, next_button

    def draw_end_screen(self):
        self.screen.fill(BG)

        title = self.title_font.render("Quiz Complete!", True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 150)))

        score = self.big_font.render(f"Final Score: {self.score}", True, WHITE)
        self.screen.blit(score, score.get_rect(center=(WIDTH // 2, 240)))

        buttons = [
            Button("Save Score", 380, 330, 240, 60, GREEN),
            Button("Main Menu", 380, 420, 240, 60),
            Button("Quit", 380, 510, 240, 60, RED)
        ]

        for button in buttons:
            button.draw(self.screen, self.font)

        return buttons

    def draw_leaderboard(self):
        self.screen.fill(BG)

        title = self.title_font.render("Leaderboard", True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 80)))

        leaderboard = load_leaderboard()

        y = 160
        if not leaderboard:
            text = self.font.render("No scores yet.", True, WHITE)
            self.screen.blit(text, text.get_rect(center=(WIDTH // 2, y)))
        else:
            for i, item in enumerate(leaderboard, start=1):
                row = f"{i}. {item['name']} | {item['score']} | {item['category']} | {item['difficulty']}"
                rendered = self.font.render(row, True, WHITE)
                self.screen.blit(rendered, (180, y))
                y += 45

        back_button = Button("Back", 390, 600, 220, 55)
        back_button.draw(self.screen, self.font)

        return back_button

    def handle_answer(self, selected):
        q = self.questions[self.index]

        if selected == q["answer"]:
            self.score += 4
            self.feedback = "Correct! +4"
        else:
            self.score -= 1
            self.feedback = f"Wrong! Correct answer: {q['answer']}"

    def next_question(self):
        self.feedback = ""
        self.ai_text = ""

        if self.index < len(self.questions) - 1:
            self.index += 1
            self.question_start_time = pygame.time.get_ticks()
        else:
            self.state = "end"

    def run(self):
        while True:
            self.clock.tick(FPS)

            if self.state == "menu":
                buttons = self.draw_menu()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    if buttons[0].clicked(event):
                        self.state = "category"
                    elif buttons[1].clicked(event):
                        self.state = "leaderboard"
                    elif buttons[2].clicked(event):
                        pygame.quit()
                        sys.exit()

            elif self.state == "category":
                buttons = self.draw_category_screen()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    for button in buttons:
                        if button.clicked(event):
                            self.category = button.text
                            self.state = "difficulty"

            elif self.state == "difficulty":
                buttons = self.draw_difficulty_screen()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    for button in buttons:
                        if button.clicked(event):
                            self.difficulty = button.text
                            self.reset_quiz()
                            self.state = "quiz"

            elif self.state == "quiz":
                answer_buttons, hint_button, explain_button, next_button = self.draw_quiz_screen()
                q = self.questions[self.index]

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    for button in answer_buttons:
                        if button.clicked(event) and not self.feedback:
                            self.handle_answer(button.text)

                    if hint_button.clicked(event):
                        self.ai_text = get_hint(q["question"], q["options"])

                    if explain_button.clicked(event):
                        self.ai_text = get_explanation(q["question"], q["answer"])

                    if next_button.clicked(event):
                        self.next_question()

            elif self.state == "end":
                buttons = self.draw_end_screen()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    if buttons[0].clicked(event):
                        save_score("Ramya", self.score, self.category, self.difficulty)
                        self.state = "leaderboard"

                    elif buttons[1].clicked(event):
                        self.state = "menu"

                    elif buttons[2].clicked(event):
                        pygame.quit()
                        sys.exit()

            elif self.state == "leaderboard":
                back_button = self.draw_leaderboard()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    if back_button.clicked(event):
                        self.state = "menu"

            pygame.display.flip()