"""
Модуль погоды — получение данных через API (без Selenium)
Использует Open-Meteo API — бесплатный, без ключа, без ограничений
"""

import requests
import json
from typing import Dict, Optional


# API endpoints
GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API = "https://api.open-meteo.com/v1/forecast"


# Расшифровка кодов погоды WMO
WMO_WEATHER_CODES = {
    0: "Ясно",
    1: "Преимущественно ясно",
    2: "Переменная облачность",
    3: "Пасмурно",
    45: "Туман",
    48: "Туман с изморозью",
    51: "Небольшая морось",
    53: "Морось",
    55: "Сильная морось",
    56: "Ледяная морось",
    57: "Сильная ледяная морось",
    61: "Небольшой дождь",
    63: "Дождь",
    65: "Сильный дождь",
    66: "Ледяной дождь",
    67: "Сильный ледяной дождь",
    71: "Небольшой снег",
    73: "Снег",
    75: "Сильный снег",
    77: "Снежные зерна",
    80: "Небольшой ливень",
    81: "Ливень",
    82: "Сильный ливень",
    85: "Снегопад",
    86: "Сильный снегопад",
    95: "Гроза",
    96: "Гроза с градом",
    99: "Гроза с сильным градом",
}


def _decode_weather_code(code: Optional[int]) -> str:
    """Расшифровывает код погоды WMO"""
    if code is None:
        return "Неизвестно"
    return WMO_WEATHER_CODES.get(code, f"Код {code}")


def _clean_city_name(city: str) -> str:
    """Очищает название города для URL"""
    return city.strip().replace(" ", "%20")


def get_weather_data(driver=None, city: str = "Белореченск") -> Dict[str, str]:
    """
    Получает данные о погоде через Open-Meteo API.
    Параметр driver игнорируется (оставлен для совместимости).
    
    Args:
        driver: Не используется (оставлен для совместимости с интерфейсом)
        city: Название города
        
    Returns:
        Словарь с ключами: city, temp, desc, wind, humidity
    """
    print(f"🔍 [API] Ищу город: {city}")
    
    try:
        # Шаг 1: Геокодинг (поиск координат города)
        geo_params = {
            "name": _clean_city_name(city),
            "count": 1,
            "language": "ru",
            "format": "json"
        }
        
        geo_response = requests.get(GEOCODING_API, params=geo_params, timeout=10)
        geo_data = geo_response.json()
        
        if not geo_data.get("results"):
            print(f"❌ Город '{city}' не найден")
            return {
                "city": city,
                "temp": "Город не найден",
                "desc": "Попробуйте другой город",
                "wind": "Н/Д",
                "humidity": "Н/Д"
            }
        
        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        found_city = location.get("name", city)
        country = location.get("country", "")
        
        print(f"   ✅ Найден: {found_city}, {country} ({lat:.2f}, {lon:.2f})")
        
        # Шаг 2: Получение погоды
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "weather_code",
                "wind_speed_10m",
                "pressure_msl"
            ],
            "timezone": "auto",
            "forecast_days": 1
        }
        
        weather_response = requests.get(WEATHER_API, params=weather_params, timeout=10)
        weather_data = weather_response.json()
        
        current = weather_data.get("current", {})
        
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")
        weather_code = current.get("weather_code")
        
        result = {
            "city": found_city,
            "temp": f"{temp}°C" if temp is not None else "Н/Д",
            "desc": _decode_weather_code(weather_code),
            "wind": f"{wind} м/с" if wind is not None else "Н/Д",
            "humidity": f"{humidity}%" if humidity is not None else "Н/Д"
        }
        
        print(f"   ✅ Погода получена: {result['temp']}, {result['desc']}")
        return result
        
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса к API")
        return {
            "city": city,
            "temp": "Таймаут",
            "desc": "Сервер не отвечает",
            "wind": "Н/Д",
            "humidity": "Н/Д"
        }
        
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка соединения")
        return {
            "city": city,
            "temp": "Нет сети",
            "desc": "Проверьте интернет",
            "wind": "Н/Д",
            "humidity": "Н/Д"
        }
        
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return {
            "city": city,
            "temp": "Ошибка",
            "desc": str(e)[:50],
            "wind": "Н/Д",
            "humidity": "Н/Д"
        }


def format_weather_for_display(data: Dict[str, str]) -> str:
    """
    Форматирует погоду для отображения в GUI.
    
    Args:
        data: Результат get_weather_data()
        
    Returns:
        Отформатированная строка
    """
    return (
        f"🌤️ ПОГОДА В {data['city'].upper()}\n"
        f"Температура: {data['temp']}\n"
        f"Погода: {data['desc']}\n"
        f"Влажность: {data.get('humidity', 'Н/Д')}\n"
        f"Ветер: {data.get('wind', 'Н/Д')}\n\n"
    )


def print_weather(weather_data: Dict[str, str], browser_name: str = "API"):
    """
    Выводит погоду в консоль (для отладки/CLI).
    
    Args:
        weather_data: Результат get_weather_data()
        browser_name: Имя источника (для совместимости)
    """
    print("\n" + "═" * 70)
    print(f"🌡️ QUICKTAB | {browser_name} | ПОГОДА")
    print("═" * 70)
    print(f"🌡️ Температура:  {weather_data['temp']}")
    print(f"☁️  Условия:      {weather_data['desc']}")
    print(f"💨 Ветер:        {weather_data['wind']}")
    print(f"💧 Влажность:    {weather_data['humidity']}")
    print("═" * 70)


# Для тестирования напрямую
if __name__ == "__main__":
    print("Тестирование модуля погоды...")
    result = get_weather_data(city="Москва")
    print_weather(result)