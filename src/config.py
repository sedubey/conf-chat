import socket

# Configuration constants
DEFAULT_PORT = 8888
BUFFER_SIZE = 4096
ENCODING = 'utf-8'

# Message types
MSG_TEXT = "TEXT"
MSG_FRIEND_REQUEST = "FRIEND_REQ"
MSG_FRIEND_ACCEPT = "FRIEND_ACC"
MSG_GROUP_CREATE = "GROUP_CREATE"
MSG_GROUP_INVITE = "GROUP_INVITE"
MSG_GROUP_MESSAGE = "GROUP_MSG"
MSG_OFFLINE = "OFFLINE_MSG"
MSG_PEER_DISCOVERY = "PEER_DISCOVERY"  # New: for finding users
MSG_USER_LOOKUP = "USER_LOOKUP"        # New: for finding specific users

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"