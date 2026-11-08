"""AI FAQ Chatbot

Answers customer questions from a business's own FAQ file.
It understands different wordings and small typos, and when it isn't sure,
it says so and hands the question to a human instead of guessing.

How it works:
  1. Every FAQ question (plus its alternative wordings) is turned into numbers with TF-IDF,
     using both words and 3-letter chunks, so "fees", "fee" and "feez" still match.
  2. A new question is turned into numbers the same way.
  3. Cosine similarity finds the closest FAQ question.
  4. If the best match is below a confidence threshold, the bot hands over to a human.

Usage:
    python faq_bot.py                 # chat in the terminal
    python faq_bot.py "fees kitni hai"
"""
import json
import sys
from pathlib import Path

import re

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Filler words that don't tell us what the question is about (English + Roman Urdu).
FILLER = set(ENGLISH_STOP_WORDS) | {"hai", "hy", "hain", "kya", "kia", "ka", "ki", "ke", "ko", "se", "mein", "main",
                                    "kab", "kaun", "kon", "kaise", "kitni", "kitne", "kitna", "tell", "want", "know", "please", "pls"}
KEEP = {"no", "not", "online", "where", "when", "how", "who"}   # these do change the meaning


def clean(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    kept = [w for w in words if w not in FILLER or w in KEEP]
    return " ".join(kept) if kept else text.lower()


class FAQBot:
    def __init__(self, faq_path=Path(__file__).parent / "faq.json", threshold=0.35):
        data = json.loads(Path(faq_path).read_text(encoding="utf-8"))
        self.fallback = data["fallback"]
        self.greeting = data["greeting"]
        self.threshold = threshold
        self.texts, self.answer_of, self.question_of = [], [], []
        for item in data["faqs"] + data.get("smalltalk", []):
            for text in [item["q"]] + item.get("alt", []):
                self.texts.append(clean(text))
                self.answer_of.append(item["a"])
                self.question_of.append(item["q"])
        self.words = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(self.texts)
        self.chars = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4), sublinear_tf=True).fit(self.texts)
        self.W = self.words.transform(self.texts)
        self.C = self.chars.transform(self.texts)

    def _scores(self, text):
        # average of word-level and spelling-level (3-letter chunk) similarity
        return 0.5 * cosine_similarity(self.words.transform([text]), self.W)[0] + \
               0.5 * cosine_similarity(self.chars.transform([text]), self.C)[0]

    def ask(self, question):
        """Returns (answer, matched_question, confidence 0-1)."""
        if not question.strip():
            return self.greeting, None, 1.0
        scores = self._scores(clean(question))
        best = scores.argmax()
        conf = float(scores[best])
        if conf < self.threshold:
            return self.fallback, None, conf
        return self.answer_of[best], self.question_of[best], conf


def main():
    bot = FAQBot()
    if len(sys.argv) > 1:
        answer, matched, conf = bot.ask(" ".join(sys.argv[1:]))
        print(f"{answer}\n(matched: {matched}, confidence {conf:.0%})")
        return
    print(bot.greeting, "\n(type 'quit' to exit)")
    while True:
        try:
            q = input("\nYou: ")
        except (EOFError, KeyboardInterrupt):
            break
        if q.strip().lower() in {"quit", "exit", "bye"}:
            print("Bot: Bye! Have a great day.")
            break
        answer, matched, conf = bot.ask(q)
        print(f"Bot: {answer}" + (f"   [{conf:.0%}]" if matched else ""))


if __name__ == "__main__":
    main()
