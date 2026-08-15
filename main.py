import streamlit as st
import psycopg2
from contextlib import contextmanager
import pandas as pd
import random
st.set_page_config(
    page_title="EnglishCard - Изучение английского",
    page_icon="📚",
    layout="wide"
)
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

            cur.execute('CREATE TABLE IF NOT EXISTS learning_stats(id SERIAL PRIMARY KEY,'
                        'user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,'
                        'word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,'
                        'correct_answers INTEGER DEFAULT 0,'
                        'total_attempts INTEGER DEFAULT 0,'
                        'last_reviewed DATE DEFAULT CURRENT_DATE);')
            conn.commit()

def get_word_id(word):
    word_id=''
    with get_db_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute('SELECT id FROM words where english_word = %s;',(word,))
            word_id = cur.fetchone()
    return word_id[0]
def insert_words():
    with get_db_connection() as conn:
        with get_cursor(conn) as cur:
            words = [('хлеб', 'bread'), ('молоко', 'milk'), ('яблоко', 'apple'), ('вода', 'water'), ('апельсин', 'orange'),
                     ('рыба', 'fish'), ('яйцо', 'egg'), ('чай', 'tea'), ('скорость', 'speed'), ('грустный', 'sad')]
            for i in words:
                cur.execute('INSERT INTO words(russian_word, english_word, is_common) VALUES(%s,%s,TRUE);', (i[0], i[1]))
                conn.commit()
def login_user(username):

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
    user_words=[]
    # insert_words()
    with get_db_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute('SELECT user_id, russian_word, english_word, is_common FROM words WHERE user_id = %s OR is_common = %s;',(user_id,True))
            for i in cur.fetchall():
                user_words.append({'id':i[0],'russian_word': i[1],'english_word':i[2],'is_common':i[3]})
            return user_words



def add_personal_word(user_id, russian_word, english_word):
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

def update_stats(user_id, word_id, correct_answers, total_attempts):
    """
    TODO: Обновить статистику изучения слова
    """
    with get_db_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute('SELECT user_id, word_id FROM learning_stats WHERE user_id = %s AND word_id = %s;',(user_id, word_id))
            present = cur.fetchone()

            if present is None:
                cur.execute('INSERT INTO learning_stats(user_id, word_id, correct_answers, total_attempts) VALUES(%s, %s, %s, %s);',(user_id, word_id, correct_answers, total_attempts))
                conn.commit()
            else:
                cur.execute('UPDATE learning_stats SET correct_answers =  correct_answers + %s, total_attempts = total_attempts + 1 WHERE user_id = %s AND word_id = %s;',(correct_answers,user_id, word_id))
                conn.commit()
def get_statistics(user_id):
    """
    TODO: Получить статистику пользователя
    Возвращает словарь со статистикой
    """
    user_statistic = ''
    stats = []
    with get_db_connection() as conn:
        with get_cursor(conn) as cur:
            cur.execute('SELECT learning_stats.user_id, words.english_word, learning_stats.correct_answers, learning_stats.total_attempts, learning_stats.last_reviewed FROM learning_stats JOIN words ON words.id = learning_stats.word_id WHERE learning_stats.user_id = %s;',(user_id,))
            user_statistic = cur.fetchall()

    for i in user_statistic:
        stats.append({'user_id': i[0], 'word': i[1], 'correct_answers': i[2], 'total_attempts': i[3], 'last_reviewed': i[4]})
    return stats


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def generate_options(correct_word, all_words):
    """
    Один вариант - правильный перевод, остальные - случайные слова из словаря
    Если слов не хватает, можно добавить слова-заглушки
    """
    help_words = ["moon", "grass", "window", "bread", "snow"]
    correct = correct_word['english_word']
    other_words = [i['english_word'] for i in all_words if i['english_word'] != correct]
    random.shuffle(other_words)
    three_mix = other_words[:3]
    for i in help_words:
        if len(three_mix) >= 3:
            break
        if i != correct and i not in three_mix:
            three_mix.append(i)
    result = [correct] + three_mix
    random.shuffle(result)
    return result



# ============================================================
# ИНТЕРФЕЙС ПРИЛОЖЕНИЯ (НЕОБХОДИМО ДОРАБОТАТЬ)
# ============================================================

def render_sidebar():
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
            st.success(f"Вы вошли как {st.session_state.user_name}!")
            if st.button('exit'):
                st.session_state.user_name = None
                st.rerun()
    return st.session_state.user_name

def render_study_tab(words):
    if "idx" not in st.session_state:
        st.session_state.idx = 0
    print(len(words))
    word = words[st.session_state.idx % len(words)]

    st.markdown(f"## Изучаем английские слова")
    st.markdown(f"### Слово: {word['russian_word']}")
    if st.session_state.get("options_word") != word["russian_word"]:
        st.session_state.options_word = word["russian_word"]
        st.session_state.options = generate_options(word, words)
        st.session_state.answer = None
    options = st.session_state.options
    cols = st.columns(len(options))
    for i, o in enumerate(options):
        with cols[i]:
            if st.button(o, key=f"opt_{i}"):
                st.session_state.answer = o
                if o == word['english_word']:
                    update_stats(st.session_state.user_id,get_word_id(word['english_word']),1, 1)
                else:
                    update_stats(st.session_state.user_id,get_word_id(word['english_word']),0,1)
    if st.session_state.get("answer"):
        if st.session_state.answer == word['english_word']:
            st.success("Правильно! 🎉")
        else:
            st.error(f"Неправильно. Ответ: {word['english_word']}")
    if st.button("Дальше →"):
        st.session_state.idx += 1
        st.rerun()


def render_add_word_tab():
    """
    TODO: Реализовать вкладку добавления слова
    - Поле для ввода слова на русском
    - Поле для ввода перевода
    - Кнопка добавления
    - Уведомление об успешном добавлении
    """
    st.write('Введите слово на русском:')
    new_russian_word = st.text_input('Русское слово')
    st.write('Введите слово на английском:')
    new_english_word = st.text_input('English word')

    if st.button('Добавить слово'):
        if new_russian_word and new_english_word:
            add_personal_word(st.session_state.user_id,new_russian_word,new_english_word)
            st.success("слово добавлено в базу данных")
        else:
            st.warning("Пожалуйста, введите слова")




def render_delete_word_tab(words):
    """
    TODO: Реализовать вкладку удаления слова
    - Выпадающий список с персональными словами пользователя
    - Кнопка удаления
    - Подтверждение удаления
    """

    personal_words = []

    for item in words:
        if item['id'] == 2 or item['is_common'] == False:
            personal_words.append(item['english_word'])
    if st.button('Get personal words'):
        st.session_state.show_words = True
    if st.session_state.get("show_words"):
        st.write(f'Персональные слова: {' '.join(personal_words)}')

    if st.button('Delete word'):
        st.session_state.show_delete = True
    if st.session_state.get("show_delete"):
        st.write('Какое слово вы хотите удалить?')
        word = st.text_input('Слово:')
        if st.button('Подтвердите удаление слова'):
            if word:
                word_id = get_word_id(word)
                delete_personal_word(st.session_state.user_id,word_id)
                st.success("слово удалено")
            else:
                st.error("Пожалуйста, введите слово")








def render_statistics_tab(user_id):
    word_stats = get_statistics(user_id)
    correct_answers = 0
    total_attempts = 0
    user_column = []
    if st.button('Получить статистику пользователя'):
        st.write(f'Количество изученных слов: {len(word_stats)}')
        for i in word_stats:
            total_attempts += i['total_attempts']
            correct_answers += i['correct_answers']
            user_column.append({'Слово':i['word'], 'Правильно': i['correct_answers'],'Всего попыток':i['total_attempts'],'last_reviewed':i['last_reviewed']})
        st.write(f'Процент правильных ответов: {(correct_answers*100)//total_attempts}%')
        df = pd.DataFrame(user_column)
        df["Ошибки"] = df["Всего попыток"] - df["Правильно"]
        st.table(df)
        long = df.melt(
            id_vars="Слово",
            value_vars=["Правильно", "Ошибки"],
            var_name="Тип",
            value_name="Значение",
        )
        st.bar_chart(long, x="Слово", y="Значение", color="Тип", stack=False)



def render_schema():
    """
    TODO: Реализовать отображение схемы базы данных (дополнительное требование)
    """
    if st.button('Получить схему Базы Данных'):
        shema = '''
        digraph DB {
            rankdir=LR;
            node [shape=record, fontname="Arial", fontsize=11];
    
            users [label="{users|id PK\\lusername\\lcreated_at\\l}"];
            words [label="{words|id PK\\luser_id FK\\lrussian_word\\lenglish_word\\lis_common\\lcreated_at\\l}"];
            stats [label="{learning_stats|id PK\\luser_id FK\\lword_id FK\\lcorrect_answers\\ltotal_attempts\\llast_reviewed\\l}"];
    
            words -> users;
            stats -> users;
            stats -> words;
        }
        '''

        st.subheader("Схема БД")
        st.graphviz_chart(shema)


def main():
    st.title("📚 EnglishCard - Изучай английский с удовольствием!")
    init_database()
    username = render_sidebar()
    if username is None:
        st.stop()
    else:
        st.session_state.user_id = login_user(st.session_state.user_name)
        words = get_user_words(st.session_state.user_id)
        # Создание вкладок
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📖 Изучение", "➕ Добавить слово", "🗑️ Удалить слово", "📊 Статистика","Схема базы данных"])
        with tab1:
            render_study_tab(words)
        with tab2:
            render_add_word_tab()
        with tab3:
            render_delete_word_tab(words)
        with tab4:
            render_statistics_tab(st.session_state.user_id)
        with tab5:
            render_schema()

if __name__ == "__main__":
    main()