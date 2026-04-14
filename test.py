"""
Тестирование API карты на Railway.
Отправляет запрос с маршрутом и сохраняет результат как PNG.
"""
import sys
sys.stdout.reconfigure(encoding='UTF-8')
import json
import base64
import requests

API_URL = "https://yandexmamp-production.up.railway.app/api/map"

ROUTE_DATA = [
    [
        {"lat": 54.804944, "lon": 83.091643},
        {"lat": 54.805118, "lon": 83.091681},
    ],
    [
        {"lat": 54.805118, "lon": 83.091681},
        {"lat": 54.80508818559745, "lon": 83.09205007426642},
    ],
    [
        {"lat": 54.80508818559745, "lon": 83.09205007426642},
        {"lat": 54.805075741655834, "lon": 83.09220411429783},
    ],
    [
        {"lat": 54.805075741655834, "lon": 83.09220411429783},
        {"lat": 54.804946, "lon": 83.09381},
        {"lat": 54.804895, "lon": 83.094505},
    ],
    [
        {"lat": 54.804895, "lon": 83.094505},
        {"lat": 54.804792, "lon": 83.09463},
        {"lat": 54.80477, "lon": 83.094625},
    ],
]


def test_health():
    """Проверка доступности сервиса."""
    print("=" * 50)
    print("1. Тест /health")
    print("=" * 50)

    url = "https://yandexmamp-production.up.railway.app/health"
    try:
        resp = requests.get(url, timeout=15)
        print(f"   Статус: {resp.status_code}")
        print(f"   Ответ:  {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"   ОШИБКА: {e}")
        return False


def test_map_without_route():
    """Запрос карты без маршрута — только позиция пользователя."""
    print("\n" + "=" * 50)
    print("2. Тест /api/map — без маршрута")
    print("=" * 50)

    payload = {
        "position": {
            "point": {"lon": 83.0925, "lat": 54.805},
            "compass_direction": 45.0,
        },
        "zoom": 17,
        "route": None,
    }

    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
        print(f"   Статус: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            img_b64 = data.get("image_base64", "")
            img_bytes = base64.b64decode(img_b64)

            filename = "map_no_route.png"
            with open(filename, "wb") as f:
                f.write(img_bytes)
            print(f"   Размер изображения: {len(img_bytes)} байт")
            print(f"   Сохранено: {filename}")
            return True
        else:
            print(f"   Ответ: {resp.text[:500]}")
            return False

    except Exception as e:
        print(f"   ОШИБКА: {e}")
        return False


def test_map_with_route():
    """Запрос карты с маршрутом из route_export.json."""
    print("\n" + "=" * 50)
    print("3. Тест /api/map — с маршрутом")
    print("=" * 50)

    # Позиция пользователя — начало маршрута, направление на север
    user_point = ROUTE_DATA[0][0]

    payload = {
        "position": {
            "point": {"lon": user_point["lon"], "lat": user_point["lat"]},
            "compass_direction": 0.0,
        },
        "zoom": 17,
        "route": {
            "segments": [
                [{"lon": p["lon"], "lat": p["lat"]} for p in segment]
                for segment in ROUTE_DATA
            ]
        },
    }

    print(f"   Сегментов маршрута: {len(ROUTE_DATA)}")
    print(f"   Позиция: {user_point}")

    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
        print(f"   Статус: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            img_b64 = data.get("image_base64", "")
            img_bytes = base64.b64decode(img_b64)

            filename = "map_with_route.png"
            with open(filename, "wb") as f:
                f.write(img_bytes)
            print(f"   Размер изображения: {len(img_bytes)} байт")
            print(f"   Сохранено: {filename}")
            return True
        else:
            print(f"   Ответ: {resp.text[:500]}")
            return False

    except Exception as e:
        print(f"   ОШИБКА: {e}")
        return False


def test_map_with_route_from_file():
    """Загрузка маршрута из файла route_export.json."""
    print("\n" + "=" * 50)
    print("4. Тест /api/map — маршрут из файла")
    print("=" * 50)

    filepath = r"C:\Users\Marina\Downloads\route_export.json"

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            route_from_file = json.load(f)
        print(f"   Файл загружен: {len(route_from_file)} сегментов")
    except FileNotFoundError:
        print(f"   Файл не найден: {filepath}")
        print("   Пропускаем этот тест")
        return False
    except json.JSONDecodeError as e:
        print(f"   Ошибка парсинга JSON: {e}")
        return False

    user_point = route_from_file[0][0]

    payload = {
        "position": {
            "point": {"lon": user_point["lon"], "lat": user_point["lat"]},
            "compass_direction": 90.0,
        },
        "zoom": 17,
        "route": {
            "segments": [
                [{"lon": p["lon"], "lat": p["lat"]} for p in segment]
                for segment in route_from_file
            ]
        },
    }

    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
        print(f"   Статус: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            img_b64 = data.get("image_base64", "")
            img_bytes = base64.b64decode(img_b64)

            filename = "map_from_file.png"
            with open(filename, "wb") as f:
                f.write(img_bytes)
            print(f"   Размер изображения: {len(img_bytes)} байт")
            print(f"   Сохранено: {filename}")
            return True
        else:
            print(f"   Ответ: {resp.text[:500]}")
            return False

    except Exception as e:
        print(f"   ОШИБКА: {e}")
        return False


def test_invalid_request():
    """Отправка невалидного запроса — проверка обработки ошибок."""
    print("\n" + "=" * 50)
    print("5. Тест /api/map — невалидный запрос")
    print("=" * 50)

    payload = {"position": "invalid", "zoom": 999}

    try:
        resp = requests.post(API_URL, json=payload, timeout=15)
        print(f"   Статус: {resp.status_code} (ожидался 422)")
        print(f"   Ответ:  {resp.text[:300]}")
        return resp.status_code == 422
    except Exception as e:
        print(f"   ОШИБКА: {e}")
        return False


def main():
    print("🚀 Тестирование API карты")
    print(f"   URL: {API_URL}\n")

    results = {
        "health":         test_health(),
        "без маршрута":   test_map_without_route(),
        "с маршрутом":    test_map_with_route(),
        "из файла":       test_map_with_route_from_file(),
        "невалидный":     test_invalid_request(),
    }

    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ")
    print("=" * 50)

    for name, passed in results.items():
        status = "✅ OK" if passed else "❌ FAIL"
        print(f"   {status}  {name}")

    total = len(results)
    passed = sum(results.values())
    print(f"\n   Итого: {passed}/{total} тестов пройдено")


if __name__ == "__main__":
    main()
