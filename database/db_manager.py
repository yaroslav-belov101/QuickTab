"""
Database Manager for QuickTab
SQLite with connection pooling and async support
"""

import sqlite3
import json
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Callable
from contextlib import contextmanager
import time

from .models import (
    SearchHistory, FavoriteSite, UserSettings, CacheEntry,
    NewsArticle, WeatherCache, CurrencyCache, AIConversation, AppStats
)


class DatabaseManager:
    """
    Управление SQLite базой данных QuickTab
    Потокобезопасный синглтон с пулом соединений
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: Optional[str] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: Optional[str] = None):
        if self._initialized:
            return
            
        self.db_path = db_path or self._get_default_db_path()
        self._local = threading.local()
        self._init_database()
        self._initialized = True
        print(f"✅ Database initialized: {self.db_path}")
    
    def _get_default_db_path(self) -> str:
        """Получить путь к БД в домашней директории пользователя"""
        home = Path.home()
        db_dir = home / ".quicktab" / "data"
        db_dir.mkdir(parents=True, exist_ok=True)
        return str(db_dir / "quicktab.db")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Получить соединение с БД (потокобезопасно)"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None,  # Autocommit mode for better performance
                timeout=20.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
        return self._local.connection
    
    @contextmanager
    def _transaction(self):
        """Контекстный менеджер для транзакций"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN")
            yield cursor
            cursor.execute("COMMIT")
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e
    
    def _init_database(self):
        """Инициализация схемы базы данных"""
        with self._transaction() as cursor:
            # Таблица истории поиска
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    query_type TEXT DEFAULT 'general',
                    result_summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    click_count INTEGER DEFAULT 0,
                    is_favorite BOOLEAN DEFAULT 0
                )
            ''')
            
            # Индекс для быстрого поиска
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_search_query ON search_history(query)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_search_date ON search_history(created_at DESC)
            ''')
            
            # Таблица избранных сайтов (замена JSON-файлу)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorite_sites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    icon TEXT,
                    category TEXT DEFAULT 'other',
                    color TEXT DEFAULT '#FECA57',
                    position INTEGER DEFAULT 0,
                    click_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP
                )
            ''')
            
            # Таблица настроек пользователя
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    theme TEXT DEFAULT 'Тёмная',
                    color_scheme TEXT DEFAULT 'Синяя',
                    font_scale REAL DEFAULT 1.0,
                    default_city TEXT DEFAULT 'Белореченск',
                    auto_update_interval INTEGER DEFAULT 5,
                    cache_enabled BOOLEAN DEFAULT 1,
                    animations_enabled BOOLEAN DEFAULT 1,
                    headless_mode BOOLEAN DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Вставка дефолтных настроек если их нет
            cursor.execute('''
                INSERT OR IGNORE INTO user_settings (id) VALUES (1)
            ''')
            
            # Универсальный кэш
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    cache_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_entries(cache_key)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at)
            ''')
            
            # Кэш новостей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT,
                    url TEXT NOT NULL,
                    source TEXT,
                    published_at TIMESTAMP,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_news_topic ON news_articles(topic, fetched_at DESC)
            ''')
            
            # Кэш погоды
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weather_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT UNIQUE NOT NULL,
                    temperature TEXT,
                    description TEXT,
                    wind TEXT,
                    humidity TEXT,
                    weather_code INTEGER,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            ''')
            
            # Кэш валют
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS currency_cache (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    usd_rate TEXT,
                    eur_rate TEXT,
                    btc_rate TEXT,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            ''')
            
            # История диалогов с ИИ
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
            
            # Статистика использования
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
            
            # Триггер для автоматической очистки старого кэша
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS cleanup_old_cache
                AFTER INSERT ON cache_entries
                BEGIN
                    DELETE FROM cache_entries WHERE expires_at < datetime('now', '-7 days');
                END
            ''')
    
    # ==================== SEARCH HISTORY ====================
    
    def add_search_history(self, query: str, query_type: str = "general", 
                          result_summary: str = "") -> SearchHistory:
        """Добавить запись в историю поиска"""
        with self._transaction() as cursor:
            cursor.execute('''
                INSERT INTO search_history (query, query_type, result_summary)
                VALUES (?, ?, ?)
            ''', (query, query_type, result_summary))
            
            history_id = cursor.lastrowid
            
            # Обновляем статистику
            self._increment_stat(cursor, 'searches_count')
            
            return self.get_search_history_by_id(history_id)
    
    def get_search_history_by_id(self, history_id: int) -> Optional[SearchHistory]:
        """Получить запись истории по ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM search_history WHERE id = ?
        ''', (history_id,))
        
        row = cursor.fetchone()
        if row:
            return self._row_to_search_history(row)
        return None
    
    def get_search_history(self, limit: int = 50, 
                          query_type: Optional[str] = None) -> List[SearchHistory]:
        """Получить историю поиска"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if query_type:
            cursor.execute('''
                SELECT * FROM search_history 
                WHERE query_type = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (query_type, limit))
        else:
            cursor.execute('''
                SELECT * FROM search_history 
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
        
        return [self._row_to_search_history(row) for row in cursor.fetchall()]
    
    def search_history_search(self, search_term: str, limit: int = 20) -> List[SearchHistory]:
        """Поиск по истории"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM search_history 
            WHERE query LIKE ? OR result_summary LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (f'%{search_term}%', f'%{search_term}%', limit))
        
        return [self._row_to_search_history(row) for row in cursor.fetchall()]
    
    def increment_search_click(self, history_id: int):
        """Увеличить счетчик кликов"""
        with self._transaction() as cursor:
            cursor.execute('''
                UPDATE search_history 
                SET click_count = click_count + 1
                WHERE id = ?
            ''', (history_id,))
    
    def toggle_search_favorite(self, history_id: int) -> bool:
        """Переключить статус избранного"""
        with self._transaction() as cursor:
            cursor.execute('''
                UPDATE search_history 
                SET is_favorite = NOT is_favorite
                WHERE id = ?
            ''', (history_id,))
            
            cursor.execute('SELECT is_favorite FROM search_history WHERE id = ?', (history_id,))
            row = cursor.fetchone()
            return bool(row[0]) if row else False
    
    def clear_search_history(self, keep_favorites: bool = True):
        """Очистить историю поиска"""
        with self._transaction() as cursor:
            if keep_favorites:
                cursor.execute('''
                    DELETE FROM search_history 
                    WHERE is_favorite = 0
                ''')
            else:
                cursor.execute('DELETE FROM search_history')
    
    def _row_to_search_history(self, row: sqlite3.Row) -> SearchHistory:
        """Конвертировать строку БД в объект"""
        return SearchHistory(
            id=row['id'],
            query=row['query'],
            query_type=row['query_type'],
            result_summary=row['result_summary'],
            created_at=datetime.fromisoformat(row['created_at']),
            click_count=row['click_count'],
            is_favorite=bool(row['is_favorite'])
        )
    
    # ==================== FAVORITE SITES ====================
    
    def add_favorite_site(self, site: FavoriteSite) -> FavoriteSite:
        """Добавить сайт в избранное"""
        with self._transaction() as cursor:
            cursor.execute('''
                INSERT INTO favorite_sites 
                (title, url, icon, category, color, position)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (site.title, site.url, site.icon, site.category, 
                  site.color, site.position))
            
            site.id = cursor.lastrowid
            return site
    
    def get_favorite_sites(self, category: Optional[str] = None) -> List[FavoriteSite]:
        """Получить избранные сайты"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT * FROM favorite_sites 
                WHERE category = ?
                ORDER BY position, created_at
            ''', (category,))
        else:
            cursor.execute('''
                SELECT * FROM favorite_sites 
                ORDER BY position, created_at
            ''')
        
        return [self._row_to_favorite_site(row) for row in cursor.fetchall()]
    
    def update_favorite_site(self, site: FavoriteSite) -> bool:
        """Обновить сайт в избранном"""
        if site.id is None:
            return False
            
        with self._transaction() as cursor:
            cursor.execute('''
                UPDATE favorite_sites 
                SET title = ?, url = ?, icon = ?, category = ?, 
                    color = ?, position = ?, click_count = ?
                WHERE id = ?
            ''', (site.title, site.url, site.icon, site.category,
                  site.color, site.position, site.click_count, site.id))
            
            return cursor.rowcount > 0
    
    def delete_favorite_site(self, site_id: int) -> bool:
        """Удалить сайт из избранного"""
        with self._transaction() as cursor:
            cursor.execute('DELETE FROM favorite_sites WHERE id = ?', (site_id,))
            return cursor.rowcount > 0
    
    def record_favorite_access(self, site_id: int):
        """Записать доступ к избранному сайту"""
        with self._transaction() as cursor:
            cursor.execute('''
                UPDATE favorite_sites 
                SET click_count = click_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (site_id,))
    
    def import_favorites_from_json(self, favorites_data: List[Dict]):
        """Импорт избранного из JSON (миграция со старого формата)"""
        with self._transaction() as cursor:
            for i, data in enumerate(favorites_data):
                cursor.execute('''
                    INSERT OR REPLACE INTO favorite_sites 
                    (title, url, icon, category, color, position)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('title', ''),
                    data.get('url', ''),
                    data.get('icon', ''),
                    data.get('category', 'other'),
                    data.get('color', '#FECA57'),
                    i
                ))
    
    def export_favorites_to_json(self) -> List[Dict]:
        """Экспорт избранного в JSON"""
        sites = self.get_favorite_sites()
        return [site.to_dict() for site in sites]
    
    def _row_to_favorite_site(self, row: sqlite3.Row) -> FavoriteSite:
        return FavoriteSite(
            id=row['id'],
            title=row['title'],
            url=row['url'],
            icon=row['icon'],
            category=row['category'],
            color=row['color'],
            position=row['position'],
            click_count=row['click_count'],
            created_at=datetime.fromisoformat(row['created_at']),
            last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None
        )
    
    # ==================== USER SETTINGS ====================
    
    def get_user_settings(self) -> UserSettings:
        """Получить настройки пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_settings WHERE id = 1')
        row = cursor.fetchone()
        
        if row:
            return self._row_to_user_settings(row)
        return UserSettings()  # Default settings
    
    def update_user_settings(self, settings: UserSettings) -> bool:
        """Обновить настройки"""
        with self._transaction() as cursor:
            cursor.execute('''
                UPDATE user_settings 
                SET theme = ?, color_scheme = ?, font_scale = ?,
                    default_city = ?, auto_update_interval = ?,
                    cache_enabled = ?, animations_enabled = ?, headless_mode = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            ''', (
                settings.theme, settings.color_scheme, settings.font_scale,
                settings.default_city, settings.auto_update_interval,
                settings.cache_enabled, settings.animations_enabled, settings.headless_mode
            ))
            return cursor.rowcount > 0
    
    def _row_to_user_settings(self, row: sqlite3.Row) -> UserSettings:
        return UserSettings(
            id=row['id'],
            theme=row['theme'],
            color_scheme=row['color_scheme'],
            font_scale=row['font_scale'],
            default_city=row['default_city'],
            auto_update_interval=row['auto_update_interval'],
            cache_enabled=bool(row['cache_enabled']),
            animations_enabled=bool(row['animations_enabled']),
            headless_mode=bool(row['headless_mode']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
    
    # ==================== CACHE ====================
    
    def get_cache(self, cache_key: str, cache_type: str) -> Optional[CacheEntry]:
        """Получить данные из кэша если не истекли"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM cache_entries 
            WHERE cache_key = ? AND cache_type = ? AND expires_at > datetime('now')
        ''', (cache_key, cache_type))
        
        row = cursor.fetchone()
        if row:
            # Увеличиваем счетчик доступов
            with self._transaction() as tx_cursor:
                tx_cursor.execute('''
                    UPDATE cache_entries SET access_count = access_count + 1 WHERE id = ?
                ''', (row['id'],))
            
            return self._row_to_cache_entry(row)
        return None
    
    def set_cache(self, cache_key: str, cache_type: str, 
                  data: Dict[str, Any], ttl_seconds: int = 300) -> CacheEntry:
        """Сохранить данные в кэш"""
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        entry = CacheEntry(
            cache_key=cache_key,
            cache_type=cache_type,
            expires_at=expires_at
        )
        entry.set_data_dict(data)
        
        with self._transaction() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries 
                (cache_key, cache_type, data, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (entry.cache_key, entry.cache_type, entry.data, entry.expires_at))
            
            entry.id = cursor.lastrowid
        
        return entry
    
    def clear_expired_cache(self):
        """Очистить истекший кэш"""
        with self._transaction() as cursor:
            cursor.execute('''
                DELETE FROM cache_entries WHERE expires_at < datetime('now')
            ''')
            return cursor.rowcount
    
    def clear_cache_by_type(self, cache_type: str):
        """Очистить кэш по типу"""
        with self._transaction() as cursor:
            cursor.execute('''
                DELETE FROM cache_entries WHERE cache_type = ?
            ''', (cache_type,))
    
    def _row_to_cache_entry(self, row: sqlite3.Row) -> CacheEntry:
        entry = CacheEntry(
            id=row['id'],
            cache_key=row['cache_key'],
            cache_type=row['cache_type'],
            data=row['data'],
            expires_at=datetime.fromisoformat(row['expires_at']),
            created_at=datetime.fromisoformat(row['created_at']),
            access_count=row['access_count']
        )
        return entry
    
    # ==================== WEATHER CACHE ====================
    
    def get_weather_cache(self, city: str) -> Optional[WeatherCache]:
        """Получить кэш погоды для города"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM weather_cache 
            WHERE city = ? AND expires_at > datetime('now')
        ''', (city,))
        
        row = cursor.fetchone()
        if row:
            return self._row_to_weather_cache(row)
        return None
    
    def set_weather_cache(self, city: str, temp: str, desc: str, 
                          wind: str, humidity: str, 
                          weather_code: Optional[int] = None,
                          ttl_minutes: int = 30) -> WeatherCache:
        """Сохранить погоду в кэш"""
        expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
        
        with self._transaction() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO weather_cache 
                (city, temperature, description, wind, humidity, weather_code, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (city, temp, desc, wind, humidity, weather_code, expires_at))
            
            cache_id = cursor.lastrowid
        
        return self.get_weather_cache(city)
    
    def _row_to_weather_cache(self, row: sqlite3.Row) -> WeatherCache:
        return WeatherCache(
            id=row['id'],
            city=row['city'],
            temperature=row['temperature'],
            description=row['description'],
            wind=row['wind'],
            humidity=row['humidity'],
            weather_code=row['weather_code'],
            fetched_at=datetime.fromisoformat(row['fetched_at']),
            expires_at=datetime.fromisoformat(row['expires_at'])
        )
    
    # ==================== CURRENCY CACHE ====================
    
    def get_currency_cache(self) -> Optional[CurrencyCache]:
        """Получить кэш валют"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM currency_cache 
            WHERE id = 1 AND expires_at > datetime('now')
        ''')
        
        row = cursor.fetchone()
        if row:
            return self._row_to_currency_cache(row)
        return None
    
    def set_currency_cache(self, usd: str, eur: str, btc: str,
                           ttl_minutes: int = 60) -> CurrencyCache:
        """Сохранить курсы валют"""
        expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
        
        with self._transaction() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO currency_cache 
                (id, usd_rate, eur_rate, btc_rate, expires_at)
                VALUES (1, ?, ?, ?, ?)
            ''', (usd, eur, btc, expires_at))
        
        return self.get_currency_cache()
    
    def _row_to_currency_cache(self, row: sqlite3.Row) -> CurrencyCache:
        return CurrencyCache(
            id=row['id'],
            usd_rate=row['usd_rate'],
            eur_rate=row['eur_rate'],
            btc_rate=row['btc_rate'],
            fetched_at=datetime.fromisoformat(row['fetched_at']),
            expires_at=datetime.fromisoformat(row['expires_at'])
        )
    
    # ==================== NEWS CACHE ====================
    
    def save_news_articles(self, topic: str, articles: List[Dict[str, str]]):
        """Сохранить новости в кэш"""
        with self._transaction() as cursor:
            # Удаляем старые новости по этой теме
            cursor.execute('''
                DELETE FROM news_articles WHERE topic = ?
            ''', (topic,))
            
            # Вставляем новые
            for article in articles:
                cursor.execute('''
                    INSERT INTO news_articles 
                    (topic, title, summary, url, source, published_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    topic,
                    article.get('title', ''),
                    article.get('summary', ''),
                    article.get('url', ''),
                    article.get('source', ''),
                    article.get('published_at')
                ))
    
    def get_news_articles(self, topic: str, limit: int = 10) -> List[NewsArticle]:
        """Получить новости по теме"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM news_articles 
            WHERE topic = ?
            ORDER BY fetched_at DESC, published_at DESC
            LIMIT ?
        ''', (topic, limit))
        
        return [self._row_to_news_article(row) for row in cursor.fetchall()]
    
    def mark_news_read(self, article_id: int):
        """Отметить новость как прочитанную"""
        with self._transaction() as cursor:
            cursor.execute('''
                UPDATE news_articles SET is_read = 1 WHERE id = ?
            ''', (article_id,))
    
    def _row_to_news_article(self, row: sqlite3.Row) -> NewsArticle:
        published = row['published_at']
        return NewsArticle(
            id=row['id'],
            topic=row['topic'],
            title=row['title'],
            summary=row['summary'],
            url=row['url'],
            source=row['source'],
            published_at=datetime.fromisoformat(published) if published else None,
            fetched_at=datetime.fromisoformat(row['fetched_at']),
            is_read=bool(row['is_read'])
        )
    
    # ==================== AI CONVERSATIONS ====================
    
    def start_ai_session(self) -> str:
        """Создать новую сессию диалога с ИИ"""
        return str(uuid.uuid4())
    
    def save_ai_conversation(self, session_id: str, query: str, response: str,
                            context: str = "", model: str = "deepseek/deepseek-chat",
                            response_time_ms: int = 0, 
                            is_clarification: bool = False) -> AIConversation:
        """Сохранить диалог с ИИ"""
        with self._transaction() as cursor:
            cursor.execute('''
                INSERT INTO ai_conversations 
                (session_id, user_query, ai_response, context, model_used,
                 response_time_ms, is_clarification)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, query, response, context, model, 
                  response_time_ms, is_clarification))
            
            conv_id = cursor.lastrowid
        
        # Обновляем статистику
        with self._transaction() as cursor:
            self._increment_stat(cursor, 'ai_requests')
        
        return self.get_ai_conversation(conv_id)
    
    def get_ai_conversation(self, conv_id: int) -> Optional[AIConversation]:
        """Получить диалог по ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ai_conversations WHERE id = ?', (conv_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_ai_conversation(row)
        return None
    
    def get_ai_session_history(self, session_id: str) -> List[AIConversation]:
        """Получить историю диалога по сессии"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM ai_conversations 
            WHERE session_id = ?
            ORDER BY created_at ASC
        ''', (session_id,))
        
        return [self._row_to_ai_conversation(row) for row in cursor.fetchall()]
    
    def get_recent_ai_conversations(self, limit: int = 20) -> List[AIConversation]:
        """Получить последние диалоги"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM ai_conversations 
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        return [self._row_to_ai_conversation(row) for row in cursor.fetchall()]
    
    def _row_to_ai_conversation(self, row: sqlite3.Row) -> AIConversation:
        return AIConversation(
            id=row['id'],
            session_id=row['session_id'],
            user_query=row['user_query'],
            ai_response=row['ai_response'],
            context=row['context'],
            model_used=row['model_used'],
            response_time_ms=row['response_time_ms'],
            tokens_used=row['tokens_used'],
            created_at=datetime.fromisoformat(row['created_at']),
            is_clarification=bool(row['is_clarification'])
        )
    
    # ==================== STATISTICS ====================
    
    def _increment_stat(self, cursor, field: str):
        """Инкрементировать поле статистики за сегодня"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO app_stats (date, {field})
            VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET
                {field} = {field} + 1
        '''.format(field=field), (today,))
    
    def get_today_stats(self) -> AppStats:
        """Получить статистику за сегодня"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM app_stats WHERE date = ?', (today,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_app_stats(row)
        
        return AppStats(date=today)
    
    def get_stats_range(self, days: int = 7) -> List[AppStats]:
        """Получить статистику за последние N дней"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM app_stats 
            WHERE date >= date('now', '-{} days')
            ORDER BY date DESC
        '''.format(days))
        
        return [self._row_to_app_stats(row) for row in cursor.fetchall()]
    
    def record_app_launch(self):
        """Записать запуск приложения"""
        with self._transaction() as cursor:
            self._increment_stat(cursor, 'app_launches')
    
    def add_session_time(self, minutes: int):
        """Добавить время сессии"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        with self._transaction() as cursor:
            cursor.execute('''
                INSERT INTO app_stats (date, total_session_time_minutes)
                VALUES (?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    total_session_time_minutes = total_session_time_minutes + ?
            ''', (today, minutes, minutes))
    
    def _row_to_app_stats(self, row: sqlite3.Row) -> AppStats:
        return AppStats(
            id=row['id'],
            date=row['date'],
            searches_count=row['searches_count'],
            weather_requests=row['weather_requests'],
            currency_requests=row['currency_requests'],
            news_requests=row['news_requests'],
            ai_requests=row['ai_requests'],
            app_launches=row['app_launches'],
            total_session_time_minutes=row['total_session_time_minutes']
        )
    
    # ==================== MAINTENANCE ====================
    
    def vacuum(self):
        """Оптимизировать базу данных"""
        conn = self._get_connection()
        conn.execute("VACUUM")
    
    def get_db_size(self) -> int:
        """Получить размер БД в байтах"""
        return Path(self.db_path).stat().st_size
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику базы данных"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        tables = ['search_history', 'favorite_sites', 'cache_entries', 
                'news_articles', 'ai_conversations', 'app_stats']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        stats['db_size_bytes'] = self.get_db_size()
        stats['db_path'] = self.db_path
        
        return stats
    
    def close(self):
        """Закрыть соединение с БД"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None