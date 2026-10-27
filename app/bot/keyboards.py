from vkbottle import Callback, Keyboard, KeyboardButtonColor, Text


def reply_main_menu() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("Карточки слов"), color=KeyboardButtonColor.PRIMARY)
    kb.add(Text("Мини-квиз"), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("Мой прогресс"), color=KeyboardButtonColor.SECONDARY)
    kb.add(Text("Помощь"), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()


def inline_topics() -> str:
    kb = Keyboard(one_time=False, inline=True)
    kb.add(Callback("🍔 Еда", {"cmd": "topic", "name": "Food"}))
    kb.add(Callback("✈️ Путешествия", {"cmd": "topic", "name": "Travel"}))
    kb.row()
    kb.add(Callback("💼 Бизнес", {"cmd": "topic", "name": "Business"}))
    kb.add(Callback("Меню", {"cmd": "menu"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()


def inline_flashcard(show_translation: bool = True) -> str:
    kb = Keyboard(one_time=False, inline=True)
    if show_translation:
        kb.add(Callback("👁 Показать перевод", {"cmd": "show_translation"}), color=KeyboardButtonColor.PRIMARY)
    kb.add(Callback("➡️ Следующее", {"cmd": "next_card"}), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Callback("Меню", {"cmd": "menu"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()


def inline_levels() -> str:
    kb = Keyboard(one_time=False, inline=True)
    kb.add(Callback("Легкий", {"cmd": "level", "name": "Easy"}))
    kb.add(Callback("Средний", {"cmd": "level", "name": "Medium"}))
    kb.add(Callback("Сложный", {"cmd": "level", "name": "Hard"}))
    kb.row()
    kb.add(Callback("Меню", {"cmd": "menu"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()


def inline_quiz_lengths(level: str) -> str:
    kb = Keyboard(one_time=False, inline=True)
    for n in [5, 10, 15, 20, 25]:
        kb.add(Callback(str(n), {"cmd": "quiz_length", "level": level, "n": n}))
    kb.row()
    kb.add(Callback("Меню", {"cmd": "menu"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()


def inline_quiz_options(options: list[str]) -> str:
    kb = Keyboard(one_time=False, inline=True)
    for opt in options:
        kb.add(Callback(opt, {"cmd": "quiz_answer", "text": opt}))
    kb.row()
    kb.add(Callback("Меню", {"cmd": "menu"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()