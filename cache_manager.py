import hashlib
import json
import pickle
import os
from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta
import sqlite3
from threading import Lock

class CacheManager:
    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 500):
        """Initialize cache manager with SQLite backend"""
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.db_path = os.path.join(cache_dir, "cache.db")
        self.lock = Lock()
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for cache"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value_path TEXT,
                    created_at TIMESTAMP,
                    accessed_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    size_bytes INTEGER,
                    cache_type TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_accessed_at ON cache_entries(accessed_at)
            """)
    
    def _generate_key(self, data: Any) -> str:
        """Generate cache key from data"""
        if isinstance(data, str):
            key_data = data
        else:
            key_data = json.dumps(data, sort_keys=True)
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_value_path(self, key: str) -> str:
        """Get file path for cached value"""
        return os.path.join(self.cache_dir, f"{key}.pkl")
    
    def set(self, key_data: Any, value: Any, cache_type: str = "general", 
            expire_hours: int = 24) -> bool:
        """Set cache entry"""
        try:
            with self.lock:
                key = self._generate_key(key_data)
                value_path = self._get_value_path(key)
                
                # Serialize and save value
                with open(value_path, 'wb') as f:
                    pickle.dump(value, f)
                
                # Get file size
                size_bytes = os.path.getsize(value_path)
                
                # Update database
                expires_at = datetime.now() + timedelta(hours=expire_hours)
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO cache_entries 
                        (key, value_path, created_at, accessed_at, expires_at, size_bytes, cache_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (key, value_path, datetime.now(), datetime.now(), 
                          expires_at, size_bytes, cache_type))
                
                # Clean up if needed
                self._cleanup_if_needed()
                
                return True
                
        except Exception as e:
            print(f"Error setting cache: {str(e)}")
            return False
    
    def get(self, key_data: Any) -> Optional[Any]:
        """Get cache entry"""
        try:
            with self.lock:
                key = self._generate_key(key_data)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT value_path, expires_at FROM cache_entries 
                        WHERE key = ? AND expires_at > ?
                    """, (key, datetime.now()))
                    
                    result = cursor.fetchone()
                    
                    if result:
                        value_path, expires_at = result
                        
                        # Update access time
                        conn.execute("""
                            UPDATE cache_entries SET accessed_at = ? WHERE key = ?
                        """, (datetime.now(), key))
                        
                        # Load and return value
                        if os.path.exists(value_path):
                            with open(value_path, 'rb') as f:
                                return pickle.load(f)
                
                return None
                
        except Exception as e:
            print(f"Error getting cache: {str(e)}")
            return None
    
    def delete(self, key_data: Any) -> bool:
        """Delete cache entry"""
        try:
            with self.lock:
                key = self._generate_key(key_data)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT value_path FROM cache_entries WHERE key = ?
                    """, (key,))
                    
                    result = cursor.fetchone()
                    
                    if result:
                        value_path = result[0]
                        
                        # Delete file
                        if os.path.exists(value_path):
                            os.remove(value_path)
                        
                        # Delete database entry
                        conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                        
                        return True
                
                return False
                
        except Exception as e:
            print(f"Error deleting cache: {str(e)}")
            return False
    
    def _cleanup_if_needed(self):
        """Clean up cache if size exceeds limit"""
        try:
            # Get total cache size
            total_size = 0
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT SUM(size_bytes) FROM cache_entries")
                result = cursor.fetchone()
                if result[0]:
                    total_size = result[0]
            
            max_size_bytes = self.max_size_mb * 1024 * 1024
            
            if total_size > max_size_bytes:
                # Remove expired entries first
                self._remove_expired()
                
                # If still over limit, remove least recently used
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("SELECT SUM(size_bytes) FROM cache_entries")
                    result = cursor.fetchone()
                    if result[0] and result[0] > max_size_bytes:
                        self._remove_lru(max_size_bytes * 0.8)  # Remove to 80% of limit
                        
        except Exception as e:
            print(f"Error in cache cleanup: {str(e)}")
    
    def _remove_expired(self):
        """Remove expired cache entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get expired entries
                cursor = conn.execute("""
                    SELECT key, value_path FROM cache_entries 
                    WHERE expires_at <= ?
                """, (datetime.now(),))
                
                expired_entries = cursor.fetchall()
                
                # Delete files and database entries
                for key, value_path in expired_entries:
                    if os.path.exists(value_path):
                        os.remove(value_path)
                
                conn.execute("DELETE FROM cache_entries WHERE expires_at <= ?", 
                           (datetime.now(),))
                
                if expired_entries:
                    print(f"Removed {len(expired_entries)} expired cache entries")
                    
        except Exception as e:
            print(f"Error removing expired entries: {str(e)}")
    
    def _remove_lru(self, target_size_bytes: float):
        """Remove least recently used entries until target size is reached"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get entries ordered by access time (oldest first)
                cursor = conn.execute("""
                    SELECT key, value_path, size_bytes FROM cache_entries 
                    ORDER BY accessed_at ASC
                """)
                
                current_size = 0
                cursor_total = conn.execute("SELECT SUM(size_bytes) FROM cache_entries")
                result = cursor_total.fetchone()
                if result[0]:
                    current_size = result[0]
                
                removed_count = 0
                for key, value_path, size_bytes in cursor:
                    if current_size <= target_size_bytes:
                        break
                    
                    # Delete file
                    if os.path.exists(value_path):
                        os.remove(value_path)
                    
                    # Delete database entry
                    conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                    
                    current_size -= size_bytes
                    removed_count += 1
                
                if removed_count > 0:
                    print(f"Removed {removed_count} LRU cache entries")
                    
        except Exception as e:
            print(f"Error removing LRU entries: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total entries and size
                cursor = conn.execute("""
                    SELECT COUNT(*), COALESCE(SUM(size_bytes), 0) FROM cache_entries
                """)
                total_entries, total_size = cursor.fetchone()
                
                # Entries by type
                cursor = conn.execute("""
                    SELECT cache_type, COUNT(*), COALESCE(SUM(size_bytes), 0) 
                    FROM cache_entries GROUP BY cache_type
                """)
                by_type = {row[0]: {'count': row[1], 'size': row[2]} for row in cursor}
                
                return {
                    'total_entries': total_entries,
                    'total_size_mb': total_size / (1024 * 1024),
                    'max_size_mb': self.max_size_mb,
                    'by_type': by_type
                }
                
        except Exception as e:
            print(f"Error getting cache stats: {str(e)}")
            return {}
    
    def clear_all(self, cache_type: Optional[str] = None):
        """Clear all cache entries or specific type"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    if cache_type:
                        # Clear specific type
                        cursor = conn.execute("""
                            SELECT value_path FROM cache_entries WHERE cache_type = ?
                        """, (cache_type,))
                        
                        for (value_path,) in cursor:
                            if os.path.exists(value_path):
                                os.remove(value_path)
                        
                        conn.execute("DELETE FROM cache_entries WHERE cache_type = ?", 
                                   (cache_type,))
                    else:
                        # Clear all
                        cursor = conn.execute("SELECT value_path FROM cache_entries")
                        
                        for (value_path,) in cursor:
                            if os.path.exists(value_path):
                                os.remove(value_path)
                        
                        conn.execute("DELETE FROM cache_entries")
                        
        except Exception as e:
            print(f"Error clearing cache: {str(e)}")

class EmbeddingCache:
    """Specialized cache for embeddings"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text"""
        return self.cache_manager.get(f"embedding:{text}")
    
    def set_embedding(self, text: str, embedding: List[float]):
        """Cache embedding for text"""
        self.cache_manager.set(f"embedding:{text}", embedding, "embedding", expire_hours=168)  # 1 week
    
    def get_batch_embeddings(self, texts: List[str]) -> Dict[str, List[float]]:
        """Get cached embeddings for multiple texts"""
        cached = {}
        for text in texts:
            embedding = self.get_embedding(text)
            if embedding:
                cached[text] = embedding
        return cached
    
    def set_batch_embeddings(self, text_embeddings: Dict[str, List[float]]):
        """Cache multiple embeddings"""
        for text, embedding in text_embeddings.items():
            self.set_embedding(text, embedding)

class SearchCache:
    """Specialized cache for search results"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
    
    def get_search_results(self, query: str, search_params: Dict) -> Optional[List[Dict]]:
        """Get cached search results"""
        cache_key = {
            'query': query,
            'params': search_params
        }
        return self.cache_manager.get(cache_key)
    
    def set_search_results(self, query: str, search_params: Dict, results: List[Dict]):
        """Cache search results"""
        cache_key = {
            'query': query,
            'params': search_params
        }
        self.cache_manager.set(cache_key, results, "search", expire_hours=6)  # 6 hours
