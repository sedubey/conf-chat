import sqlite3
import hashlib
import json
from datetime import datetime

class UserDatabase:
    def __init__(self, username):
        self.db_name = f"{username}_chat.db"
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        # Users table (local user + friends)
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (username TEXT PRIMARY KEY, 
                     public_key TEXT,
                     ip TEXT,
                     port INTEGER,
                     is_online INTEGER DEFAULT 0)''')
        
        # Friends table (relationship management)
        c.execute('''CREATE TABLE IF NOT EXISTS friends
                    (user1 TEXT, user2 TEXT, 
                     status TEXT CHECK(status IN ('pending', 'accepted')),
                     PRIMARY KEY (user1, user2))''')
        
        # Messages table
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                    (id TEXT PRIMARY KEY,
                     sender TEXT,
                     recipient TEXT,
                     group_id TEXT,
                     content TEXT,
                     timestamp REAL,
                     delivered INTEGER DEFAULT 0,
                     message_type TEXT)''')
        
        # Groups table
        c.execute('''CREATE TABLE IF NOT EXISTS groups
                    (group_id TEXT PRIMARY KEY,
                     group_name TEXT,
                     creator TEXT,
                     created_at REAL)''')
        
        # Group members table
        c.execute('''CREATE TABLE IF NOT EXISTS group_members
                    (group_id TEXT,
                     username TEXT,
                     joined_at REAL,
                     PRIMARY KEY (group_id, username))''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, username, public_key=None, ip=None, port=None):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO users 
                    (username, public_key, ip, port, is_online)
                    VALUES (?, ?, ?, ?, ?)''',
                 (username, public_key, ip, port, 1))
        conn.commit()
        conn.close()
    
    def update_user_status(self, username, is_online, ip=None, port=None):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        if ip and port:
            c.execute('''UPDATE users SET is_online=?, ip=?, port=? 
                        WHERE username=?''', 
                     (1 if is_online else 0, ip, port, username))
        else:
            c.execute('''UPDATE users SET is_online=? WHERE username=?''',
                     (1 if is_online else 0, username))
        conn.commit()
        conn.close()
    
    def add_friend_request(self, from_user, to_user):
        """Add a friend request - from_user requests to be friends with to_user"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        # Store the request in both directions for easier querying
        c.execute('''INSERT OR IGNORE INTO friends 
                    (user1, user2, status) VALUES (?, ?, ?)''',
                 (from_user, to_user, 'pending'))
        conn.commit()
        conn.close()

    def accept_friend_request(self, accepting_user, requesting_user):
        """Accept a friend request - accepting_user accepts request from requesting_user"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
    
        # First, delete any pending request
        c.execute('''DELETE FROM friends 
                    WHERE user1=? AND user2=? AND status='pending' ''', 
                (requesting_user, accepting_user))
    
        # Now create a SINGLE friendship record (direction doesn't matter for friendship)
        # We'll always store it with the alphabetically first username as user1
        users_sorted = sorted([accepting_user, requesting_user])
        user1, user2 = users_sorted[0], users_sorted[1]
    
        c.execute('''INSERT OR REPLACE INTO friends 
                    (user1, user2, status) VALUES (?, ?, ?)''',
                (user1, user2, 'accepted'))
    
        conn.commit()
        conn.close()

    def get_friends(self, username):
        """Get all accepted friends for a user"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        # Friends are where user1=username OR user2=username and status is accepted
        c.execute('''SELECT user1, user2 FROM friends 
                    WHERE ((user1=? OR user2=?) AND status='accepted')''', 
                (username, username))
        friends = []
        for row in c.fetchall():
            if row[0] == username:
                friends.append(row[1])
            else:
                friends.append(row[0])
        conn.close()
        # Remove duplicates and return sorted list
        unique_friends = sorted(list(set(friends)))
        return unique_friends

    def get_pending_requests(self, username):
        """Get pending friend requests for a user"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        # Pending requests where this user is the recipient
        c.execute('''SELECT user1 FROM friends 
                    WHERE user2=? AND status='pending' ''', (username,))
        pending = [row[0] for row in c.fetchall()]
        conn.close()
        unique_pending = sorted(list(set(pending)))
        return unique_pending
    
    def store_message(self, message):
        """Store a message in the database, handling duplicates gracefully"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        try:
            c.execute('''INSERT OR IGNORE INTO messages 
                        (id, sender, recipient, group_id, content, timestamp, message_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (message.id, message.sender, message.recipient,
                      message.group_id, message.content, message.timestamp,
                      message.msg_type))
            conn.commit()
        except sqlite3.IntegrityError:
            # Message already exists, ignore
            pass
        finally:
            conn.close()
    
    def get_undelivered_messages(self, username):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''SELECT * FROM messages 
                    WHERE recipient=? AND delivered=0''', (username,))
        messages = c.fetchall()
        conn.close()
        return messages
    
    def mark_message_delivered(self, message_id):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''UPDATE messages SET delivered=1 WHERE id=?''', (message_id,))
        conn.commit()
        conn.close()