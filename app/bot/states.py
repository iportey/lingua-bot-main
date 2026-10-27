from vkbottle import BaseStateGroup


class BotStates(BaseStateGroup):
    MENU = 0
    WAITING_QUIZ = 1
    VIEWING_FLASHCARD = 2
