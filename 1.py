import sys
import sqlite3
import webbrowser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                             QTableWidgetItem, QPushButton)
from PyQt6.QtCore import Qt
from pyuic_1 import Ui_MainWindow  # Окно авторизации
from pyuic_2 import Ui_MainWindow_2  # Главное окно
from pyuic_3 import Ui_MainWindow_3  # Окно редактирования
from hash import hash_password, check_password  # Модуль для работы с хешированием паролей


class AuthWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Авторизация / Регистрация")

        self.is_registration_mode = False  # Режим по умолчанию - вход
        self.lineEdit_3.setVisible(False)  # Скрытие поля подтверждения пароля
        self.label_3.setVisible(False)  # Скрытие подписи для подтверждения

        self.pushButton.setText("Войти")
        self.pushButton_2.setText("Зарегистрироваться")

        # Подключение обработчиков событий
        self.pushButton.clicked.connect(self.handle_auth)
        self.pushButton_2.clicked.connect(self.toggle_mode)

    # Переключение между режимами входа и регистрации
    def toggle_mode(self):

        self.is_registration_mode = not self.is_registration_mode

        if self.is_registration_mode:
            # Дополнительные элементы для регистрации
            self.lineEdit_3.setVisible(True)
            self.label_3.setVisible(True)
            self.pushButton.setText("Зарегистрироваться")
            self.pushButton_2.setText("Войти")
            self.setWindowTitle("Регистрация")
        else:
            # Скрытие лишних элементов для входа
            self.lineEdit_3.setVisible(False)
            self.label_3.setVisible(False)
            self.pushButton.setText("Войти")
            self.pushButton_2.setText("Зарегистрироваться")
            self.setWindowTitle("Авторизация")

    # Определение, какой метод вызвать - вход или регистрация
    def handle_auth(self):
        if self.is_registration_mode:
            self.register()
        else:
            self.login()

    # Обработка попытки входа пользователя
    def login(self):
        login = self.lineEdit.text()
        password = self.lineEdit_2.text()

        # Проверка заполненности полей
        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль!")
            return

        # Подключение к базе данных и проверка учетных данных
        conn = sqlite3.connect('games.db')
        cursor = conn.cursor()
        try:
            # Поиск пользователя в базе
            cursor.execute("SELECT password_hash FROM users WHERE login=?", (login,))
            result = cursor.fetchone()

            # Проверка пароля
            if result and check_password(result[0], password):
                # Если успешно - открывтие главного окна
                self.main_window = GameDatabaseApp()
                self.main_window.show()
                self.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
        finally:
            conn.close()

            # Обработка регистрации нового пользователя

    def register(self):
        login = self.lineEdit.text()
        password = self.lineEdit_2.text()
        confirm_password = self.lineEdit_3.text()

        # Проверка заполненности всех полей
        if not login or not password or not confirm_password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        # Проверка совпадения паролей
        if password != confirm_password:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return

        # Проверка сложности пароля
        errors = []
        if len(password) < 8:
            errors.append("Пароль должен содержать не менее 8 символов")
        if not any(c.isdigit() for c in password):
            errors.append("Пароль должен содержать хотя бы одну цифру")
        if not any(c.isupper() for c in password):
            errors.append("Пароль должен содержать хотя бы одну заглавную букву")
        if not any(c.islower() for c in password):
            errors.append("Пароль должен содержать хотя бы одну строчную букву")

        if errors:
            QMessageBox.warning(self, "Ошибка", "Пароль не соответствует требованиям:\n- " + "\n- ".join(errors))
            return

        # Хеширование пароля и сохранение в базу
        hashed = hash_password(password)
        conn = sqlite3.connect('games.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (login, password_hash) VALUES (?, ?)", (login, hashed))
            conn.commit()
            QMessageBox.information(self, "Успех", "Регистрация успешна! Теперь вы можете войти.")
            self.toggle_mode()  # Переключение обратно на режим входа
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Логин уже существует")
        finally:
            conn.close()


# Главное окно приложения - менеджер игр
class GameDatabaseApp(QMainWindow, Ui_MainWindow_2):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Менеджер игр")

        # Инициализация базы данных и загрузка данных
        self.create_connection()
        self.load_data()

        self.pushButton.setText("Добавить игру")
        self.pushButton.clicked.connect(self.add_game)

        self.pushButton_3.setText("Удалить игру")
        self.pushButton_3.clicked.connect(self.delete_game)

        self.pushButton_2.setText("Редактировать игру")
        self.pushButton_2.clicked.connect(self.edit_game)

        # Подключение фильтров
        self.comboBox_2.currentIndexChanged.connect(self.search_games)  # Фильтр по жанру
        self.comboBox.currentIndexChanged.connect(self.search_games)  # Фильтр по названию

        # Обработка двойного клика по таблице
        self.tableWidget.doubleClicked.connect(self.show_game_info)

    # Обработка нажатия клавиш - удаление по клавише Delete
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_game()
        else:
            super().keyPressEvent(event)

    # Создание подключения к базе данных и проверка структуры
    def create_connection(self):
        try:
            self.conn = sqlite3.connect('games.db')
            self.cursor = self.conn.cursor()

            # Проверка существование необходимых колонок
            self.cursor.execute("PRAGMA table_info(games)")
            columns = [column[1] for column in self.cursor.fetchall()]

            # Добавление колонки, если их нет
            if 'image_url' not in columns:
                self.cursor.execute("ALTER TABLE games ADD COLUMN image_url TEXT")
            if 'trailer_url' not in columns:
                self.cursor.execute("ALTER TABLE games ADD COLUMN trailer_url TEXT")

            self.conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка базы данных: {str(e)}')

    # Загрузка данных из базы и отображение в таблице
    def load_data(self):
        try:
            # Получение всех игры из базы
            self.cursor.execute("SELECT * FROM games")
            games = self.cursor.fetchall()

            # Уникальные жанры и названия для фильтров
            genres = set()
            titles = set()
            for game in games:
                genres.add(game[2])  # Жанр
                titles.add(game[1])  # Название

            # Настройка выпадающих списков фильтров
            self.comboBox_2.clear()
            self.comboBox_2.addItem("Все")
            self.comboBox_2.addItems(sorted(genres))

            self.comboBox.clear()
            self.comboBox.addItem("Все")
            self.comboBox.addItems(sorted(titles))

            # Настройка таблицы
            self.tableWidget.setRowCount(len(games))
            self.tableWidget.setColumnCount(7)
            self.tableWidget.setHorizontalHeaderLabels(
                ["ID", "Название", "Жанр", "Год", "Разработчик", "Изображение", "Трейлер"]
            )

            # Заполнение таблицы данными
            for row_idx, game in enumerate(games):
                for col_idx in range(7):
                    value = game[col_idx] if col_idx < len(game) else ""
                    self.tableWidget.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

                # Добавление кнопки для просмотра изображения
                if len(game) > 5 and game[5]:
                    btn_image = QPushButton("Просмотреть")
                    btn_image.clicked.connect(lambda _, url=game[5]: webbrowser.open(url))
                    self.tableWidget.setCellWidget(row_idx, 5, btn_image)

                # Добавление кнопки для просмотра трейлера
                if len(game) > 6 and game[6]:
                    btn_trailer = QPushButton("Смотреть")
                    btn_trailer.clicked.connect(lambda _, url=game[6]: webbrowser.open(url))
                    self.tableWidget.setCellWidget(row_idx, 6, btn_trailer)

        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')

    # Открытие окна для добавления новой игры
    def add_game(self):
        self.edit_window = GameEditWindow(self)
        self.edit_window.show()

    # Открытие окна для редактирования выбранной игры
    def edit_game(self):
        selected_items = self.tableWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите игру для редактирования!")
            return

        # Получение данных выбранной игры
        row = selected_items[0].row()
        game_id = self.tableWidget.item(row, 0).text()
        self.cursor.execute("SELECT * FROM games WHERE id=?", (game_id,))
        game_data = self.cursor.fetchone()

        # Открывание окна редактирования с данными игры
        self.edit_window = GameEditWindow(self, game_data)
        self.edit_window.show()

    # Удаление выбранной игры
    def delete_game(self):
        selected_items = self.tableWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите игру для удаления!")
            return

        # Подтверждение удаления
        row = selected_items[0].row()
        game_id = self.tableWidget.item(row, 0).text()
        game_name = self.tableWidget.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить игру '{game_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Удаление игры из базы
                self.cursor.execute("DELETE FROM games WHERE id=?", (game_id,))

                # Если это была последняя запись, сбрасывается автоинкремент
                self.cursor.execute("SELECT COUNT(*) FROM games")
                count = self.cursor.fetchone()[0]
                if count == 0:
                    self.cursor.execute("DELETE FROM sqlite_sequence WHERE name='games'")

                self.conn.commit()
                self.load_data()  # Обновление таблицы
                QMessageBox.information(self, "Успех", "Игра успешно удалена!")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить игру: {str(e)}")

    # Фильтрация игр по выбранным критериям
    def search_games(self):
        genre = self.comboBox_2.currentText()
        title = self.comboBox.currentText()

        # Формирование SQL-запроса с учетом фильтров
        query = "SELECT * FROM games WHERE 1=1"
        params = []

        if genre != "Все":
            query += " AND genre=?"
            params.append(genre)

        if title != "Все":
            query += " AND title=?"
            params.append(title)

        try:
            # Выполнение запроса и обновление таблицы
            self.cursor.execute(query, params)
            games = self.cursor.fetchall()

            self.tableWidget.setRowCount(len(games))
            for row_idx, game in enumerate(games):
                for col_idx in range(7):
                    value = game[col_idx] if col_idx < len(game) else ""
                    self.tableWidget.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

                # Кнопки для изображения и трейлера
                if len(game) > 5 and game[5]:
                    btn_image = QPushButton("Просмотреть")
                    btn_image.clicked.connect(lambda _, url=game[5]: webbrowser.open(url))
                    self.tableWidget.setCellWidget(row_idx, 5, btn_image)

                if len(game) > 6 and game[6]:
                    btn_trailer = QPushButton("Смотреть")
                    btn_trailer.clicked.connect(lambda _, url=game[6]: webbrowser.open(url))
                    self.tableWidget.setCellWidget(row_idx, 6, btn_trailer)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка поиска: {str(e)}")

    # Показ подробной информации об игре по двойному клику
    def show_game_info(self, index):
        row = index.row()
        game_id = self.tableWidget.item(row, 0).text()
        title = self.tableWidget.item(row, 1).text()
        genre = self.tableWidget.item(row, 2).text()
        year = self.tableWidget.item(row, 3).text()
        developer = self.tableWidget.item(row, 4).text()
        image_url = self.tableWidget.item(row, 5).text() if self.tableWidget.item(row, 5) else "Нет изображения"
        trailer_url = self.tableWidget.item(row, 6).text() if self.tableWidget.item(row, 6) else "Нет трейлера"

        # Формирование информации
        info = (
            f"ID: {game_id}\nНазвание: {title}\nЖанр: {genre}\n"
            f"Год выпуска: {year}\nРазработчик: {developer}\n"
            f"Изображение: {image_url}\nТрейлер: {trailer_url}"
        )
        QMessageBox.information(self, "Информация об игре", info)


# Окно для добавления/редактирования игры
class GameEditWindow(QMainWindow, Ui_MainWindow_3):

    def __init__(self, parent=None, game_data=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent  # Ссылка на родительское окно
        self.game_data = game_data  # Данные игры

        # Настройка окна в зависимости от режима
        if game_data:
            # Режим редактирования существующей игры
            self.setWindowTitle("Редактирование игры")
            self.lineEdit.setText(game_data[1])  # Название
            self.lineEdit_2.setText(game_data[2])  # Жанр
            self.lineEdit_3.setText(str(game_data[3]))  # Год
            self.lineEdit_4.setText(game_data[4])  # Разработчик
            self.lineEdit_5.setText(game_data[5] if len(game_data) > 5 else "")  # Изображение
            self.lineEdit_6.setText(game_data[6] if len(game_data) > 6 else "")  # Трейлер
        else:
            # Режим добавления новой игры
            self.setWindowTitle("Добавление новой игры")

        # Подключение кнопки сохранения
        self.pushButton.clicked.connect(self.save_game)

    # Сохранение игры в базу данных
    def save_game(self):
        # Получаем данные из полей формы
        title = self.lineEdit.text()
        genre = self.lineEdit_2.text()
        year = self.lineEdit_3.text()
        developer = self.lineEdit_4.text()
        image_url = self.lineEdit_5.text()
        trailer_url = self.lineEdit_6.text()

        # Проверка обязательных полей
        if not title or not genre or not year or not developer:
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля!")
            return

        # Проверка корректности года
        if not year.isdigit() or int(year) < 1970 or int(year) > 2025:
            QMessageBox.warning(self, "Ошибка", "Введите корректный год (1970-2025)")
            return

        if self.game_data:
            # Режим редактирования - обновление существующей записи
            try:
                self.parent.cursor.execute(
                    "UPDATE games SET title=?, genre=?, year=?, developer=?, image_url=?, trailer_url=? WHERE id=?",
                    (title, genre, year, developer, image_url, trailer_url, self.game_data[0]))
                self.parent.conn.commit()
                QMessageBox.information(self, "Успех", "Игра успешно обновлена!")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить игру: {str(e)}")
        else:
            # Режим добавления - создание новой записи
            try:
                self.parent.cursor.execute(
                    "INSERT INTO games (title, genre, year, developer, image_url, trailer_url) VALUES (?, ?, ?, ?, ?, ?)",
                    (title, genre, year, developer, image_url, trailer_url))
                self.parent.conn.commit()
                QMessageBox.information(self, "Успех", "Игра успешно добавлена!")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить игру: {str(e)}")

        # Обновление данных в родительском окне
        self.parent.load_data()
        self.close()


if __name__ == '__main__':
    # Инициализация базы данных при запуске приложения
    conn = sqlite3.connect('games.db')
    cursor = conn.cursor()

    # Создание таблицы пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    ''')

    # Создание таблицы игр
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT NOT NULL,
            year INTEGER,
            developer TEXT,
            image_url TEXT,
            trailer_url TEXT
        )
    ''')

    conn.commit()
    conn.close()

    app = QApplication(sys.argv)
    auth_window = AuthWindow()
    auth_window.show()
    sys.exit(app.exec())
