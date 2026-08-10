import streamlit as st
import psycopg2
from contextlib import contextmanager
import pandas as pd
import random
from datetime import datetime

# ============================================================
# НАСТРОЙКА СТРАНИЦЫ
# ============================================================
# st.set_page_config(
#     page_title="EnglishCard - Изучение английского",
#     page_icon="📚",
#     layout="wide"
# )


# ============================================================
# РАБОТА С БАЗОЙ ДАННЫХ (НЕОБХОДИМО РЕАЛИЗОВАТЬ)
# ============================================================
@contextmanager
def get_db_connection():
    connect = psycopg2.connect(host = 'localhost', database = 'english_card', user = 'postgres', password = 'postgres')
    try:
        yield connect
    finally:
        connect.close()
@contextmanager
def get_cursor(conn):
    cur = conn.cursor()
    try:
        yield cur
    finally:
        cur.close()
def init_database():
    """
    TODO: Реализовать создание таблиц, если они не существуют
    Необходимые таблицы:
    1. users (id, username, created_at)
    2. common_words (id, russian_word, english_word, created_at)
    3. user_words (id, user_id, russian_word, english_word, created_at)
    4. learning_stats (id, user_id, word_id, word_type, correct_answers, total_attempts, last_reviewed)

    Также заполнить common_words начальными словами (минимум 10 слов)
    """
    with get_db_connection() as conn:
        with get_cursor(conn) as cur:
            # cur.execute('DROP TABLE  learning_stats; DROP TABLE words; DROP TABLE users')
            cur.execute('CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY,'
                        'username VARCHAR(100) NOT NULL UNIQUE,'
                        'created_at DATE DEFAULT CURRENT_DATE);')

            cur.execute('CREATE TABLE IF NOT EXISTS words(id SERIAL PRIMARY KEY,'
                        'user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,'
                        'russian_word VARCHAR(50) UNIQUE,'
                        'english_word VARCHAR(50) UNIQUE,'
                        'is_common BOOLEAN DEFAULT FALSE,' #FALSE - пользовательское слово, TRUE - общее слово 
                        'created_at DATE DEFAULT CURRENT_DATE);')

            # cur.execute('CREATE TABLE IF NOT EXISTS user_words(id SERIAL PRIMARY KEY,'
            #             'user_id INTEGER NOT NULL REFERENCES users(id),'
            #             'russian_word VARCHAR(70),'
            #             'english_word VARCHAR(70),'
            #             'created_at TIMESTAMP WITH ZONE DEFAULT CURRENT_TIMESTAMP);')

            # cur.execute('CREATE TABLE IF NOT EXISTS word_types(id SERIAL PRIMARY KEY, type VARCHAR(60) NOT NULL UNIQUE);')

            cur.execute('CREATE TABLE IF NOT EXISTS learning_stats(id SERIAL PRIMARY KEY,'
                        'user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,'
                        'word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,'
                        'correct_answers INTEGER DEFAULT 0,'
                        'total_attempts INTEGER DEFAULT 0,'
                        'last_reviewed DATE DEFAULT CURRENT_DATE);')
            # cur.execute('DELETE FROM words()')
            conn.commit()
            # cur.execute('SELECT id FROM users')
            # print(cur.fetchall())
            cur.execute('SELECT * FROM words')
            print(cur.fetchall())
def insert_words():
    with get_db_connection() as conn:
        with get_cursor(conn) as cur:
            words = [('хлеб', 'bread'), ('молоко', 'milk'), ('яблоко', 'apple'), ('вода', 'water'), ('апельсин', 'orange'),
                     ('рыба', 'fish'), ('яйцо', 'egg'), ('чай', 'tea'), ('скорость', 'speed'), ('грустный', 'sad')]
            for i in words:
                cur.execute('INSERT INTO words(russian_word, english_word, is_common) VALUES(%s,%s,TRUE);', (i[0], i[1]))
                conn.commit()
def login_user(username):
    """
    TODO: Реализовать вход пользователя
    Если пользователь существует - вернуть его id
    Если нет - создать нового и вернуть его id
    """
    with get_db_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute('SELECT id FROM users WHERE username = %s;', (username,))
            user = cur.fetchone()
            if user:
                return user[0]
            else:
                cur.execute('INSERT INTO users(username) VALUES(%s) RETURNING id;', (username,))
                new_user = cur.fetchone()
                conn.commit()
                return new_user[0]

def get_user_words(user_id):
    """
    TODO: Получить все слова пользователя (общие + персональные)
    Возвращает список словарей: [{'id': 1, 'russian_word': 'красный', 'english_word': 'red', 'word_type': 'common'}, ...]
    """
    user_words=[]
    dict_words={'id':None,'russian_word': None,'english_word':None,'is_common':None}
    with get_db_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute('SELECT user_id, russian_word, english_word, is_common FROM words WHERE user_id = %s OR is_common = %s;',(user_id,True))
            for i in cur.fetchall():
                user_words.append({'id':i[0],'russian_word': i[1],'english_word':i[2],'is_common':i[3]})
            return user_words


def add_personal_word(user_id, russian_word, english_word):
    """
    TODO: Добавить персональное слово для пользователя
    Проверить, нет ли уже такого слова
    Возвращает True/False
    """
    with get_db_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute('SELECT russian_word FROM words')
            list_words=[]
            words = cur.fetchall()
            for i in words:
                list_words.append(i[0])
            if russian_word in list_words:
                return False
            else:
                cur.execute(
                    'INSERT INTO words(user_id, russian_word, english_word, is_common) VALUES(%s,%s,%s,FALSE);',
                    (user_id, russian_word, english_word))
                conn.commit()
                return True



def delete_personal_word(user_id, word_id):
    """
    TODO: Удалить персональное слово пользователя
    Возвращает True/False
    """
    with get_db_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute('SELECT id FROM words WHERE user_id = %s AND id = %s;',(user_id,word_id))
            user = cur.fetchone()
            if user:
                cur.execute('DELETE FROM words WHERE id = %s and user_id =%s;',(word_id,user_id))
                conn.commit()
                return True
            else:
                return False

def update_stats(user_id, word_id, word_type, is_correct):
    """
    TODO: Обновить статистику изучения слова
    """



def get_statistics(user_id):
    """
    TODO: Получить статистику пользователя
    Возвращает словарь со статистикой
    """
    pass


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def generate_options(correct_word, all_words):
    """
    TODO: Сгенерировать 4 варианта ответа для викторины
    Один вариант - правильный перевод, остальные - случайные слова из словаря
    Если слов не хватает, можно добавить слова-заглушки
    """
    pass


# ============================================================
# ИНТЕРФЕЙС ПРИЛОЖЕНИЯ (НЕОБХОДИМО ДОРАБОТАТЬ)
# ============================================================

def render_sidebar():
    """
    TODO: Реализовать боковую панель с авторизацией
    - Поле для ввода имени
    - Кнопка входа
    - Приветствие после входа
    - Кнопка выхода
    """
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    with st.sidebar:
        st.write('Добро пожаловать!')
        if st.session_state.user_name is None:
            name_input = st.text_input("Введите ваше имя:")
            if st.button('Зарегистрироваться'):
                if name_input:
                    st.session_state.user_name = name_input
                    st.rerun()
                else:
                    st.warning("Пожалуйста, введите имя")
        else:
            st.write(f"Приятно познакомиться, {st.session_state.user_name}!")

            if st.button('exit'):
                st.session_state.user_name = None
                st.rerun()



def render_study_tab(words):
    """
    TODO: Реализовать вкладку изучения слов
    - Отображение текущего слова на русском
    - 4 кнопки с вариантами перевода
    - Обработка правильных/неправильных ответов
    - Кнопка следующего слова
    """
    pass


def render_add_word_tab():
    """
    TODO: Реализовать вкладку добавления слова
    - Поле для ввода слова на русском
    - Поле для ввода перевода
    - Кнопка добавления
    - Уведомление об успешном добавлении
    """
    pass


def render_delete_word_tab(words):
    """
    TODO: Реализовать вкладку удаления слова
    - Выпадающий список с персональными словами пользователя
    - Кнопка удаления
    - Подтверждение удаления
    """
    pass


def render_statistics_tab(user_id):
    """
    TODO: Реализовать вкладку статистики (дополнительное требование)
    - Количество изученных слов
    - Количество попыток
    - Процент правильных ответов
    - История последних попыток
    """
    pass


def render_schema():
    """
    TODO: Реализовать отображение схемы базы данных (дополнительное требование)
    """
    pass


# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

def main():
    init_database()
    # insert_words()
    print(login_user('Dmitriy'))
    print(login_user('Oleg'))
    # print(get_user_words(1))
    print(add_personal_word(1,'собака','dog'))
    # print(delete_personal_word(1,13))
    print(get_user_words(1))
    """
    Главная функция приложения
    TODO: Реализовать основную логику:
    1. Инициализация БД
    2. Авторизация пользователя
    3. Отображение вкладок с функционалом
    4. Приветственное сообщение для неавторизованных пользователей 
    
    """

    # st.title("📚 EnglishCard - Изучай английский с удовольствием!")

    # TODO: Инициализация состояния сессии
    # st.session_state.user_id
    # st.session_state.username

    # TODO: Инициализация БД
    # init_database()

    # TODO: Боковая панель с авторизацией
    # render_sidebar()

    # TODO: Основной контент в зависимости от авторизации
    # if st.session_state.user_id:
    #     words = get_user_words(st.session_state.user_id)
    #     # Создание вкладок
    #     tab1, tab2, tab3, tab4 = st.tabs(["📖 Изучение", "➕ Добавить слово", "🗑️ Удалить слово", "📊 Статистика"])
    #     with tab1:
    #         render_study_tab(words)
    #     # ... остальные вкладки
    # else:
    #     # Приветственное сообщение
    #     pass


if __name__ == "__main__":
    main()