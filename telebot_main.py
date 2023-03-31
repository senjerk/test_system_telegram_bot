from aiogram import Bot, Dispatcher, executor
from telebot_class import DATA_USERS_SET, User, CALL_BACK, States_name_text, States_text, \
    Markup, CALL_BACK_TEST, States_reminder, States_review
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncio
import aioschedule as schedule
from datetime import datetime

bot = Bot('bot_token')
db = Dispatcher(bot, storage=MemoryStorage())
DATA_USERS = DATA_USERS_SET()
MARKUP = Markup()
REMINDER_MESSAGE = "wakey wakey it's time for school"


@db.message_handler(commands=['start'])
async def start(message):
    try:
        user = User(message.from_user.id)
        if user.state is None:
            markup = Markup().get_state_markup()
            await bot.send_message(message.chat.id, text='Выберите режим пользователя:', reply_markup=markup)
        elif user.name_test is None and user.state == 'teacher':
            markup = Markup().get_short_markup_teacher()
            await bot.send_message(message.chat.id, text='Открыто базовое меню преподавателя.', reply_markup=markup)
        elif user.name_test and user.state == 'teacher':
            markup = Markup().get_full_markup_teacher()
            await bot.send_message(message.chat.id, text='Открыт редактор урока.', reply_markup=markup)
        elif user.name_test is None and user.state == 'student':
            markup = Markup().get_short_markup_student()
            await bot.send_message(message.chat.id, text='Открыто базовое меню студента.', reply_markup=markup)
        elif user.name_test and user.state == 'student':
            markup = Markup().get_full_markup_student()
            await bot.send_message(message.chat.id, text='Открыто меню урока.', reply_markup=markup)
    except Exception as err:
        print(err)


@db.callback_query_handler(CALL_BACK.filter(func=['open teacher']))
async def open_tests_teacher(call, callback_data: dict):
    if call.__class__.__name__ == 'CallbackQuery':
        chat_id = call.message.chat.id
        message_id = call.message.message_id
    else:
        chat_id = call.chat.id
        message_id = call.message_id
    index = int(callback_data['action'])
    tests = DATA_USERS.get_test_for_teacher(call.from_user.id)
    if not tests:
        await bot.send_message(chat_id, text='Вы не имеете существующих уроков.')
    else:
        if 'func' in callback_data:
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                        text='Ваши существующие уроки:',
                                        reply_markup=Markup().get_tests_markup_teacher(tests, index))
        else:
            await bot.send_message(chat_id, text='Ваши существующие уроки:',
                                   reply_markup=Markup().get_tests_markup_teacher(tests, index))


@db.callback_query_handler(CALL_BACK_TEST.filter(func=['save otv']))
async def open_tests_teacher_del(call, callback_data: dict):
    user = User(call.from_user.id)
    if not DATA_USERS.test_be(user.name_test):
        await call.message.delete()
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        call.message.from_user.id = call.from_user.id
        await start(call.message)
    elif not DATA_USERS.find_test_try(user.user_id, user.name_test):
        await call.message.delete()
        await bot.send_message(call.message.chat.id, text='Ваша попытка была удалена.')
    elif not DATA_USERS.test_is_open(user.user_id, user.name_test):
        await call.message.delete()
        await bot.send_message(call.message.chat.id, text='Ваше время закончилось')
    elif DATA_USERS.get_name_for_id_test(callback_data['name_test']) != user.name_test:
        await call.message.delete()
    else:
        index, otv = callback_data['action'].split(' ', 1)
        index = int(index)
        otv = int(otv)
        otv = call.message.reply_markup.inline_keyboard[otv][0].text
        key = DATA_USERS.save_otv(user.user_id, user.name_test, index, otv)
        if key:
            mes = await bot.send_message(call.message.chat.id, text='Ответ сохранён.')
            await mes.delete()


@db.callback_query_handler(CALL_BACK_TEST.filter(func=['open teacher_del']))
async def open_tests_teacher_del(call, callback_data: dict):
    if call.__class__.__name__ == 'CallbackQuery':
        chat_id = call.message.chat.id
        message_id = call.message.message_id
    else:
        chat_id = call.chat.id
        message_id = call.message_id
    user = User(call.from_user.id)
    if not DATA_USERS.test_be(user.name_test):
        await call.message.delete()
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        call.message.from_user.id = call.from_user.id
        await start(call.message)
    else:
        index = int(callback_data['action'])
        tests = DATA_USERS.get_test_for_name(call.from_user.id)
        if not tests:
            await bot.send_message(chat_id, text='Вопросы для теста не были заданы.')
        else:
            if 'func' in callback_data:
                if DATA_USERS.get_name_for_id_test(callback_data['name_test']) == user.name_test:
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                                text='Выберите тестовый вопрос, который хотите удалить:',
                                                reply_markup=Markup().get_tests_markup_teacher_del(tests, index,
                                                                                                   user.name_test))
                else:
                    await bot.delete_message(chat_id, message_id)
            else:
                await bot.send_message(chat_id, text='Выберите тестовый вопрос, который хотите удалить:',
                                       reply_markup=Markup().get_tests_markup_teacher_del(tests, index, user.name_test))


@db.callback_query_handler(CALL_BACK_TEST.filter(func=['open teacher_result']))
async def open_tests_teacher_result(call, callback_data: dict):
    if call.__class__.__name__ == 'CallbackQuery':
        chat_id = call.message.chat.id
        message_id = call.message.message_id
    else:
        chat_id = call.chat.id
        message_id = call.message_id
    user = User(call.from_user.id)
    if not DATA_USERS.test_be(user.name_test):
        await call.message.delete()
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        call.message.from_user.id = call.from_user.id
        await start(call.message)
    else:
        index = int(callback_data['action'])
        tests = DATA_USERS.get_test_for_name(call.from_user.id)
        if not tests:
            await bot.send_message(chat_id, text='Вопросы для теста не были заданы.')
        else:
            if 'func' in callback_data:
                if DATA_USERS.get_name_for_id_test(callback_data['name_test']) == user.name_test:
                    markup, qe = Markup().get_test_markup_qe_teacher_result(tests, index, user.name_test)
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                                text=qe, reply_markup=markup)
                else:
                    await bot.delete_message(chat_id, message_id)
            else:
                markup, qe = Markup().get_test_markup_qe_teacher_result(tests, index, user.name_test)
                await bot.send_message(chat_id, text=qe, reply_markup=markup)


@db.callback_query_handler(CALL_BACK_TEST.filter(func=['open test_try']))
async def open_tests_try(call, callback_data: dict):
    if call.__class__.__name__ == 'CallbackQuery':
        chat_id = call.message.chat.id
        message_id = call.message.message_id
    else:
        chat_id = call.chat.id
        message_id = call.message_id
    user = User(call.from_user.id)
    if not DATA_USERS.test_be(user.name_test):
        await call.message.delete()
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        call.message.from_user.id = call.from_user.id
        await start(call.message)
    else:
        index = int(callback_data['action'])
        tests_try = DATA_USERS.get_test_try_for_teacher(call.from_user.id, user.name_test)
        if not tests_try:
            await bot.send_message(chat_id, text='Данное тестирование ещё никто не проходил.')
        else:
            if 'func' in callback_data:
                if DATA_USERS.get_name_for_id_test(callback_data['name_test']) == user.name_test:
                    markup = Markup().get_test_try_for_teacher_markup(tests_try, index, user.name_test)
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                                text='Результаты:', reply_markup=markup)
                else:
                    await bot.delete_message(chat_id, message_id)
            else:
                markup = Markup().get_test_try_for_teacher_markup(tests_try, index, user.name_test)
                await bot.send_message(chat_id, text='Результаты:', reply_markup=markup)


@db.callback_query_handler(CALL_BACK_TEST.filter(func=['open test_try student', 'open test_try student user_id']))
async def get_test_try_student(call, callback_data: dict):
    user = User(call.from_user.id)
    if call.__class__.__name__ == 'CallbackQuery':
        chat_id = call.message.chat.id
        message_id = call.message.message_id
    else:
        chat_id = call.chat.id
        message_id = call.message_id
    if not DATA_USERS.test_be(user.name_test):
        await call.message.delete()
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        call.message.from_user.id = call.from_user.id
        await start(call.message)
    else:
        user_id, index = callback_data['action'].split(' ', 1)
        user_id = int(user_id)
        index = int(index)
        tests = DATA_USERS.get_test_for_name(user.user_id)
        tests_try = DATA_USERS.get_test_try(user_id, user.name_test)
        if not tests:
            await bot.send_message(chat_id, text='Вопросы для теста не были заданы.')
        else:
            if 'func' in callback_data:
                if DATA_USERS.get_name_for_id_test(callback_data['name_test']) == user.name_test:
                    markup, qe = Markup().get_test_markup_student_for_teacher(tests, tests_try, index, user.name_test,
                                                                              user_id)
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                                text=qe, reply_markup=markup)
                else:
                    await bot.delete_message(chat_id, message_id)
            else:
                markup, qe = Markup().get_test_markup_student_for_teacher(tests, tests_try, index, user.name_test,
                                                                          user_id)
                await bot.send_message(chat_id, text=qe, reply_markup=markup)


@db.callback_query_handler(CALL_BACK_TEST.filter(func=['del test_try student']))
async def tests_try_del(call, callback_data: dict):
    user = User(call.from_user.id)
    if not DATA_USERS.test_be(user.name_test):
        await call.message.delete()
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        call.message.from_user.id = call.from_user.id
        await start(call.message)
    if DATA_USERS.get_name_for_id_test(callback_data['name_test']) != user.name_test:
        await call.message.delete()
    else:
        user_id, name_test = callback_data['action'].split(' ', 1)
        name_test = DATA_USERS.get_name_for_id_test(int(name_test))
        DATA_USERS.del_test_try(int(user_id), name_test)
        await call.message.delete()
        await bot.send_message(call.message.chat.id, text='Попытка прохождения студента была <b>успешно удалена</b>.',
                               parse_mode='html')


@db.callback_query_handler(CALL_BACK_TEST.filter(func=['open test_try_del']))
async def open_tests_try_del(call, callback_data: dict):
    if call.__class__.__name__ == 'CallbackQuery':
        chat_id = call.message.chat.id
        message_id = call.message.message_id
    else:
        chat_id = call.chat.id
        message_id = call.message_id
    user = User(call.from_user.id)
    if not DATA_USERS.test_be(user.name_test):
        await call.message.delete()
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        call.message.from_user.id = call.from_user.id
        await start(call.message)
    else:
        index = int(callback_data['action'])
        tests_try = DATA_USERS.get_test_try_for_teacher(call.from_user.id, user.name_test)
        if not tests_try:
            await bot.send_message(chat_id, text='Нету студентов, которые прошли тестирование.')
        else:
            if 'func' in callback_data:
                if DATA_USERS.get_name_for_id_test(callback_data['name_test']) == user.name_test:
                    markup = Markup().get_test_try_for_teacher_markup_del(tests_try, index, user.name_test)
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                                text='Результат:', reply_markup=markup)
                else:
                    await bot.delete_message(chat_id, message_id)
            else:
                markup = Markup().get_test_try_for_teacher_markup_del(tests_try, index, user.name_test)
                await bot.send_message(chat_id, text='Результат:', reply_markup=markup)


@db.callback_query_handler(CALL_BACK_TEST.filter(func=['del test']))
async def set_state(call, callback_data: dict):
    index = int(callback_data["action"])
    user = User(call.from_user.id)
    if not DATA_USERS.test_be(user.name_test):
        await call.message.delete()
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        call.message.from_user.id = call.from_user.id
        await start(call.message)
    elif DATA_USERS.get_name_for_id_test(callback_data['name_test']) != user.name_test:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        key = DATA_USERS.del_test_for_teacher(user.user_id, user.name_test, index)
        if key:
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, text='Вопрос успешно удалён.')
        else:
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id,
                                   text=f'<b>Ошибка</b>: вы не являетесь автором или тест не установлен.',
                                   parse_mode='html')


@db.callback_query_handler(CALL_BACK.filter(func=['set_state']))
async def set_state(call, callback_data: dict):
    state = callback_data["action"]
    DATA_USERS.set_or_update_state(call.from_user.id, state)
    if state == "student":
        state_text = "студента"
    else:
        state_text = "преподавателя"
    await bot.send_message(call.message.chat.id, text=f'Профиль изменён на {state_text}.')
    call.message.from_user.id = call.from_user.id
    await start(call.message)


@db.callback_query_handler(CALL_BACK.filter(func=['set name_test']))
async def set_name_test(call, callback_data: dict):
    if 'func' in callback_data:
        name_test = DATA_USERS.get_name_for_id_test(callback_data["action"])
    else:
        name_test = callback_data["action"]
    key = DATA_USERS.set_name_test(call.from_user.id, name_test)
    if key:
        await bot.send_message(call.message.chat.id, text=f'Урок "<b>{name_test}</b>" был успешно открыт.',
                               parse_mode='html')
        call.message.from_user.id = call.from_user.id
        await start(call.message)
    else:
        await bot.send_message(call.message.chat.id, text=f'<b>Ошибка</b>: у вас не установлен профиль.',
                               parse_mode='html')
        call.message.from_user.id = call.from_user.id
        await start(call.message)


@db.callback_query_handler(CALL_BACK_TEST.filter(func=['open lesson']))
async def open_lesson(call, callback_data: dict):
    if call.__class__.__name__ == 'CallbackQuery':
        chat_id = call.message.chat.id
        message_id = call.message.message_id
    else:
        chat_id = call.chat.id
        message_id = call.message_id
    user = User(call.from_user.id)
    if not DATA_USERS.test_be(user.name_test):
        await call.message.delete()
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        call.message.from_user.id = call.from_user.id
        await start(call.message)
    else:
        index = int(callback_data['action'])
        lesson = DATA_USERS.get_lesson(call.from_user.id)
        if not lesson:
            await bot.send_message(chat_id, text='Текст для урока не был написан.')
        else:
            if 'func' in callback_data:
                if DATA_USERS.get_name_for_id_test(callback_data['name_test']) != user.name_test:
                    await bot.delete_message(chat_id, message_id)
                else:
                    markup, text = MARKUP.get_lesson_markup(lesson, index, user.name_test)
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                                text=text, reply_markup=markup)
            else:
                markup, text = MARKUP.get_lesson_markup(lesson, index, user.name_test)
                await bot.send_message(chat_id, text=text, reply_markup=markup)


@db.callback_query_handler(CALL_BACK_TEST.filter(func=['open test_list']))
async def open_test_list(call, callback_data: dict):
    if call.__class__.__name__ == 'CallbackQuery':
        chat_id = call.message.chat.id
        message_id = call.message.message_id
    else:
        chat_id = call.chat.id
        message_id = call.message_id
    index = int(callback_data['action'])
    tests = DATA_USERS.get_list_test(call.from_user.id)
    if not tests:
        await bot.send_message(chat_id, text='Нету подключённых уроков.')
    else:
        if 'func' in callback_data:
            markup = MARKUP.get_markup_list_test(tests, index)
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                        text='Список подключенных уроков:', reply_markup=markup)
        else:
            markup = MARKUP.get_markup_list_test(tests, index)
            await bot.send_message(chat_id, text='Список подключенных уроков:', reply_markup=markup)


@db.callback_query_handler(CALL_BACK_TEST.filter(func=['end test']))
async def end_test(call, callback_data: dict):
    user = User(call.from_user.id)
    if not DATA_USERS.test_be(user.name_test):
        await call.message.delete()
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        call.message.from_user.id = call.from_user.id
        await start(call.message)
    elif DATA_USERS.get_name_for_id_test(callback_data['name_test']) != user.name_test:
        await call.message.delete()
    else:
        if user.name_test is None:
            await bot.send_message(call.message.chat.id, text='Тест не установлен.')
        else:
            DATA_USERS.close_test(user.user_id, user.name_test)
            await call.message.delete()


@db.callback_query_handler(CALL_BACK_TEST.filter(func=['open test student']))
async def open_test_student(call, callback_data: dict):
    user = User(call.from_user.id)
    if call.__class__.__name__ == 'CallbackQuery':
        chat_id = call.message.chat.id
        message_id = call.message.message_id
    else:
        chat_id = call.chat.id
        message_id = call.message_id

    if not DATA_USERS.test_be(user.name_test):
        await call.message.delete()
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        call.message.from_user.id = call.from_user.id
        await start(call.message)
    elif not DATA_USERS.find_test_try(user.user_id, user.name_test):
        await call.message.delete()
        await bot.send_message(call.message.chat.id, text='Ваша попытка была удалена.')  
    else:
        index = int(callback_data['action'])
        tests = DATA_USERS.get_test_for_name(user.user_id)
        tests_try = DATA_USERS.get_test_try(user.user_id, user.name_test)
        # print(tests)
        # print(tests_try)
        if not tests:
            await bot.send_message(chat_id, text='Нету тестовых вопросов для этого урока.')
        else:
            if 'func' in callback_data:
                if DATA_USERS.get_name_for_id_test(callback_data['name_test']) == user.name_test:
                    markup, qe = Markup().get_test_markup_student(tests, tests_try, index, user.name_test)
                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                                text=qe, reply_markup=markup)
                else:
                    await bot.delete_message(chat_id, message_id)
            else:
                markup, qe = Markup().get_test_markup_student(tests, tests_try, index, user.name_test)
                await bot.send_message(chat_id, text=qe, reply_markup=markup)


@db.message_handler(lambda message: message.text in [
    'Добавить вопрос', 'Удалить вопрос', 'Посмотреть тест урока',
    'Изменить текст урока', 'Посмотреть урок', 'Изменить время',
    'Посмотреть результаты', 'Удалить попытку', 'Удалить урок', 'Редактировать', 'Вернуться в меню'])
async def call_reply_mark_teacher_full(message):
    user = User(message.from_user.id)
    if user.state != 'teacher' or user.name_test is None:
        await message.reply(text='Урок несуществует или вы находитесь в профиле студента.')
        await start(message)
    elif not DATA_USERS.test_be(user.name_test):
        await message.reply(text='Урок был удалён.')
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        await start(message)
    elif message.text == 'Добавить вопрос':
        await message.reply(
            text=f'<b>Напишите тестовый вопрос в формате</b>:\nВопрос<b>;</b> правильный ответ<b>;</b> неправильный '
                 f'ответ<b>,</b> неправильный ответ... \n(<i>максимальное кол-во неправильных ответов: <u>4</u></i>).',
            parse_mode='html')
        await States_text.add_test.set()
    elif message.text == 'Удалить вопрос':
        await open_tests_teacher_del(message, {'action': '0'})
    elif message.text == 'Посмотреть тест урока':
        await open_tests_teacher_result(message, {'action': '0'})
    elif message.text == 'Изменить текст урока':
        await message.reply(text='Введите текст для урока (пробелы и переносы строк учитываются):')
        await States_text.update_lesson.set()
    elif message.text == 'Посмотреть урок':
        await open_lesson(message, {'action': '0'})
    elif message.text == 'Изменить время':
        await message.reply(text='Введите кол-во минут для прохождения тестирования (0 - время неограничено):')
        await States_text.set_time.set()
    elif message.text == 'Посмотреть результаты':
        await open_tests_try(message, {'action': '0'})
    elif message.text == 'Удалить попытку':
        await open_tests_try_del(message, {'action': '0'})
    elif message.text == 'Удалить урок':
        key = DATA_USERS.del_tests(user.user_id, user.name_test)
        if key:
            await message.reply(text=f'Урок "<b>{user.name_test}</b>" был успешно удалён.', parse_mode='html')
            await start(message)
        else:
            await message.reply(text=f'<b>Ошибка</b>: вы не являетесь автором или тест не установлен.',
                                parse_mode='html')
    elif message.text == 'Редактировать':
        await bot.send_message(message.chat.id, text='Открыт редактор теста',
                               reply_markup=MARKUP.get_full_markup_teacher_edit())

    elif message.text == 'Вернуться в меню':
        await bot.send_message(message.chat.id, text='Открыто меню теста',
                               reply_markup=MARKUP.get_full_markup_teacher())


@db.message_handler(lambda message: message.text in [
    'Присоединиться к тесту', 'Открыть урок', 'Пройти тестирование', 'Результат тестирования', 'Изменить имя',
    'Список тестов'])
async def call_reply_mark_student_base(message):
    user = User(message.from_user.id)
    if user.state != 'student':
        await message.reply(text='Нет такого теста или вы находитесь в профиле учителя')
        await start(message)
    elif message.text == 'Присоединиться к тесту':
        await message.reply(text='Введите имя теста')
        await States_text.set_name_test.set()
    elif message.text == 'Список тестов':
        await open_test_list(message, {'action': 0})
    elif user.name_test is None:
        await message.reply(text='Тест не был установлен.')
        await start(message)
    elif not DATA_USERS.test_be(user.name_test):
        await message.reply(text='Тестирование было удалено.')
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        await start(message)
    elif message.text == 'Открыть урок':
        await open_lesson(message, {'action': '0'})
    elif message.text == 'Пройти тестирование':
        ind = DATA_USERS.be_user_name_for_test(user.user_id, user.name_test)
        if ind:
            key = DATA_USERS.start_test(user.user_id, user.name_test)
            if key:
                await open_test_student(message, {'action': '0'})
            else:
                await message.reply(text='Тестирование закончилось.')
        else:
            await message.reply(text='Напишите уникальное имя пользователя для прохождения тестирования по теме урока:')
            await States_text.set_username.set()
    elif message.text == 'Результат тестирования':
        count = DATA_USERS.count_true_test(user.user_id, user.name_test)
        if not count:
            await message.reply(text='Вы ещё не проходили тестирование.')
        else:
            await message.reply(text=f'Результат: <b>{count}</b>.', parse_mode='html')
    elif message.text == 'Изменить имя':
        await message.reply(text='Напишите уникальное имя пользователя для прохождения тестирования по теме урока:')
        await States_text.update_username.set()


@db.message_handler(lambda message: message.text in ['Вернуться назад'])
async def call_exit_test(message):
    user = User(message.from_user.id)
    if user.state is None:
        await message.reply(text='Ваш профиль не установлен.')
        await start(message)
    elif message.text == 'Вернуться назад':
        DATA_USERS.del_name_test_in_user(user.user_id)
        await start(message)


@db.message_handler(lambda message: message.text in ["Изменить профиль", "Создать тест", "Мои тесты"])
async def call_reply_mark_teacher_base(message):
    user = User(message.from_user.id)
    if message.text == "Изменить профиль":
        markup = Markup().get_state_markup()
        await bot.send_message(message.chat.id, text='Выберите режим пользователя:', reply_markup=markup)
    elif user.state != 'teacher' or user.state is None:
        await message.reply(text=f'<b>Ошибка</b>: вы находитесь в профиле студента или у вас не установлен профиль.',
                            parse_mode='html')
        await start(message)
    elif message.text == "Создать тест":
        await message.reply(
            "Введите название для урока:",
            parse_mode='html')
        await States_name_text.name_text.set()
    elif message.text == "Мои тесты":
        await open_tests_teacher(message, {'action': '0'})


async def handle_feedback_speech(message, key):
    if key:
        await message.reply("Спасибо за отзыв! Желаю успехов и хорошего дня. 🥰")
    else:
        await message.reply("Ваш отзыв был успешно изменен. Спасибо! 🥰")


@db.message_handler(state=States_review.Q1)
async def write_reviews(message, state: FSMContext):
    key = DATA_USERS.write_reviews(message.text, message.from_user.id)
    await state.finish()
    await handle_feedback_speech(message, key)


@db.message_handler(lambda message: message.text == "Оставить отзыв✍️")
async def feedback(message):
    await message.reply(
        "Оставьте, пожалуйста отзыв!\nВ дальнейшем мы учтем ваши пожелания при улучшении версии бота",
        parse_mode='html')
    await States_review.Q1.set()


async def handle_reminder_speech(message, key):
    reminder = DATA_USERS.get_user_reminder(message.from_user.id)
    if key:
        await message.reply(f"Напоминание успешно установлено на {reminder}.", parse_mode='html')
    else:
        await message.reply(f"Напоминание успешно изменено на {reminder}.", parse_mode='html')


@db.message_handler(state=States_reminder.Q2)
async def create_reminder(message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%H:%M")
        flag = True
    except ValueError:
        await message.answer(
            "Неправильно указано время. Пожалуйста, напишите время в 24-х часовом формате (пример: 14:30).")
        flag = False
    if flag:
        key = DATA_USERS.create_reminder(message.text, message.from_user.id)
        await handle_reminder_speech(message, key)
    await state.finish()


# @db.message_handler(lambda message: message.text == "Напоминалка⏰")
# async def feedback(message):
#     await message.reply(
#         "Открыто меню напоминалки.",
#         parse_mode='html', reply_markup=MARKUP.get_reminder_markup())


@db.message_handler(lambda message: message.text in ['Установить напоминалку', 'Удалить напоминалку',
                                                     'Вернуться нaзад'])
async def handler_reminder(message):
    if message.text == "Установить напоминалку":
        await message.reply("Укажите время, в которое будет <b>ежедневно</b> срабатывать напоминание (пример: 12:10 "
                            "или 7:11).", parse_mode='html')
        await States_reminder.Q2.set()
    elif message.text == "Удалить напоминалку":
        DATA_USERS.delete_reminder(message.from_user.id)
        await bot.send_message(message.chat.id, 'Напоминалка была <b>успешно удалена</b>.', parse_mode="html")
    elif message.text == "Вернуться нaзад":
        await start(message)


@db.message_handler(state=States_text.add_test)
async def add_test(message, state: FSMContext):
    await state.finish()
    user = User(message.from_user.id)
    if not DATA_USERS.test_be(user.name_test):
        await message.reply(text='Урок удалён.')
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        await start(message)
    else:
        try:
            qe, otv, err = message.text.split(';')
            qe = qe.strip()
            otv = otv.strip()
            err = [i.strip() for i in err.split(',')]
            DATA_USERS.add_test_for_teacher(user.user_id, user.name_test, {"qe": qe, "otv": otv, "err": err})
            await message.reply(text='Вопрос был успешно добавлен.')
        except Exception as err:
            print(err)
            await message.reply(
                text='Вопрос не соответствует формату (вопрос;правильный ответ;неправильный ответ,н.о. ...)')


@db.message_handler(state=States_text.set_name_test)
async def add_test(message, state: FSMContext):
    await state.finish()
    key = DATA_USERS.set_name_test(message.from_user.id, message.text)
    if key:
        await bot.send_message(message.chat.id, text=f'Вы успешно записались на урок "{message.text}".')
        await start(message)
    else:
        await bot.send_message(message.chat.id, text='Этого урока не существует или вы имеете профиль студента.')


@db.message_handler(state=States_name_text.name_text)
async def create_test(message, state: FSMContext):
    key = DATA_USERS.create_test(message.from_user.id, message.text)
    await state.finish()
    if key:
        await message.reply("Урок был успешно создан.", reply_markup=Markup().get_full_markup_teacher())
        DATA_USERS.set_name_test(message.from_user.id, message.text)
    else:
        await message.reply(f'<b>Ошибка</b>: вы в профиле студента или тест с данным именем уже существует.',
                            parse_mode='html')


@db.message_handler(state=States_text.set_username)
async def create_test(message, state: FSMContext):
    await state.finish()
    user = User(message.from_user.id)
    if not DATA_USERS.test_be(user.name_test):
        await message.reply(text='Урок удалён.')
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        await start(message)
    else:
        key = DATA_USERS.set_username(user.user_id, user.name_test, message.text)
        if key:
            await message.reply(text='Имя пользователя успешно задано.')
            key = DATA_USERS.start_test(user.user_id, user.name_test)
            if key:
                await open_test_student(message, {'action': '0'})
            else:
                await message.reply(text='Тестирование уже закончилось или было пройдено.')
        else:
            await message.reply(text='Данное название урока уже занято.')


@db.message_handler(state=States_text.update_username)
async def update_username(message, state: FSMContext):
    await state.finish()
    user = User(message.from_user.id)
    if not DATA_USERS.test_be(user.name_test):
        await message.reply(text='Урок удалён.')
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        await start(message)
    else:
        key = DATA_USERS.set_username(user.user_id, user.name_test, message.text)
        if key:
            await message.reply(text='Имя успешно изменено.')
        else:
            await message.reply(text='Данное имя уже занято.')


@db.message_handler(state=States_text.set_time)
async def create_test(message, state: FSMContext):
    await state.finish()
    try:
        user = User(message.from_user.id)
        time_set = int(message.text)
        if not DATA_USERS.test_be(user.name_test):
            await message.reply(text='Урок удалён.')
            DATA_USERS.set_name_test(user.user_id, None, ignore=True)
            await start(message)
        else:
            key = DATA_USERS.set_time(user.user_id, user.name_test, time_set)
            if key:
                await message.reply("Время для тестирования было успешно установлено.",
                                    reply_markup=Markup().get_full_markup_teacher())
                DATA_USERS.set_name_test(message.from_user.id, message.text)
            else:
                await message.reply(f'<b>Ошибка</b>: вы не являетесь автором или имеете профиль студента.',
                                    parse_mode='html')
    except Exception as err:
        print(err)
        message.reply(text='Неверный формат для времени (пример правильного формата: 100).')


@db.message_handler(state=States_text.update_lesson)
async def create_test(message, state: FSMContext):
    user = User(message.from_user.id)
    await state.finish()
    if not DATA_USERS.test_be(user.name_test):
        await message.reply(text='Урок удалён.')
        DATA_USERS.set_name_test(user.user_id, None, ignore=True)
        await start(message)
    elif user.state != 'teacher' or user.name_test is None:
        await message.reply(text=f'<b>Ошибка</b>: вы не являетесь автором или урок не установлен.', parse_mode='html')
        await start(message)
    else:
        key = DATA_USERS.set_lesson(user.user_id, user.name_test, message.text)
        if key:
            await message.reply(text='Текст урока был изменён.')
        else:
            await message.reply(text=f'<b>Ошибка</b>: вы не являетесь автором данного урока.', parse_mode='html')


# async def send_reminder(id_user):
#     alarm_time = DATA_USERS.get_user_reminder(id_user)
#     now = datetime.now()
#
#     if now.strftime("%H:%M").lstrip("0") == alarm_time:
#         await bot.send_message(id_user, REMINDER_MESSAGE)
#
#
# async def send_all_reminders():
#     rows = DATA_USERS.get_all_users_reminders()
#     for row in rows:
#         id_user = row[0]
#         await send_reminder(id_user)
#
#
# schedule.every().minute.do(send_all_reminders)


# async def scheduler():
#     while True:
#         await schedule.run_pending()
#         await asyncio.sleep(1)

if __name__ == '__main__':
    # loop = asyncio.new_event_loop()
    # loop.create_task(scheduler())

    executor.start_polling(db)
