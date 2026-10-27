import logging
import random

from vkbottle import GroupEventType
from vkbottle.bot import Bot, Message, MessageEvent

from app.bot import keyboards
from app.bot.deps import get_session
from app.bot.states import BotStates
from app.db import repository
from app.domain import content, texts

logger = logging.getLogger(__name__)

MENU_COMMANDS = [
    "/start", "start",
    "Начать", "начать",
    "Меню", "меню",
    "Назад", "назад",
]

# Состояние карточек: {"topic": str, "remaining": list, "current": dict}
user_flashcard_state: dict[int, dict] = {}

# Состояние квиза: {"level": str, "total": int, "current_idx": int, "correct": int, "wrong": int, "errors": list, "question": dict}
user_quiz_state: dict[int, dict] = {}


async def _send_menu(bot: Bot, peer_id: int, text: str) -> None:
    await bot.state_dispenser.set(peer_id, BotStates.MENU)
    await bot.api.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=0,
        keyboard=keyboards.reply_main_menu(),
    )


async def _snackbar(event: MessageEvent, text: str) -> None:
    try:
        await event.show_snackbar(text)
    except Exception as exc:
        logger.debug("snackbar failed: %s", exc)


async def _send_next_card(bot: Bot, peer_id: int, user_id: int) -> None:
    state = user_flashcard_state.get(user_id)
    if not state:
        return

    if not state["remaining"]:
        state["remaining"] = content.get_all_cards(state["topic"])
        random.shuffle(state["remaining"])
    
    card = state["remaining"].pop()
    state["current"] = card
    
    await bot.api.messages.send(
        peer_id=peer_id,
        message=texts.TXT_CARD_FRONT.format(word=card["word"], phonetic=card["phonetic"]),
        random_id=0,
        keyboard=keyboards.inline_flashcard(True),
    )


async def _send_quiz_question(bot: Bot, peer_id: int, user_id: int) -> None:
    state = user_quiz_state.get(user_id)
    if not state:
        return
    
    q = content.get_random_question(state["level"])
    state["question"] = q
    
    await bot.api.messages.send(
        peer_id=peer_id,
        message=texts.TXT_QUIZ_QUESTION.format(q=q["q"]),
        random_id=0,
        keyboard=keyboards.inline_quiz_options(q["options"]),
    )


def register_handlers(bot: Bot) -> None:

    @bot.on.message(text=MENU_COMMANDS)
    async def start_handler(message: Message) -> None:
        await _send_menu(bot, message.peer_id, texts.TXT_WELCOME)

    @bot.on.message(text=["Карточки слов", "Карточки", "/cards"])
    async def flashcards_handler(message: Message) -> None:
        await bot.state_dispenser.set(message.peer_id, BotStates.MENU)
        await message.answer(texts.TXT_CHOOSE_TOPIC, keyboard=keyboards.inline_topics())

    @bot.on.message(text=["Мини-квиз", "Квиз", "/quiz"])
    async def quiz_handler(message: Message) -> None:
        await bot.state_dispenser.set(message.peer_id, BotStates.MENU)
        await message.answer(texts.TXT_CHOOSE_LEVEL, keyboard=keyboards.inline_levels())

    @bot.on.message(text=["Мой прогресс", "Прогресс", "/progress"])
    async def progress_handler(message: Message) -> None:
        await bot.state_dispenser.set(message.peer_id, BotStates.MENU)
        async with get_session() as session:
            score = await repository.get_score(session, message.from_id)
            correct = await repository.get_correct_answers(session, message.from_id)
        
        text = texts.TXT_PROGRESS.format(score=score, correct=correct)
        await message.answer(text, keyboard=keyboards.reply_main_menu())

    @bot.on.message(text=["Помощь", "/help"])
    async def help_handler(message: Message) -> None:
        await bot.state_dispenser.set(message.peer_id, BotStates.MENU)
        await message.answer(texts.TXT_HELP, keyboard=keyboards.reply_main_menu())

    @bot.on.message()
    async def fallback_handler(message: Message) -> None:
        await bot.state_dispenser.set(message.peer_id, BotStates.MENU)
        await message.answer(texts.TXT_FALLBACK, keyboard=keyboards.reply_main_menu())

    @bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
    async def callback_handler(event: MessageEvent) -> None:
        payload = event.payload or {}
        cmd = payload.get("cmd")
        peer_id = event.peer_id
        user_id = event.user_id

        if cmd == "menu":
            await _snackbar(event, texts.TXT_MAIN_MENU)
            await _send_menu(bot, peer_id, texts.TXT_WELCOME)

        elif cmd == "topic":
            topic = payload.get("name", "Food")
            cards = content.get_all_cards(topic)
            random.shuffle(cards)
            
            user_flashcard_state[user_id] = {
                "topic": topic,
                "remaining": cards,
                "current": None,
            }
            
            await _snackbar(event, f"Тема: {topic}")
            await _send_next_card(bot, peer_id, user_id)

        elif cmd == "show_translation":
            state = user_flashcard_state.get(user_id, {})
            card = state.get("current")
            if not card:
                await _snackbar(event, "Ошибка. Начните заново.")
                return
            
            await _snackbar(event, "Перевод показан")
            
            # Пытаемся отредактировать сообщение (убрать кнопку "Показать перевод")
            try:
                await bot.api.messages.edit(
                    peer_id=peer_id,
                    conversation_message_id=event.conversation_message_id,
                    message=texts.TXT_CARD_BACK.format(
                        word=card["word"], translation=card["translation"], phonetic=card["phonetic"]
                    ),
                    keyboard=keyboards.inline_flashcard(False),
                )
            except Exception as exc:
                logger.error("edit failed: %s", exc)
                # Если редактирование не удалось, отправляем новое сообщение
                await bot.api.messages.send(
                    peer_id=peer_id,
                    message=texts.TXT_CARD_BACK.format(
                        word=card["word"], translation=card["translation"], phonetic=card["phonetic"]
                    ),
                    random_id=0,
                    keyboard=keyboards.inline_flashcard(False),
                )

        elif cmd == "next_card":
            await _snackbar(event, "Следующая карточка")
            await _send_next_card(bot, peer_id, user_id)

        elif cmd == "level":
            level = payload.get("name", "Easy")
            await _snackbar(event, f"Уровень: {level}")
            await bot.api.messages.send(
                peer_id=peer_id,
                message=f"Уровень: {level}\n\n" + texts.TXT_CHOOSE_LENGTH,
                random_id=0,
                keyboard=keyboards.inline_quiz_lengths(level),
            )

        elif cmd == "quiz_length":
            level = payload.get("level", "Easy")
            total = payload.get("n", 5)
            
            user_quiz_state[user_id] = {
                "level": level,
                "total": total,
                "current_idx": 1,
                "correct": 0,
                "wrong": 0,
                "errors": [],
                "question": None,
            }
            
            await _snackbar(event, f"Вопросов: {total}")
            await bot.api.messages.send(
                peer_id=peer_id,
                message=f"🎯 Начинаем квиз! Вопросов: {total}.",
                random_id=0,
            )
            await _send_quiz_question(bot, peer_id, user_id)

        elif cmd == "quiz_answer":
            answer = payload.get("text", "")
            state = user_quiz_state.get(user_id)
            if not state or not state.get("question"):
                await _snackbar(event, "Ошибка квиза.")
                return
            
            correct_answer = state["question"]["a"]
            
            if answer == correct_answer:
                state["correct"] += 1
                async with get_session() as session:
                    await repository.add_score(session, user_id, 10)
                    await repository.add_correct(session, user_id)
                await _snackbar(event, "✅ Верно! +10 очков")
            else:
                state["wrong"] += 1
                state["errors"].append(f"«{state['question']['q']}» → {correct_answer}")
                async with get_session() as session:
                    await repository.add_score(session, user_id, -5)
                await _snackbar(event, "❌ Неверно! -5 очков")
            
            state["current_idx"] += 1
            
            if state["current_idx"] > state["total"]:
                # Итоги
                result_text = texts.TXT_QUIZ_RESULT_HEADER.format(
                    correct=state["correct"], wrong=state["wrong"]
                )
                if state["correct"] > state["wrong"]:
                    result_text += texts.TXT_QUIZ_RESULT_GOOD
                else:
                    result_text += texts.TXT_QUIZ_RESULT_BAD
                
                if state["errors"]:
                    err_list = "\n".join(f"• {e}" for e in state["errors"])
                    result_text += texts.TXT_QUIZ_WRONG_LIST.format(words=err_list)
                
                await bot.api.messages.send(
                    peer_id=peer_id,
                    message=result_text,
                    random_id=0,
                    keyboard=keyboards.reply_main_menu(),
                )
                await bot.state_dispenser.set(peer_id, BotStates.MENU)
                user_quiz_state.pop(user_id, None)
            else:
                await bot.api.messages.send(
                    peer_id=peer_id,
                    message=f"Вопрос {state['current_idx']} из {state['total']}",
                    random_id=0,
                )
                await _send_quiz_question(bot, peer_id, user_id)