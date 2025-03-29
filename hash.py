import bcrypt


# Хеширование пароля с использованием bcrypt
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


# Проверка соответствия пароля его хешу
def check_password(hashed, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)


# Проверка сложности пароля по критериям
def correct_password(passwd):
    # Проверка длины пароля
    if len(passwd) <= 8:
        return False

    # Проверка наличия букв разного регистра
    upper = any(a.isupper() for a in passwd)  # Есть хотя бы одна заглавная
    lower = any(a.islower() for a in passwd)  # Есть хотя бы одна строчная
    if not (upper and lower):
        return False

    # Проверка наличия цифр
    if not any(a.isdigit() for a in passwd):
        return False

    return True
