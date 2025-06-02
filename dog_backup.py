import requests
import json
import os
from tqdm import tqdm  # Импортируем tqdm для прогресс-бара


# --- 1. Основные настройки и функции для работы с Яндекс.Диском ---

class YandexDiskUploader:
    def __init__(self, token):
        # Инициализируем наш загрузчик с токеном Яндекса
        self.token = token
        self.base_url = "https://cloud-api.yandex.net/v1/disk/resources"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"OAuth {self.token}"
        }

    def create_folder(self, folder_name):
        # Функция для создания папки на Яндекс.Диске
        # path - это путь к папке на Диске
        path = folder_name
        params = {"path": path}
        response = requests.put(self.base_url, headers=self.headers, params=params)

        if response.status_code == 201:
            print(f"Папка '{folder_name}' успешно создана на Яндекс.Диске.")
            return True
        elif response.status_code == 409:
            print(f"Папка '{folder_name}' уже существует на Яндекс.Диске.")
            return True
        else:
            print(
                f"Ошибка при создании папки '{folder_name}': {response.status_code} - {response.json().get('message', 'Неизвестная ошибка')}")
            return False

    def upload_file_from_url(self, folder_name, file_name, file_url):
        # Функция для загрузки файла на Яндекс.Диск по URL
        # from - это URL картинки, которую мы хотим загрузить
        # path - это полный путь к файлу на Диске (папка/имя_файла)
        path = f"{folder_name}/{file_name}"
        params = {"path": path, "url": file_url}

        # Сначала получаем ссылку для загрузки
        upload_link_response = requests.post(f"{self.base_url}/upload", headers=self.headers, params=params)

        if upload_link_response.status_code == 202:
            print(f"Файл '{file_name}' успешно загружен на Яндекс.Диск.")
            return True
        else:
            print(
                f"Ошибка при загрузке файла '{file_name}': {upload_link_response.status_code} - {upload_link_response.json().get('message', 'Неизвестная ошибка')}")
            return False


# --- 2. Функции для работы с Dog API ---

def get_dog_breeds():
    # Получаем полный список пород собак
    response = requests.get("https://dog.ceo/api/breeds/list/all")
    if response.status_code == 200:
        return response.json().get("message", {})
    else:
        print(f"Ошибка при получении списка пород: {response.status_code}")
        return {}


def get_random_image(breed, sub_breed=None):
    # Получаем случайную картинку для породы или под-породы
    if sub_breed:
        url = f"https://dog.ceo/api/breed/{breed}/{sub_breed}/images/random"
    else:
        url = f"https://dog.ceo/api/breed/{breed}/images/random"

    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("message")
    else:
        # Если картинка не найдена, выводим сообщение об ошибке
        print(
            f"Ошибка при получении картинки для {breed}{'/' + sub_breed if sub_breed else ''}: {response.status_code}")
        return None


# --- 3. Основная логика программы ---

def main():
    print("Привет! Это программа для резервного копирования фотографий собак на Яндекс.Диск.")
    print("---")

    # Получаем название породы от пользователя
    while True:
        breed_name = input("Введите название породы собаки (например, spaniel, poodle): ").lower().strip()
        all_breeds = get_dog_breeds()
        if breed_name in all_breeds:
            print(f"Порода '{breed_name}' найдена.")
            break
        else:
            print(f"Порода '{breed_name}' не найдена. Пожалуйста, попробуйте еще раз.")
            print("Примеры пород: labrador, pug, husky, corgi, bulldog.")
            print(
                "Полный список можно посмотреть здесь: https://dog.ceo/dog-api/documentation/ (раздел 'All Breeds list')")

    # Получаем токен Яндекс.Диска от пользователя
    yandex_token = input("Введите ваш токен Яндекс.Диска: ").strip()

    # Создаем объект для работы с Яндекс.Диском
    uploader = YandexDiskUploader(yandex_token)

    # Список для хранения информации о загруженных файлах
    uploaded_files_info = []

    # Создаем папку для породы на Яндекс.Диске
    if not uploader.create_folder(breed_name):
        print("Не удалось создать папку на Яндекс.Диске. Программа завершает работу.")
        return  # Выходим, если не можем создать папку

    # Проверяем, есть ли под-породы
    sub_breeds = get_dog_breeds().get(breed_name)

    if sub_breeds:  # Если есть под-породы
        print(
            f"У породы '{breed_name}' есть под-породы: {', '.join(sub_breeds)}. Загружаем по одной картинке для каждой под-породы.")
        # Создаем прогресс-бар для под-пород
        for sub_breed in tqdm(sub_breeds, desc=f"Загрузка {breed_name} под-пород"):
            image_url = get_random_image(breed_name, sub_breed)
            if image_url:
                # Извлекаем имя файла из URL
                file_original_name = os.path.basename(image_url)
                # Формируем новое имя файла
                file_name = f"{breed_name}_{sub_breed}_{file_original_name}"

                if uploader.upload_file_from_url(breed_name, file_name, image_url):
                    uploaded_files_info.append({"file_name": file_name})
    else:  # Если под-пород нет, просто загружаем картинку для основной породы
        print(f"У породы '{breed_name}' нет под-пород. Загружаем одну случайную картинку.")
        # Создаем прогресс-бар для одной картинки
        for _ in tqdm(range(1), desc=f"Загрузка {breed_name}"):  # Прогресс-бар на 1 итерацию
            image_url = get_random_image(breed_name)
            if image_url:
                file_original_name = os.path.basename(image_url)
                file_name = f"{breed_name}_{file_original_name}"

                if uploader.upload_file_from_url(breed_name, file_name, image_url):
                    uploaded_files_info.append({"file_name": file_name})

    # Сохраняем информацию о загруженных файлах в JSON
    json_file_name = "uploaded_dog_images.json"
    with open(json_file_name, "w", encoding="utf-8") as f:
        json.dump(uploaded_files_info, f, indent=2, ensure_ascii=False)  # indent=2 делает файл красивее

    print(f"\nРабота завершена!")
    print(f"Информация о загруженных файлах сохранена в '{json_file_name}'.")
    print(f"Картинки загружены в папку '{breed_name}' на вашем Яндекс.Диске.")


# Это запускает нашу главную функцию, когда скрипт выполняется
if __name__ == "__main__":
    main()