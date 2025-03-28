import aiosqlite
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        
    async def setup(self):
        """Initialize the database and create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    display_name TEXT,
                    registration_date TEXT NOT NULL,
                    additional_info TEXT
                )
            ''')
            
            # Create chat_history table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def is_user_registered(self, user_id):
        """Check if a user is already registered."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM users WHERE user_id = ?", 
                (str(user_id),)
            )
            result = await cursor.fetchone()
            return result is not None
    
    async def register_user(self, user_id, username, display_name, additional_info=None):
        """Register a new user in the database."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO users (user_id, username, display_name, registration_date, additional_info) VALUES (?, ?, ?, ?, ?)",
                    (str(user_id), username, display_name, datetime.now().isoformat(), additional_info)
                )
                await db.commit()
                logger.info(f"User {username} ({user_id}) registered successfully")
                return True
        except aiosqlite.IntegrityError:
            logger.warning(f"User {user_id} already exists in database")
            return False
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return False
    
    async def get_all_users(self):
        """Get all registered users from the database."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT user_id, username, display_name, registration_date, additional_info FROM users"
            )
            users = await cursor.fetchall()
            return [dict(user) for user in users]
    
    async def store_chat_interaction(self, user_id, message, response):
        """Store a chat interaction in the database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO chat_history (user_id, message, response, timestamp) VALUES (?, ?, ?, ?)",
                (str(user_id), message, response, datetime.now().isoformat())
            )
            await db.commit()
            logger.info(f"Chat interaction stored for user {user_id}")
