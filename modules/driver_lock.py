import threading

# Глобальная блокировка для доступа к единому WebDriver
lock = threading.Lock()