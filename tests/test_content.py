from app.domain import content


def test_flashcards_exist():
    assert len(content.FLASHCARDS) == 3
    card = content.get_random_card("Food")
    assert "word" in card
    assert "translation" in card
    assert "phonetic" in card


def test_quizzes_exist():
    assert len(content.QUIZZES) == 3
    q = content.get_random_question("Easy")
    assert "q" in q
    assert "a" in q
    assert "options" in q
    assert len(q["options"]) == 3
