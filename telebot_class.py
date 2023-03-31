import json
import sqlite3
from aiogram import types
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher.filters.state import StatesGroup, State
from random import shuffle
from datetime import datetime, timedelta


FORMAT_DATE = '%d %m %Y %H:%M'
DATA_USER = 'USERS_SET.db'
DATA_USER_SET = 'users'
DATA_TESTS = 'tests'
DATA_TESTS_TRY = 'tests_try'
DATA_USERNAME = 'user_name'
CALL_BACK = CallbackData("call", "func", "action")
CALL_BACK_TEST = CallbackData("None", "func", "action", 'name_test')


class DATA_USERS_SET:
    def __init__(self):
        self.connect = sqlite3.connect(DATA_USER)
        self.cursor = self.connect.cursor()

    def create(self):
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {DATA_USER_SET}(user_id INTEGER, "
                            f"state TEXT, name_test TEXT DEFAULT NULL)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS tests(user_id INTEGER, name_test TEXT, test TEXT DEFAULT '[]', "
                            "lesson TEXT DEFAULT '[]', time INTEGER DEFAULT 10, id integer primary key)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS tests_try("
                            "user_id INTEGER, name_test TEXT, test_try TEXT, end TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS user_name("
                            "user_id INTEGER, name_test TEXT, username TEXT)")
        self.connect.commit()

    def set_or_update_state(self, user_id, state):
        if state not in ['teacher', 'student']:
            raise ValueError("state invalid nor teacher or student")
        self.cursor.execute(f"SELECT user_id FROM {DATA_USER_SET} WHERE user_id = {user_id}")
        data = self.cursor.fetchone()
        if data is None:
            self.cursor.execute(f"INSERT INTO {DATA_USER_SET} (user_id, state) VALUES(?, ?)", (user_id, state))
            self.connect.commit()
        else:
            self.cursor.execute(f"UPDATE {DATA_USER_SET} SET state = (?), name_test = NULL WHERE user_id = (?)",
                                (state, user_id))
            self.connect.commit()

    def test_be(self, name_test):
        self.cursor.execute(f"SELECT name_test FROM {DATA_TESTS} WHERE name_test = '{name_test}'")
        data = self.cursor.fetchone()
        if data is None:
            return False
        return True

    def set_name_test(self, user_id, name_test, ignore=False):
        self.cursor.execute(f"SELECT state FROM {DATA_USER_SET} WHERE user_id = {user_id}")
        data = self.cursor.fetchone()
        if data is None:
            return False
        if not self.test_be(name_test) and not ignore:
            return False
        self.cursor.execute(f"SELECT name_test FROM {DATA_USER_SET} WHERE user_id = {user_id}")
        data = self.cursor.fetchone()
        if data is None:
            self.cursor.execute(f"INSERT INTO {DATA_USER_SET} (user_id, name_test) VALUES(?, ?)", (user_id, name_test))
            self.connect.commit()
        else:
            self.cursor.execute(f"UPDATE {DATA_USER_SET} SET name_test = (?) WHERE user_id = (?)", (name_test, user_id))
            self.connect.commit()
        return True

    def del_name_test_in_user(self, user_id):
        self.cursor.execute(f"SELECT state FROM {DATA_USER_SET} WHERE user_id = {user_id}")
        data = self.cursor.fetchone()
        if data is None:
            return False
        self.cursor.execute(f"SELECT name_test FROM {DATA_USER_SET} WHERE user_id = {user_id}")
        data = self.cursor.fetchone()
        if data is None:
            self.cursor.execute(f"INSERT INTO {DATA_USER_SET} (user_id, name_test) VALUES(?, ?)", (user_id, None))
            self.connect.commit()
        else:
            self.cursor.execute(f"UPDATE {DATA_USER_SET} SET name_test = (?) WHERE user_id = (?)", (None, user_id))
            self.connect.commit()
        return True

    def create_test(self, user_id, name_test):
        if self.test_be(name_test):
            return False
        self.cursor.execute(f"INSERT INTO {DATA_TESTS} (user_id, name_test) VALUES(?, ?)", (user_id, name_test))
        self.connect.commit()
        self.set_name_test(user_id, name_test)
        return True

    def set_test_for_class(self, user_id, name_test, test):
        try:
            if not self.test_be(name_test):
                return False
            self.cursor.execute(f"SELECT name_test, user_id FROM {DATA_TESTS} WHERE name_test = {name_test}")
            name, user = self.cursor.fetchone()
            if user != user_id or name is None:
                return False
            self.cursor.execute(f"UPDATE {DATA_TESTS} SET test = (?) WHERE name_test = (?)",
                                (json.dumps(test, ensure_ascii=False), name_test))
            self.connect.commit()
            return True
        except Exception as err:
            print(err)
            return False

    def add_test_for_teacher(self, user_id, name_test, test):
        if not self.test_be(name_test):
            return False
        self.cursor.execute(f"SELECT name_test, user_id FROM {DATA_TESTS} WHERE name_test = (?)", [name_test])
        name, user = self.cursor.fetchone()
        if user != user_id or name is None:
            return False
        self.cursor.execute(f"SELECT test FROM {DATA_TESTS} WHERE name_test = (?)", [name_test])
        data = json.loads(self.cursor.fetchone()[0])
        data.append(test)
        self.cursor.execute(f"UPDATE {DATA_TESTS} SET test = (?) WHERE name_test = (?)",
                            (json.dumps(data, ensure_ascii=False), name_test))
        self.connect.commit()
        self.cursor.execute(f"DELETE FROM {DATA_TESTS_TRY} WHERE name_test = (?)",
                            [name_test])
        self.connect.commit()
        return True

    def del_test_for_teacher(self, user_id, name_test, index):
        try:
            if not self.test_be(name_test):
                return False
            self.cursor.execute(f"SELECT name_test, user_id FROM {DATA_TESTS} WHERE name_test = (?)", [name_test])
            name, user = self.cursor.fetchone()
            if user != user_id or name is None:
                return False
            self.cursor.execute(f"SELECT test FROM {DATA_TESTS} WHERE name_test = (?)", [name_test])
            data = json.loads(self.cursor.fetchone()[0])
            del data[index]
            self.cursor.execute(f"UPDATE {DATA_TESTS} SET test = (?) WHERE name_test = (?)",
                                (json.dumps(data, ensure_ascii=False), name_test))
            self.connect.commit()
            self.cursor.execute(f"DELETE FROM {DATA_TESTS_TRY} WHERE name_test = (?)",
                                [name_test])
            self.connect.commit()
            return True
        except Exception as err:
            print(err)
            return False

    def set_lesson(self, user_id, name_test, text):
        try:
            if not self.test_be(name_test):
                return False
            self.cursor.execute(f"SELECT name_test, user_id FROM {DATA_TESTS} WHERE name_test = (?)", [name_test])
            name, user = self.cursor.fetchone()
            if user != user_id or name is None:
                return False
            ln = len(text)
            result = []
            count = ln // 1000
            count = count + 1 if ln % 1000 else count
            start = 0
            end = 1000
            for _ in range(count):
                result.append(text[start: end])
                start += 1000
                end += 1000
            # print(len(result))
            result = json.dumps(result, ensure_ascii=False)
            self.cursor.execute(f"UPDATE {DATA_TESTS} SET lesson = (?) WHERE name_test = (?)",
                                (result, name_test))
            self.connect.commit()
            return True
        except Exception as err:
            print(err)
            return False

    def get_lesson(self, user_id):
        self.cursor.execute(f"SELECT name_test FROM {DATA_USER_SET} WHERE user_id = {user_id}")
        data = self.cursor.fetchone()
        if data is None:
            return False
        name_test = data[0]
        if not self.test_be(name_test):
            return False
        self.cursor.execute(f"SELECT lesson FROM {DATA_TESTS} WHERE name_test = (?)", [name_test])
        data = self.cursor.fetchone()
        if data is None:
            return False
        data = json.loads(data[0])
        return data

    def get_test_for_name(self, user_id):
        self.cursor.execute(f"SELECT name_test FROM {DATA_USER_SET} WHERE user_id = {user_id}")
        data = self.cursor.fetchone()
        if data is None:
            return False
        if data[0] is None:
            return False
        self.cursor.execute(f"SELECT test FROM {DATA_TESTS} WHERE name_test = (?)", [data[0]])
        data = self.cursor.fetchone()
        return json.loads(data[0])

    def get_test_for_teacher(self, user_id):
        self.cursor.execute(f"SELECT name_test FROM {DATA_TESTS} WHERE user_id = {user_id}")
        data = tuple([i[0] for i in self.cursor.fetchall()])
        return data

    def set_time(self, user_id, name_test, time):
        try:
            if not self.test_be(name_test):
                return False
            self.cursor.execute(f"SELECT name_test, user_id FROM {DATA_TESTS} WHERE name_test = (?)", [name_test])
            name, user = self.cursor.fetchone()
            if user != user_id or name is None:
                return False
            self.cursor.execute(f"UPDATE {DATA_TESTS} SET time = (?) WHERE name_test = (?)",
                                (time, name_test))
            self.connect.commit()
            return True
        except Exception as err:
            print(err)
            return False

    def test_is_open(self, user_id, name_test):
        try:
            self.cursor.execute(f"SELECT end FROM {DATA_TESTS_TRY} "
                                f"WHERE name_test = (?) AND user_id = (?)", [name_test, user_id])
            date_now = datetime.now()
            date_test = datetime.strptime(self.cursor.fetchone()[0], FORMAT_DATE)
            if date_now >= date_test:
                return False
            return True
        except Exception as err:
            print(err)
            return False

    def start_test(self, user_id, name_test):
        try:
            if not self.test_be(name_test):
                return False
            self.cursor.execute(f"SELECT user_id FROM {DATA_TESTS_TRY} "
                                f"WHERE name_test = (?) AND user_id = (?)", [name_test, user_id])
            if self.cursor.fetchone() is None:
                self.cursor.execute(f"SELECT test, time FROM {DATA_TESTS} "
                                    f"WHERE name_test = (?)", [name_test])
                test, t = self.cursor.fetchall()[0]
                test = json.loads(test)
                time_set = (datetime.now() + timedelta(seconds=t * 60)).strftime(FORMAT_DATE)
                test_try = json.dumps([[None, i['otv']] for i in test], ensure_ascii=False)

                self.cursor.execute(
                    f"INSERT INTO {DATA_TESTS_TRY} (user_id, name_test, test_try, end) VALUES(?, ?, ?, ?)",
                    (user_id, name_test, test_try, time_set))
                self.connect.commit()
                return True
            else:
                self.cursor.execute(f"SELECT end FROM {DATA_TESTS_TRY} "
                                    f"WHERE name_test = (?) AND user_id = (?)", [name_test, user_id])
                date_now = datetime.now()
                date_test = datetime.strptime(self.cursor.fetchone()[0], FORMAT_DATE)
                if date_now >= date_test:
                    return False
                return True

        except Exception as err:
            print(err)
            return False

    def get_test_try(self, user_id, name_test):
        try:
            if not self.test_be(name_test):
                return False
            self.cursor.execute(f"SELECT test_try FROM {DATA_TESTS_TRY} "
                                f"WHERE name_test = (?) AND user_id = (?)", [name_test, user_id])
            data = json.loads(self.cursor.fetchone()[0])
            if data is None:
                return False
            else:
                return data
        except Exception as err:
            print(err)
            return False

    def save_otv(self, user_id, name_test, index, otv):
        try:
            if not self.test_be(name_test):
                return False
            self.cursor.execute(f"SELECT test_try FROM {DATA_TESTS_TRY} "
                                f"WHERE name_test = (?) AND user_id = (?)", [name_test, user_id])
            data = json.loads(self.cursor.fetchone()[0])
            data[index][0] = otv
            data = json.dumps(data, ensure_ascii=False)
            self.cursor.execute(f"UPDATE {DATA_TESTS_TRY} SET test_try = (?) WHERE name_test = (?) AND user_id = (?)",
                                (data, name_test, user_id))
            self.connect.commit()
            return True
        except Exception as err:
            print(err)
            return False

    def count_true_test(self, user_id, name_test):
        self.cursor.execute(f"SELECT end FROM {DATA_TESTS_TRY} "
                            f"WHERE name_test = (?) AND user_id = (?)", [name_test, user_id])
        date_now = datetime.now()
        data = self.cursor.fetchone()
        if data is None:
            return False
        date_test = datetime.strptime(data[0], FORMAT_DATE)
        if date_now < date_test:
            return False
        tests_try = self.get_test_try(user_id, name_test)
        if type(tests_try) != bool:
            return f'{sum([i[0] == i[1] for i in tests_try])} / {len(tests_try)}'
        else:
            return '0'

    def close_test(self, user_id, name_test):
        date = (datetime.now() - timedelta(seconds=60)).strftime(FORMAT_DATE)
        self.cursor.execute(f"UPDATE {DATA_TESTS_TRY} SET end = (?) WHERE name_test = (?) AND user_id = (?)",
                            (date, name_test, user_id))
        self.connect.commit()

    def set_username(self, user_id, name_test, username):
        if not self.test_be(name_test):
            return False
        self.cursor.execute(f"SELECT username FROM {DATA_USERNAME} "
                            f"WHERE username = (?) AND name_test = (?)", [username, name_test])
        if self.cursor.fetchone() is not None:
            return False
        self.cursor.execute(f"SELECT username FROM {DATA_USERNAME} "
                            f"WHERE name_test = (?) AND user_id = (?)", [name_test, user_id])
        data = self.cursor.fetchone()
        if data is not None:
            self.cursor.execute(f"UPDATE {DATA_USERNAME} SET username = (?) WHERE name_test = (?) AND user_id = (?)",
                                (username, name_test, user_id))
            self.connect.commit()
        else:
            self.cursor.execute(f"INSERT INTO {DATA_USERNAME} (user_id, name_test, username) VALUES(?, ?, ?)",
                                (user_id, name_test, username))
            self.connect.commit()
        return True

    def be_user_name_for_test(self, user_id, name_test):
        if not self.test_be(name_test):
            return None
        self.cursor.execute(f"SELECT username FROM {DATA_USERNAME} "
                            f"WHERE name_test = (?) AND user_id = (?)", [name_test, user_id])
        data = self.cursor.fetchone()
        if data is None:
            return False
        return data[0]

    def get_test_try_for_teacher(self, user_id, name_test):
        if not self.test_be(name_test):
            return False
        self.cursor.execute(f"SELECT user_id FROM {DATA_TESTS_TRY} "
                            f"WHERE name_test = (?)", [name_test])
        data = self.cursor.fetchall()
        return [[i[0], self.be_user_name_for_test(i[0], name_test)] for i in data]

    def del_test_try(self, user_id, name_test):
        if not self.test_be(name_test):
            return False
        self.cursor.execute(f"DELETE FROM {DATA_TESTS_TRY} WHERE user_id = (?) AND name_test = (?)",
                            [user_id, name_test])
        self.connect.commit()

    def del_tests(self, user_id, name_test):
        try:
            if not self.test_be(name_test):
                return False
            self.cursor.execute(f"SELECT name_test, user_id FROM {DATA_TESTS} WHERE name_test = (?)", [name_test])
            name, user = self.cursor.fetchone()
            if user != user_id or name is None:
                return False
            self.cursor.execute(f"UPDATE {DATA_USER_SET} SET name_test = NULL WHERE name_test = (?) AND user_id = (?)",
                                [name_test, user_id])
            self.connect.commit()
            self.cursor.execute(f"DELETE FROM {DATA_TESTS} WHERE name_test = (?)",
                                [name_test])
            self.connect.commit()
            self.cursor.execute(f"DELETE FROM {DATA_TESTS_TRY} WHERE name_test = (?)",
                                [name_test])
            self.connect.commit()
            self.cursor.execute(f"DELETE FROM {DATA_USERNAME} WHERE name_test = (?)",
                                [name_test])
            self.connect.commit()
            return True
        except Exception as err:
            print(err)
            return False

    def get_list_test(self, user_id):
        self.cursor.execute(f"SELECT name_test FROM {DATA_USERNAME} WHERE user_id = (?)", [user_id])
        data = self.cursor.fetchall()
        if not data:
            return False
        else:
            return [i[0] for i in data] 

    def write_reviews(self, text, user_id):
        date = datetime.now()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS data_review(
                id_user INTEGER,
                review TEXT,
                datetime TEXT
                )""")
        self.connect.commit()
        self.cursor.execute(f"SELECT review FROM data_review WHERE id_user = {user_id}")
        data = self.cursor.fetchone()
        if data is None:
            self.cursor.execute("INSERT INTO data_review VALUES(?,?,?)", (user_id, text, date.strftime(FORMAT_DATE)))
            self.connect.commit()
            return True
        else:
            self.cursor.execute(f"UPDATE data_review SET review = (?), datetime = (?) WHERE id_user = (?)",
                                (text, date.strftime(FORMAT_DATE), user_id))
            self.connect.commit()
            return False

    def create_reminder(self, text, user_id):
        self.cursor.execute(f"SELECT reminder_time FROM data_reminder WHERE id_user = {user_id}")
        data = self.cursor.fetchone()
        if data is None:
            self.cursor.execute("INSERT INTO data_reminder VALUES(?,?)", (user_id, text))
            self.connect.commit()
            return True
        else:
            self.cursor.execute(f"UPDATE data_reminder SET reminder_time = (?) WHERE id_user = (?)",
                                (text, user_id))
            self.connect.commit()
            return False

    def get_user_reminder(self, id_user):
        self.cursor.execute('SELECT  reminder_time FROM data_reminder WHERE id_user=?', (id_user,))
        return self.cursor.fetchone()[0]

    def get_all_users_reminders(self):
        self.cursor.execute('SELECT id_user FROM data_reminder')
        return self.cursor.fetchall()

    def delete_reminder(self, id_user):
        self.cursor.execute("DELETE FROM data_reminder WHERE id_user=?", (id_user,))
        self.connect.commit()

    def find_test_try(self, user_id, name_test):
        self.cursor.execute(f"SELECT user_id FROM {DATA_TESTS_TRY} WHERE name_test = (?) AND user_id = (?)",
            (name_test, user_id))
        if self.cursor.fetchone() is None:
            return False
        return True

    def get_name_for_id_test(self, test_id):
        self.cursor.execute(f"SELECT name_test FROM {DATA_TESTS} WHERE id = (?)", [test_id])
        return self.cursor.fetchone()[0]

    def get_id_for_name_test(self, test_name):
        self.cursor.execute(f"SELECT id FROM {DATA_TESTS} WHERE name_test = (?)", [test_name])
        return self.cursor.fetchone()[0]


class User:
    def __init__(self, user_id):
        self.connect = sqlite3.connect(DATA_USER)
        self.cursor = self.connect.cursor()
        self.user_id = user_id
        self.cursor.execute(f"SELECT state FROM {DATA_USER_SET} WHERE user_id = {user_id}")
        data = self.cursor.fetchone()
        self.state = None if data is None else data[0]
        self.cursor.execute(f"SELECT name_test FROM {DATA_USER_SET} WHERE user_id = {user_id}")
        data = self.cursor.fetchone()
        self.name_test = None if data is None else data[0]


class States_text(StatesGroup):
    add_test = State()
    join_test = State()
    update_lesson = State()
    set_time = State()
    set_name_test = State()
    set_username = State()
    update_username = State()


class States_name_text(StatesGroup):
    name_text = State()


class States_review(StatesGroup):
    Q1 = State()


class States_reminder(StatesGroup):
    Q2 = State()


class Markup:
    def get_short_markup_teacher(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn1 = types.KeyboardButton(text='Мои тесты')
        btn2 = types.KeyboardButton(text='Создать тест')
        btn3 = types.KeyboardButton(text='Изменить профиль')
        btn4 = types.KeyboardButton(text='Оставить отзыв✍️')
        markup.add(btn1, btn2, btn3, btn4)
        return markup

    def get_short_markup_student(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn1 = types.KeyboardButton(text='Присоединиться к тесту')
        btn2 = types.KeyboardButton(text='Список тестов')
        btn3 = types.KeyboardButton(text='Изменить профиль')
        btn4 = types.KeyboardButton(text='Оставить отзыв✍️')
        # btn5 = types.KeyboardButton(text='Напоминалка⏰')
        markup.add(btn1, btn2, btn3, btn4)
        return markup

    def get_full_markup_teacher(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        btn1 = types.KeyboardButton(text='Посмотреть урок')
        btn2 = types.KeyboardButton(text='Посмотреть тест урока')
        btn3 = types.KeyboardButton(text='Посмотреть результаты')
        btn4 = types.KeyboardButton(text='Редактировать')
        btn5 = types.KeyboardButton(text='Удалить попытку')
        btn6 = types.KeyboardButton(text='Вернуться назад')

        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
        return markup

    def get_full_markup_teacher_edit(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn1 = types.KeyboardButton(text='Добавить вопрос')
        btn2 = types.KeyboardButton(text='Изменить текст урока')
        btn3 = types.KeyboardButton(text='Удалить вопрос')
        btn4 = types.KeyboardButton(text='Изменить время')
        btn5 = types.KeyboardButton(text='Удалить урок')
        btn6 = types.KeyboardButton(text='Вернуться в меню')
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
        return markup


    def get_full_markup_student(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        btn1 = types.KeyboardButton(text='Открыть урок')
        btn2 = types.KeyboardButton(text='Пройти тестирование')
        btn3 = types.KeyboardButton(text='Результат тестирования')
        btn4 = types.KeyboardButton(text='Изменить имя')
        btn5 = types.KeyboardButton(text='Оставить отзыв✍️')
        btn6 = types.KeyboardButton(text='Вернуться назад')

        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
        return markup

    def get_tests_markup_teacher(self, tests, index):
        markup = types.InlineKeyboardMarkup(row_width=1)
        if len(tests) <= index:
            index = 0
        tests_list = tests[index:]
        # print(len(tests_list))
        next_index = 0
        if len(tests_list) > 4:
            next_index = index + 4
            tests_list = tests_list[:4]
        for name in tests_list:
            btn = types.InlineKeyboardButton(text=name,
                                             callback_data=CALL_BACK.new(func='set name_test', action=DATA_USERS_SET().get_id_for_name_test(name)))
            markup.add(btn)
        if index != 0:
            markup.add(types.InlineKeyboardButton(text='Назад',
                                                  callback_data=CALL_BACK.new(func='open teacher',
                                                                              action=f'{index - 4}')))
        if next_index:
            markup.add(types.InlineKeyboardButton(text='Вперёд',
                                                  callback_data=CALL_BACK.new(func='open teacher',
                                                                              action=f'{next_index}')))
        return markup

    def get_test_markup_qe_teacher_result(self, tests, index, name_test):
        markup = types.InlineKeyboardMarkup(row_width=1)
        if len(tests) <= index:
            index = 0
        test_list = tests[index]
        otv = test_list['otv']
        qe = test_list['qe']
        err = test_list['err']
        otv_list = [otv] + err
        shuffle(otv_list)
        for i in otv_list:
            markup.add(types.InlineKeyboardButton(text=f'{i + "  ✔" if i == otv else i}', callback_data='None'))
        if index != 0:
            markup.add(types.InlineKeyboardButton(text=f'Назад',
                                                  callback_data=CALL_BACK_TEST.new(func='open teacher_result',
                                                                                   action=f'{index - 1}',
                                                                                   name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        # else:
        #     markup.add(types.InlineKeyboardButton(text=f'закрыть результат', callback_data='None'))
        if index != len(tests) - 1:
            markup.add(types.InlineKeyboardButton(text=f'Вперёд',
                                                  callback_data=CALL_BACK_TEST.new(func='open teacher_result',
                                                                                   action=f'{index + 1}',
                                                                                   name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        return markup, qe

    def get_test_markup_student(self, tests, tests_try, index, name_test):
        markup = types.InlineKeyboardMarkup(row_width=1)
        if len(tests) <= index:
            index = 0
        test_list = tests[index]
        otv_student = tests_try[index][0]
        otv = test_list['otv']
        qe = test_list['qe']
        err = test_list['err']
        otv_list = [otv] + err
        shuffle(otv_list)
        # print(otv_list, otv_student)
        for i in otv_list:
            markup.add(types.InlineKeyboardButton(text=f'{i + "  ✔" if i == otv_student else i}',
                                                  callback_data=CALL_BACK_TEST.new(
                                                      func='save otv', action=f'{index} {otv_list.index(i)}', name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))  
        if index != 0:
            markup.add(types.InlineKeyboardButton(text=f'Назад',
                                                  callback_data=CALL_BACK_TEST.new(func='open test student',
                                                                                   action=f'{index - 1}',
                                                                                   name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        if index != len(tests) - 1:
            markup.add(types.InlineKeyboardButton(text=f'Вперёд',
                                                  callback_data=CALL_BACK_TEST.new(func='open test student',
                                                                                   action=f'{index + 1}',
                                                                                   name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        else:
            markup.add(types.InlineKeyboardButton(text=f'Завершить тест',
                                                  callback_data=CALL_BACK_TEST.new(func='end test', action=f'None',
                                                                                   name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        return markup, qe

    def get_test_markup_student_for_teacher(self, tests, tests_try, index, name_test, user_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        if len(tests) <= index:
            index = 0
        test_list = tests[index]
        otv_student = tests_try[index][0]
        otv = test_list['otv']
        qe = test_list['qe']
        err = test_list['err']
        otv_list = [otv] + err
        shuffle(otv_list)
        # print(otv_list, otv_student)
        for i in otv_list:
            if i == otv_student and i != otv:
                i = i + '  ❌'
            elif i == otv_student and i == otv:
                i = i + "  ✔"
            markup.add(types.InlineKeyboardButton(text=f'{i}',
                                                  callback_data='None'))
        if index != 0:
            markup.add(types.InlineKeyboardButton(text=f'Назад',
                                                  callback_data=CALL_BACK_TEST.new(func='open test_try student',
                                                                                   action=f'{user_id} {index - 1}',
                                                                                   name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))

        if index == 0 or index == len(tests_try) - 1:
            markup.add(types.InlineKeyboardButton(text=f'Вернуться обратно',
                                                  callback_data=CALL_BACK_TEST.new(func='open test_try', action=f'{0}',
                                                                                   name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))

        if index != len(tests_try) - 1:
            markup.add(types.InlineKeyboardButton(text=f'Вперёд',
                                                  callback_data=CALL_BACK_TEST.new(func='open test_try student',
                                                                                   action=f'{user_id} {index + 1}',
                                                                                   name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        return markup, qe

    def get_tests_markup_teacher_del(self, tests, index, name_test):
        # print(tests)
        markup = types.InlineKeyboardMarkup(row_width=1)
        if len(tests) <= index:
            index = 0
        tests_list = tests[index:]
        # print(len(tests_list))
        next_index = 0

        if len(tests_list) > 4:
            next_index = index + 4
            tests_list = tests_list[:4]
        for name in tests_list:
            btn = types.InlineKeyboardButton(
                text=name['qe'][:20],
                callback_data=CALL_BACK_TEST.new(func='del test', action=f'{tests.index(name)}', name_test=DATA_USERS_SET().get_id_for_name_test(name_test)))
            markup.add(btn)
        if index != 0:
            markup.add(types.InlineKeyboardButton(
                text='Назад',
                callback_data=CALL_BACK_TEST.new(func='open teacher_del', action=f'{index - 4}', name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        if next_index:
            markup.add(types.InlineKeyboardButton(
                text='Вперёд',
                callback_data=CALL_BACK_TEST.new(func='open teacher_del', action=f'{next_index}', name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        return markup

    def get_test_try_for_teacher_markup(self, test_try, index, name_test):
        markup = types.InlineKeyboardMarkup(row_width=1)
        if len(test_try) <= index:
            index = 0
        tests_list = test_try[index:]
        next_index = 0
        if len(tests_list) > 4:
            next_index = index + 4
            tests_list = tests_list[:4]
        for name in tests_list:
            user_id, username = name
            count = DATA_USERS_SET().count_true_test(user_id, name_test)
            if not count:
                continue
            btn = types.InlineKeyboardButton(
                text=f'{username} - {count}',
                callback_data=CALL_BACK_TEST.new(func='open test_try student', action=f'{user_id} 0',
                                                 name_test=DATA_USERS_SET().get_id_for_name_test(name_test)))
            markup.add(btn)
        if index != 0:
            markup.add(types.InlineKeyboardButton(
                text='Назад',
                callback_data=CALL_BACK_TEST.new(func='open test_try', action=f'{index - 1}', name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        if next_index:
            markup.add(types.InlineKeyboardButton(
                text='Вперёд',
                callback_data=CALL_BACK_TEST.new(func='open test_try', action=f'{index + 1}', name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        return markup

    def get_test_try_for_teacher_markup_del(self, test_try, index, name_test):
        markup = types.InlineKeyboardMarkup(row_width=1)
        if len(test_try) <= index:
            index = 0
        tests_list = test_try[index:]
        next_index = 0
        if len(tests_list) > 4:
            next_index = index + 4
            tests_list = tests_list[:4]
        for name in tests_list:
            user_id, username = name
            btn = types.InlineKeyboardButton(text=f'{username}',
                                             callback_data=CALL_BACK_TEST.new(func='del test_try student',
                                                                              action=f'{user_id} {DATA_USERS_SET().get_id_for_name_test(name_test)}',
                                                                              name_test=DATA_USERS_SET().get_id_for_name_test(name_test)))
            markup.add(btn)
        if index != 0:
            markup.add(types.InlineKeyboardButton(text='Назад',
                                                  callback_data=CALL_BACK_TEST.new(func='open test_try_del',
                                                                                   action=f'{index - 1}',
                                                                                   name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        if next_index:
            markup.add(types.InlineKeyboardButton(text='Вперёд',
                                                  callback_data=CALL_BACK_TEST.new(func='open test_try_del',
                                                                                   action=f'{index + 1}',
                                                                                   name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        return markup

    def get_state_markup(self):
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton(text='Студент',
                                          callback_data=CALL_BACK.new(func='set_state', action='student'))
        btn2 = types.InlineKeyboardButton(text='Преподаватель',
                                          callback_data=CALL_BACK.new(func='set_state', action='teacher'))
        markup.add(btn1, btn2)
        return markup

    def get_lesson_markup(self, lesson, index, name_test):
        if len(lesson) <= index:
            index = 0
        markup = types.InlineKeyboardMarkup(row_width=1)
        result = lesson[index]
        if index != 0:
            markup.add(types.InlineKeyboardButton(text=f'Назад',
                                                  callback_data=CALL_BACK_TEST.new(
                                                      func='open lesson', action=f'{index - 1}', name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        if index != len(lesson) - 1:
            markup.add(types.InlineKeyboardButton(text=f'Вперёд',
                                                  callback_data=CALL_BACK_TEST.new(func='open lesson',
                                                                                   action=f'{index + 1}',
                                                                                   name_test=DATA_USERS_SET().get_id_for_name_test(name_test))))
        return markup, result

    def get_markup_list_test(self, tests_lists, index):
        markup = types.InlineKeyboardMarkup(row_width=1)
        if len(tests_lists) <= index:
            index = 0
        tests_list = tests_lists[index:]
        next_index = 0
        if len(tests_list) > 4:
            next_index = index + 4
            tests_list = tests_list[:4]
        for name in tests_list:
            btn = types.InlineKeyboardButton(
                text=f'{name}',
                callback_data=CALL_BACK.new(func='set name_test', action=DATA_USERS_SET().get_id_for_name_test(name)))
            markup.add(btn)
        if index != 0:
            markup.add(types.InlineKeyboardButton(
                text='Назад',
                callback_data=CALL_BACK_TEST.new(func='open test_list', action=f'{index - 1}', name_test='None')))
        if next_index:
            markup.add(types.InlineKeyboardButton(
                text='Вперёд',
                callback_data=CALL_BACK_TEST.new(func='open test_list', action=f'{index + 1}', name_test='None')))
        return markup

    def get_reminder_markup(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        
        btn1 = types.KeyboardButton(text='Установить напоминалку')
        btn2 = types.KeyboardButton(text='Удалить напоминалку')
        btn3 = types.KeyboardButton(text='Вернуться нaзад')

        markup.add(btn1, btn2, btn3)
        return markup

# a = DATA_USERS_SET()
# a.create()
# print(a.get_id_for_name_test("123"))