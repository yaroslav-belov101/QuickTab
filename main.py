# main.py — точка входа в приложение QuickTab
#!/usr/bin/env python3
"""
QuickTab v0.8.0 — быстрый доступ к информации
Главный файл запуска приложения
"""

import sys
import os

# Добавляем корень проекта в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import QuickTabGUI


def main():
    """Главная функция запуска приложения"""
    print("🚀 Запуск QuickTab v0.8.0...")
    print("=" * 50)
    
    try:
        # Инициализация базы данных
        from database.migration import run_migrations
        run_migrations()
        print("✅ База данных готова")
        
        # Запуск GUI
        app = QuickTabGUI()
        app.mainloop()
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("=" * 50)
    print("✅ QuickTab завершен!")


if __name__ == "__main__":
    main()