#!/usr/bin/env python3
"""
QuickTab — быстрый доступ к информации
Точка входа в приложение
"""

import sys
import os

# Добавляем корень проекта в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import QuickTabGUI


def main():
    """Главная функция запуска приложения"""
    print("🚀 Запуск QuickTab...")
    print("=" * 40)
    
    try:
        app = QuickTabGUI()
        app.mainloop()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
    
    print("=" * 40)
    print("✅ QuickTab завершен!")


if __name__ == "__main__":
    main()