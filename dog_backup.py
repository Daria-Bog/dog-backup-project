# --- Начало программы: Импорты необходимых библиотек ---

import requests  # Это библиотека для выполнения HTTP-запросов (обращения к сайтам, API)
import json  # Это библиотека для работы с форматом JSON (сохранение данных в файл)
import os  # Это модуль для работы с операционной системой (например, для обработки путей файлов)
import logging  # Это мощный модуль для ведения логов (записи информации о работе программы)
from tqdm import tqdm  # Это библиотека для создания красивого прогресс-бара

# --- 1. Настройка логирования (вместо простого print) ---

# Создаем "логгер" - это как журнал, куда мы будем записывать все важные сообщения
# "dog_backup_logger" - это имя нашего журнала
logger = logging.getLogger("dog_backup_logger")
logger.setLevel(
    logging.INFO)  # Устанавливаем уровень логирования: INFO значит, что мы будем видеть информационные сообщения

# Создаем "обработчик" - это то, куда будут выводиться наши сообщения.
# StreamHandler выводит сообщения в консоль (на экран)
handler = logging.StreamHandler()

# Создаем "форматтер" - это шаблон, по которому будут выглядеть наши сообщения в логе
# %(levelname)s - уровень сообщения (INFO, WARNING, ERROR и т.д.)
# %(message)s - само сообщение
formatter = logging.Formatter('%(levelname)s: %(message)s')

# Прикрепляем форматтер к обработчику
handler.setFormatter(formatter)
# Прикрепляем обработчик к логгеру
logger.addHandler(handler)


# Теперь вместо print() мы будем использовать logger.info(), logger.warning(), logger.error()

# --- 2. Класс для работы с Яндекс.Диском (YandexDiskUploader) ---

class YandexDiskUploader:
    # Инициализация объекта. Срабатывает, когда мы создаем YandexDiskUploader(токен)
    def __init__(self, token):
        self.token = token
        self.base_url = "https://cloud-api.yandex.net/v1/disk/resources"  # Базовый URL для API Яндекс.Диска
        self.headers = {  # Заголовки HTTP-запроса, содержащие токен для авторизации
            "Content-Type": "application/json",
            "Authorization": f"OAuth {self.token}"  # f-строка для удобного форматирования токена
        }
        logger.info("YandexDiskUploader: Инициализация завершена.")

    def create_folder(self, folder_name):
        # Функция для создания папки на Яндекс.Диске
        logger.info(f"YandexDiskUploader: Попытка создать папку '{folder_name}' на Яндекс.Диске...")
        path = folder_name  # Путь к папке на Диске (просто имя папки)
        params = {"path": path}  # Параметры запроса: указываем путь

        try:
            # Отправляем PUT-запрос для создания ресурса (папки)
            response = requests.put(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()  # Проверяем статус ответа: если это ошибка (4xx или 5xx), генерируем исключение

            if response.status_code == 201:  # 201 Created - папка успешно создана
                logger.info(f"YandexDiskUploader: Папка '{folder_name}' успешно создана.")
                return True
            elif response.status_code == 409:  # 409 Conflict - папка уже существует
                logger.info(f"YandexDiskUploader: Папка '{folder_name}' уже существует.")
                return True
            else:  # На всякий случай, если будет другой успешный статус
                logger.warning(
                    f"YandexDiskUploader: Неожиданный успешный статус {response.status_code} при создании папки '{folder_name}'.")
                return True
        except requests.exceptions.RequestException as e:  # Ловим все сетевые ошибки
            logger.error(f"YandexDiskUploader: Сетевая ошибка при создании папки '{folder_name}': {e}")
            return False
        except Exception as e:  # Ловим любые другие неожиданные ошибки
            logger.error(f"YandexDiskUploader: Неизвестная ошибка при создании папки '{folder_name}': {e}")
            return False

    def upload_file_from_url(self, folder_name, file_name, file_url):
        # Функция для загрузки файла на Яндекс.Диск по URL
        logger.info(f"YandexDiskUploader: Загрузка файла '{file_name}' из URL: {file_url} в папку '{folder_name}'...")
        path = f"{folder_name}/{file_name}"  # Полный путь к файлу на Диске (папка/имя_файла)
        params = {"path": path, "url": file_url}  # Параметры: куда загрузить и откуда взять URL

        try:
            # Сначала получаем ссылку для загрузки (Яндекс.Диск должен получить URL и начать загрузку)
            # Это синхронный метод, который сразу возвращает 202 Accepted, если запрос принят
            upload_link_response = requests.post(f"{self.base_url}/upload", headers=self.headers, params=params)
            upload_link_response.raise_for_status()  # Проверяем статус ответа

            if upload_link_response.status_code == 202:  # 202 Accepted - запрос на загрузку принят
                logger.info(f"YandexDiskUploader: Запрос на загрузку файла '{file_name}' успешно принят Яндекс.Диском.")
                # В данном случае, Яндекс.Диск сам выполняет загрузку "по воздуху",
                # нам не нужно проверять статус асинхронной операции.
                return True
            else:
                logger.warning(
                    f"YandexDiskUploader: Неожиданный успешный статус {upload_link_response.status_code} при загрузке файла '{file_name}'.")
                return False
        except requests.exceptions.RequestException as e:  # Ловим все сетевые ошибки
            logger.error(f"YandexDiskUploader: Сетевая ошибка при загрузке файла '{file_name}': {e}")
            return False
        except Exception as e:  # Ловим любые другие неожиданные ошибки
            logger.error(f"YandexDiskUploader: Неизвестная ошибка при загрузке файла '{file_name}': {e}")
            return False


# --- 3. Функции для работы с Dog API ---

def get_dog_breeds():
    # Функция для получения полного списка пород собак с Dog API
    logger.info("Dog API: Получение списка всех пород...")
    try:
        response = requests.get("https://dog.ceo/api/breeds/list/all")
        response.raise_for_status()  # Проверяем статус ответа

        if response.status_code == 200:  # 200 OK - запрос успешен
            logger.info("Dog API: Список пород успешно получен.")
            return response.json().get("message", {})  # Возвращаем словарь пород
        else:
            logger.warning(f"Dog API: Неожиданный успешный статус {response.status_code} при получении списка пород.")
            return {}
    except requests.exceptions.RequestException as e:  # Ловим все сетевые ошибки
        logger.error(f"Dog API: Сетевая ошибка при получении списка пород: {e}")
        return {}
    except Exception as e:  # Ловим любые другие неожиданные ошибки
        logger.error(f"Dog API: Неизвестная ошибка при получении списка пород: {e}")
        return {}


def get_random_image(breed, sub_breed=None):
    # Функция для получения случайной картинки для породы или под-породы
    if sub_breed:
        url = f"https://dog.ceo/api/breed/{breed}/{sub_breed}/images/random"
        logger.info(f"Dog API: Запрос случайной картинки для под-породы '{breed}/{sub_breed}'...")
    else:
        url = f"https://dog.ceo/api/breed/{breed}/images/random"
        logger.info(f"Dog API: Запрос случайной картинки для породы '{breed}'...")

    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверяем статус ответа

        if response.status_code == 200:  # 200 OK - запрос успешен
            image_url = response.json().get("message")
            logger.info(f"Dog API: Получен URL картинки: {image_url}")
            return image_url
        else:
            logger.warning(
                f"Dog API: Неожиданный успешный статус {response.status_code} при получении картинки для {breed}{'/' + sub_breed if sub_breed else ''}.")
            return None
    except requests.exceptions.RequestException as e:  # Ловим все сетевые ошибки
        logger.error(
            f"Dog API: Сетевая ошибка при получении картинки для {breed}{'/' + str(sub_breed) if sub_breed else ''}: {e}")
        return None
    except Exception as e:  # Ловим любые другие неожиданные ошибки
        logger.error(
            f"Dog API: Неизвестная ошибка при получении картинки для {breed}{'/' + str(sub_breed) if sub_breed else ''}: {e}")
        return None


# --- 4. Основная логика программы (main функция) ---

def main():
    logger.info("--- Привет! Это программа для резервного копирования фотографий собак на Яндекс.Диск. ---")
    logger.info("---")

    # --- 4.1. Получение и проверка ввода пользователя ---

    # Получаем название породы от пользователя
    breed_name = ""
    all_breeds = get_dog_breeds()  # Получаем список пород в начале
    if not all_breeds:  # Если не удалось получить породы, значит проблемы с API
        logger.error(
            "Не удалось получить список пород с Dog API. Проверьте подключение к интернету или доступность сервиса.")
        return  # Выходим из программы

    while True:
        breed_name_input = input("Введите название породы собаки (например, spaniel, poodle): ").lower().strip()
        if breed_name_input in all_breeds:
            breed_name = breed_name_input
            logger.info(f"Порода '{breed_name}' найдена в списке.")
            break
        else:
            logger.warning(f"Порода '{breed_name_input}' не найдена. Пожалуйста, попробуйте еще раз.")
            logger.info("Примеры пород: labrador, pug, husky, corgi, bulldog.")
            logger.info(
                "Полный список можно посмотреть здесь: https://dog.ceo/dog-api/documentation/ (раздел 'All Breeds list')")

    # Получаем токен Яндекс.Диска от пользователя
    # Добавляем .strip() для консистентности, как рекомендовал преподаватель
    yandex_token = input("Введите ваш токен Яндекс.Диска: ").strip()

    # --- 4.2. Инициализация загрузчика Яндекс.Диска ---

    uploader = YandexDiskUploader(yandex_token)

    # Список для хранения информации о загруженных файлах
    uploaded_files_info = []

    # --- 4.3. Создание папки на Яндекс.Диске ---

    if not uploader.create_folder(breed_name):
        logger.error("Не удалось создать папку на Яндекс.Диске. Программа завершает работу.")
        return  # Выходим, если не можем создать папку

    # --- 4.4. Обработка пород и загрузка картинок ---

    # Проверяем, есть ли под-породы у выбранной породы
    sub_breeds = all_breeds.get(breed_name)  # all_breeds уже содержит актуальные под-породы

    if sub_breeds:  # Если есть под-породы
        logger.info(
            f"У породы '{breed_name}' есть под-породы: {', '.join(sub_breeds)}. Загружаем по одной картинке для каждой под-породы.")
        # Используем tqdm для прогресс-бара, чтобы видеть ход загрузки под-пород
        for sub_breed in tqdm(sub_breeds, desc=f"Загрузка {breed_name} под-пород"):
            image_url = get_random_image(breed_name, sub_breed)
            if image_url:  # Если URL картинки успешно получен
                # Извлекаем имя файла из URL (например, '02102973_603.jpg' из полного URL)
                file_original_name = os.path.basename(image_url)
                # Формируем новое имя файла: порода_подпорода_имяфайла.jpg
                file_name = f"{breed_name}_{sub_breed}_{file_original_name}"

                # Загружаем файл на Яндекс.Диск
                if uploader.upload_file_from_url(breed_name, file_name, image_url):
                    uploaded_files_info.append({"file_name": file_name})  # Добавляем информацию в список
    else:  # Если под-пород нет, просто загружаем одну картинку для основной породы
        logger.info(f"У породы '{breed_name}' нет под-пород. Загружаем одну случайную картинку.")
        # Прогресс-бар на 1 итерацию для консистентности
        for _ in tqdm(range(1), desc=f"Загрузка {breed_name}"):
            image_url = get_random_image(breed_name)
            if image_url:  # Если URL картинки успешно получен
                file_original_name = os.path.basename(image_url)
                file_name = f"{breed_name}_{file_original_name}"

                if uploader.upload_file_from_url(breed_name, file_name, image_url):
                    uploaded_files_info.append({"file_name": file_name})

    # --- 4.5. Сохранение информации в JSON-файл ---

    json_file_name = "uploaded_dog_images.json"
    try:
        # Открываем файл в режиме записи ('w' - write) с кодировкой UTF-8 для поддержки русских символов
        with open(json_file_name, "w", encoding="utf-8") as f:
            # Сохраняем список uploaded_files_info в JSON-файл
            # indent=2 делает JSON-файл красивым и читаемым (с отступами)
            # ensure_ascii=False позволяет сохранять русские буквы напрямую, без преобразования в \u....
            json.dump(uploaded_files_info, f, indent=2, ensure_ascii=False)
        logger.info(f"Информация о загруженных файлах успешно сохранена в '{json_file_name}'.")
    except IOError as e:
        logger.error(f"Ошибка записи JSON-файла '{json_file_name}': {e}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка при сохранении JSON-файла: {e}")

    logger.info(f"\n--- Работа завершена! ---")
    logger.info(f"Картинки загружены в папку '{breed_name}' на вашем Яндекс.Диске.")


# --- 5. Запуск основной функции ---

# Это стандартный Python-код, который говорит:
# "Если этот скрипт запускается напрямую (не импортируется как модуль в другой программе),
# то вызови функцию main()"
if __name__ == "__main__":
    main()