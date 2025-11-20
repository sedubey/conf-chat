import hashlib
import json

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def search_users(search_term, users_list):
    """Search users by name (word match)"""
    search_words = search_term.lower().split()
    results = []
    
    for user in users_list:
        name_lower = user.lower()
        for word in search_words:
            if word in name_lower:
                results.append(user)
                break
    
    return results

def validate_username(username):
    """Basic username validation"""
    if len(username) < 3 or len(username) > 20:
        return False
    if not username.replace('_', '').isalnum():
        return False
    return True