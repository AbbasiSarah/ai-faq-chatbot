"""Run with: python -m pytest"""
from faq_bot import FAQBot

bot = FAQBot()


def matched(q):
    return bot.ask(q)[1]


def test_different_wordings_find_the_same_answer():
    for q in ["How much are the fees?", "how much is the fee", "course price", "fees kitni hai"]:
        assert matched(q) == "How much are the fees?"


def test_typos_and_roman_urdu():
    assert matched("feez kitni hy") == "How much are the fees?"
    assert matched("next batch kab hai") == "When does the next batch start?"
    assert matched("certificate milega?") == "Will I get a certificate?"


def test_unrelated_questions_go_to_a_human():
    for q in ["what is the capital of France", "tell me a joke", "what is the weather today"]:
        answer, m, conf = bot.ask(q)
        assert m is None and answer == bot.fallback


def test_java_question():
    assert matched("do you teach java") == "Do you teach other languages like Java or C++?"
