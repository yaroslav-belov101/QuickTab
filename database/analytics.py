"""
Analytics module for QuickTab
Сбор и анализ статистики использования
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import Counter

from .db_manager import DatabaseManager


class QuickTabAnalytics:
    """Аналитика использования приложения"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Получить статистику для дашборда"""
        today = self.db.get_today_stats()
        week_stats = self.db.get_stats_range(days=7)
        
        total_searches = sum(s.searches_count for s in week_stats)
        total_ai = sum(s.ai_requests for s in week_stats)
        
        # Популярные запросы
        popular_queries = self._get_popular_queries(limit=5)
        
        # Активность по часам
        hourly_activity = self._get_hourly_activity()
        
        return {
            'today': today.to_dict(),
            'week_total': {
                'searches': total_searches,
                'ai_requests': total_ai,
                'app_launches': sum(s.app_launches for s in week_stats)
            },
            'popular_queries': popular_queries,
            'hourly_activity': hourly_activity,
            'db_stats': self.db.get_stats()
        }
    
    def _get_popular_queries(self, limit: int = 5) -> List[Dict]:
        """Получить самые популярные запросы"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT query, COUNT(*) as count, MAX(created_at) as last_used
            FROM search_history
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY query
            ORDER BY count DESC
            LIMIT ?
        ''', (limit,))
        
        return [{
            'query': row['query'],
            'count': row['count'],
            'last_used': row['last_used']
        } for row in cursor.fetchall()]
    
    def _get_hourly_activity(self) -> List[int]:
        """Получить активность по часам (0-23)"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT strftime('%H', created_at) as hour, COUNT(*) as count
            FROM search_history
            WHERE created_at >= datetime('now', '-1 day')
            GROUP BY hour
            ORDER BY hour
        ''')
        
        # Заполняем все 24 часа
        activity = [0] * 24
        for row in cursor.fetchall():
            hour = int(row['hour'])
            activity[hour] = row['count']
        
        return activity
    
    def get_search_trends(self, days: int = 30) -> Dict[str, Any]:
        """Получить тренды поиска"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date(created_at) as day, COUNT(*) as count
            FROM search_history
            WHERE created_at >= date('now', '-{} days')
            GROUP BY day
            ORDER BY day
        '''.format(days))
        
        dates = []
        counts = []
        for row in cursor.fetchall():
            dates.append(row['day'])
            counts.append(row['count'])
        
        return {
            'dates': dates,
            'counts': counts,
            'total': sum(counts),
            'average': sum(counts) / len(counts) if counts else 0
        }
    
    def get_category_distribution(self) -> Dict[str, int]:
        """Распределение запросов по категориям"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT query_type, COUNT(*) as count
            FROM search_history
            GROUP BY query_type
        ''')
        
        return {row['query_type']: row['count'] for row in cursor.fetchall()}
    
    def get_favorite_sites_usage(self) -> List[Dict]:
        """Статистика использования избранных сайтов"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, click_count, last_accessed, category
            FROM favorite_sites
            ORDER BY click_count DESC
        ''')
        
        return [{
            'title': row['title'],
            'clicks': row['click_count'],
            'last_accessed': row['last_accessed'],
            'category': row['category']
        } for row in cursor.fetchall()]
    
    def export_analytics_report(self) -> str:
        """Экспортировать отчет в текстовом формате"""
        stats = self.get_dashboard_stats()
        trends = self.get_search_trends(days=7)
        categories = self.get_category_distribution()
        
        lines = [
            "=" * 60,
            "QUICKTAB ANALYTICS REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
            "",
            "📊 TODAY'S ACTIVITY",
            f"  Searches: {stats['today']['searches_count']}",
            f"  AI Requests: {stats['today']['ai_requests']}",
            f"  Weather Checks: {stats['today']['weather_requests']}",
            f"  App Launches: {stats['today']['app_launches']}",
            "",
            "📈 WEEKLY SUMMARY",
            f"  Total Searches: {stats['week_total']['searches']}",
            f"  Total AI Requests: {stats['week_total']['ai_requests']}",
            f"  Average per day: {stats['week_total']['searches'] / 7:.1f}",
            "",
            "🔍 TOP QUERIES",
        ]
        
        for i, query in enumerate(stats['popular_queries'], 1):
            lines.append(f"  {i}. '{query['query']}' ({query['count']} times)")
        
        lines.extend([
            "",
            "📂 CATEGORIES",
        ])
        
        for cat, count in categories.items():
            lines.append(f"  {cat}: {count}")
        
        lines.extend([
            "",
            "💾 DATABASE",
            f"  Path: {stats['db_stats']['db_path']}",
            f"  Size: {stats['db_stats']['db_size_bytes'] / 1024 / 1024:.2f} MB",
            "=" * 60
        ])
        
        return '\n'.join(lines)