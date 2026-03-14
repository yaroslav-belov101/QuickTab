"""
Database migrations for QuickTab
Управление версиями схемы БД
"""

import sqlite3
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

from .db_manager import DatabaseManager


class Migration:
    """Базовый класс миграции"""
    
    def __init__(self, version: int, description: str):
        self.version = version
        self.description = description
    
    def up(self, cursor: sqlite3.Cursor):
        """Применить миграцию"""
        raise NotImplementedError
    
    def down(self, cursor: sqlite3.Cursor):
        """Откатить миграцию"""
        raise NotImplementedError


class MigrationManager:
    """Управление миграциями базы данных"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        self._init_migrations_table()
    
    def _init_migrations_table(self):
        """Создать таблицу для отслеживания миграций"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def get_current_version(self) -> int:
        """Получить текущую версию схемы"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX(version) FROM schema_migrations')
        result = cursor.fetchone()
        return result[0] if result[0] else 0
    
    def is_applied(self, version: int) -> bool:
        """Проверить применена ли миграция"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM schema_migrations WHERE version = ?', (version,))
        return cursor.fetchone() is not None
    
    def apply_migration(self, migration: Migration):
        """Применить одну миграцию"""
        if self.is_applied(migration.version):
            print(f"  Migration {migration.version} already applied")
            return
        
        print(f"  Applying migration {migration.version}: {migration.description}")
        
        with self.db._transaction() as cursor:
            migration.up(cursor)
            cursor.execute('''
                INSERT INTO schema_migrations (version, description)
                VALUES (?, ?)
            ''', (migration.version, migration.description))
        
        print(f"  ✓ Migration {migration.version} applied")
    
    def rollback_migration(self, migration: Migration):
        """Откатить миграцию"""
        if not self.is_applied(migration.version):
            print(f"  Migration {migration.version} not applied")
            return
        
        print(f"  Rolling back migration {migration.version}: {migration.description}")
        
        with self.db._transaction() as cursor:
            migration.down(cursor)
            cursor.execute('''
                DELETE FROM schema_migrations WHERE version = ?
            ''', (migration.version,))
        
        print(f"  ✓ Migration {migration.version} rolled back")
    
    def migrate(self, migrations: List[Migration], target_version: int = None):
        """Применить все миграции до целевой версии"""
        current = self.get_current_version()
        target = target_version or max(m.version for m in migrations)
        
        print(f"Migrating from version {current} to {target}")
        
        for migration in sorted(migrations, key=lambda m: m.version):
            if current < migration.version <= target:
                self.apply_migration(migration)
        
        print("✅ Migrations complete")
    
    def rollback(self, migrations: List[Migration], steps: int = 1):
        """Откатить последние N миграций"""
        applied = self._get_applied_migrations()
        
        print(f"Rolling back {steps} migration(s)")
        
        for migration in sorted(applied, key=lambda m: m.version, reverse=True)[:steps]:
            self.rollback_migration(migration)
        
        print("✅ Rollback complete")
    
    def _get_applied_migrations(self) -> List[Migration]:
        """Получить список примененных миграций"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT version, description FROM schema_migrations ORDER BY version')
        rows = cursor.fetchall()
        
        return [Migration(row[0], row[1]) for row in rows]


# ==================== ПРИМЕРЫ МИГРАЦИЙ ====================

class Migration_001_InitialSchema(Migration):
    """Начальная миграция - создает базовые таблицы"""
    
    def __init__(self):
        super().__init__(1, "Initial schema with search history and favorites")
    
    def up(self, cursor: sqlite3.Cursor):
        # Таблицы создаются автоматически в DatabaseManager
        pass
    
    def down(self, cursor: sqlite3.Cursor):
        cursor.execute("DROP TABLE IF EXISTS search_history")
        cursor.execute("DROP TABLE IF EXISTS favorite_sites")


class Migration_002_AddAIConversations(Migration):
    """Добавление таблицы диалогов с ИИ"""
    
    def __init__(self):
        super().__init__(2, "Add AI conversations table")
    
    def up(self, cursor: sqlite3.Cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_query TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                context TEXT,
                model_used TEXT DEFAULT 'deepseek/deepseek-chat',
                response_time_ms INTEGER DEFAULT 0,
                tokens_used INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_clarification BOOLEAN DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ai_session ON ai_conversations(session_id, created_at DESC)
        ''')
    
    def down(self, cursor: sqlite3.Cursor):
        cursor.execute("DROP TABLE IF EXISTS ai_conversations")


class Migration_003_AddAppStats(Migration):
    """Добавление статистики использования"""
    
    def __init__(self):
        super().__init__(3, "Add app statistics table")
    
    def up(self, cursor: sqlite3.Cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                searches_count INTEGER DEFAULT 0,
                weather_requests INTEGER DEFAULT 0,
                currency_requests INTEGER DEFAULT 0,
                news_requests INTEGER DEFAULT 0,
                ai_requests INTEGER DEFAULT 0,
                app_launches INTEGER DEFAULT 0,
                total_session_time_minutes INTEGER DEFAULT 0
            )
        ''')
    
    def down(self, cursor: sqlite3.Cursor):
        cursor.execute("DROP TABLE IF EXISTS app_stats")


# Список всех миграций
ALL_MIGRATIONS = [
    Migration_001_InitialSchema(),
    Migration_002_AddAIConversations(),
    Migration_003_AddAppStats(),
]


def run_migrations():
    """Запустить все миграции"""
    manager = MigrationManager()
    manager.migrate(ALL_MIGRATIONS)


if __name__ == "__main__":
    run_migrations()