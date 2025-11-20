import socket
import threading
import time
import json
from typing import Dict, List, Set
from .message import Message
from .database import UserDatabase
from .config import *
from .utils import hash_password, search_users, validate_username

class P2PChatPeer:
    def __init__(self, username, port=DEFAULT_PORT, bootstrap_nodes=None):
        self.username = username.lower()  # Normalize username to lowercase
        self.port = port
        self.ip = get_local_ip()
        self.running = False
        self.server_socket = None
        self.connected_peers: Dict[str, socket.socket] = {}
        self.known_peers: Dict[str, tuple] = {}  # username -> (ip, port)
        self.groups: Dict[str, Set[str]] = {}  # group_id -> set of members
        
        # Initialize database
        self.db = UserDatabase(username)
        self.db.add_user(username, ip=self.ip, port=self.port)
        
        # Store known bootstrap nodes
        if bootstrap_nodes is None:
            self.bootstrap_nodes = set([('localhost', 8888)])  # Default bootstrap
        else:
            self.bootstrap_nodes = set(bootstrap_nodes)
        
        print(f"Peer {username} initialized on {self.ip}:{port}")
    
    def start(self):
        """Start the P2P peer server"""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            print(f"Peer server listening on port {self.port}")
            
            # Start listening for connections
            listen_thread = threading.Thread(target=self._accept_connections)
            listen_thread.daemon = True
            listen_thread.start()
            
        except Exception as e:
            print(f"Error starting server: {e}")
            self.running = False
    
    def _accept_connections(self):
        """Accept incoming connections from other peers"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"New connection from {addr}")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_socket, addr):
        """Handle messages from a connected client"""
        buffer = b""
        try:
            while self.running:
                # Try to receive data
                try:
                    data = client_socket.recv(BUFFER_SIZE)
                    if not data:
                        break
                    buffer += data
                    
                    # Try to decode complete JSON messages
                    while buffer:
                        try:
                            # Find a complete JSON object
                            decoded = buffer.decode(ENCODING)
                            message_str = decoded.split('}{', 1)[0] + '}' if '}{' in decoded else decoded
                            
                            message = Message.from_json(message_str)
                            self._process_message(message, client_socket)
                            
                            # Remove processed message from buffer
                            remaining = buffer[len(message_str.encode(ENCODING)):]
                            buffer = remaining
                            
                        except (json.JSONDecodeError, KeyError):
                            # Incomplete message, wait for more data
                            break
                            
                except socket.timeout:
                    continue
                except BlockingIOError:
                    continue
                    
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            client_socket.close()
            # Remove from connected peers if present
            to_remove = []
            for peer_id, sock in self.connected_peers.items():
                if sock == client_socket:
                    to_remove.append(peer_id)
            for peer_id in to_remove:
                del self.connected_peers[peer_id]
    
    def _process_message(self, message: Message, client_socket):
        """Process incoming messages based on type"""
        # Don't process our own messages
        if message.sender.lower() == self.username:
            return
        
        print(f"Received {message.msg_type} message from {message.sender}")

        # Store peer information from any message (but only if we don't already know them)
        if (hasattr(message, 'sender') and message.sender and 
            message.sender.lower() not in self.known_peers):
            try:
                peer_addr = client_socket.getpeername()
                self.known_peers[message.sender.lower()] = (peer_addr[0], peer_addr[1])
            except:
                pass

        # Route messages intended for specific users
        if (message.recipient and 
            message.recipient.lower() != self.username and 
            message.recipient.lower() != "all"):
            # Message is for someone else, forward it (but only once)
            if not getattr(message, '_forwarded', False):
                message._forwarded = True  # Mark as forwarded to prevent loops
                self.send_direct_message(message.recipient, message)
            return

        # Process messages intended for us
        if message.msg_type == MSG_TEXT:
            self._handle_text_message(message)
        elif message.msg_type == MSG_FRIEND_REQUEST:
            self._handle_friend_request(message)
        elif message.msg_type == MSG_FRIEND_ACCEPT:
            self._handle_friend_accept(message)
        elif message.msg_type == MSG_GROUP_MESSAGE:
            self._handle_group_message(message)
        elif message.msg_type == MSG_GROUP_INVITE:
            self._handle_group_invite(message)
        elif message.msg_type == MSG_OFFLINE:
            self._handle_offline_message(message)
        elif message.msg_type == MSG_PEER_DISCOVERY:
            self._handle_peer_discovery(message)
        elif message.msg_type == MSG_USER_LOOKUP:
            self._handle_user_lookup(message)
    
    def _handle_text_message(self, message: Message):
        """Handle incoming text message"""
        print(f"\n📨 New message from {message.sender}: {message.content}\n")
        self.db.store_message(message)
    
    def _handle_friend_request(self, message: Message):
        """Handle friend request"""
        from_user = message.sender.lower()  # Normalize case
        
        # Don't process our own messages
        if from_user == self.username:
            return
            
        print(f"\n🎯 FRIEND REQUEST from {from_user}")
        print(f"   Type: accept {from_user}")
        print(f"   Or ignore it")
        print(f"   (Type 'help' for all commands)\n")
        
        # Store the pending request
        self.db.add_friend_request(from_user, self.username)
    
    def _handle_friend_accept(self, message: Message):
        """Handle friend acceptance"""
        friend = message.sender.lower()  # Normalize case

        # Don't process our own messages
        if friend == self.username:
            return
        
        print(f"\n✅ FRIEND REQUEST ACCEPTED by {friend}!")
        print(f"   You are now friends with {friend}")
        print(f"   You can now send messages: msg {friend} [your message]\n")

        # Update friendship status in OUR database too
        self.db.accept_friend_request(friend, self.username)

        # Also add the friend to our user database with their connection info
        self.db.add_user(friend, ip=message.content.get('ip'), 
                        port=message.content.get('port'))
    
    def _handle_group_message(self, message: Message):
        """Handle group message"""
        print(f"\n👥 Group message from {message.sender}: {message.content}\n")
        self.db.store_message(message)
    
    def _handle_group_invite(self, message: Message):
        """Handle group invitation"""
        group_id = message.content['group_id']
        group_name = message.content['group_name']
        print(f"\n🎯 Invited to group '{group_name}' by {message.sender}")
        
        # Add to local group
        if group_id not in self.groups:
            self.groups[group_id] = set()
        self.groups[group_id].add(self.username)
    
    def _handle_offline_message(self, message: Message):
        """Handle stored offline messages"""
        messages = message.content.get('messages', [])
        for msg_data in messages:
            msg = Message.from_json(json.dumps(msg_data))
            print(f"\n📫 Offline message from {msg.sender}: {msg.content}")
            self.db.mark_message_delivered(msg.id)
    
    def _handle_peer_discovery(self, message: Message):
        """Handle peer discovery messages"""
        peer_username = message.sender.lower()
        peer_ip = message.content.get('ip')
        peer_port = message.content.get('port')
        
        if peer_username != self.username and peer_ip and peer_port:
            self.known_peers[peer_username] = (peer_ip, peer_port)
    
    def _handle_user_lookup(self, message: Message):
        """Handle user lookup requests"""
        target_user = message.content.get('target_user', '')
        if target_user.lower() == self.username.lower():
            # Only respond if we haven't recently responded to this same request
            request_id = f"{message.sender}_{target_user}"
            if not hasattr(self, '_recent_lookups'):
                self._recent_lookups = set()
        
            if request_id not in self._recent_lookups:
                self._recent_lookups.add(request_id)
                # Clean up old lookups after a while
                if len(self._recent_lookups) > 10:
                    self._recent_lookups.clear()
            
                # Send our connection info back
                response = Message(MSG_PEER_DISCOVERY, self.username,
                             {"ip": self.ip, "port": self.port},
                             message.sender)
                self.send_direct_message(message.sender, response)
    
    def _find_user_connection(self, username):
        """Find the socket connection for a specific user"""
        username_lower = username.lower()

        # Don't look up ourselves
        if username_lower == self.username:
            return None

        # Check if we know this user's address
        if username_lower in self.known_peers:
            ip, port = self.known_peers[username_lower]
            peer_id = f"{ip}:{port}"
        
            # Check if we're already connected
            if peer_id in self.connected_peers:
                return self.connected_peers[peer_id]
        
            # Only try to connect if we're not already connected to this peer
            if (ip, port) != (self.ip, self.port):
                if self.connect_to_peer(ip, port, max_retries=1, retry_delay=0):
                    return self.connected_peers.get(peer_id)
    
        return None
    
    def send_direct_message(self, target_username, message):
        """Send message directly to a specific user if possible"""
        target_username = target_username.lower()

        # Don't try to send to ourselves
        if target_username == self.username:
            return True

        # Try to find direct connection first
        target_socket = self._find_user_connection(target_username)

        if target_socket and target_socket.fileno() != -1:
            try:
                message_json = message.to_json().encode(ENCODING)
                target_socket.send(message_json)
                return True
            except Exception as e:
                # Remove broken connection
                to_remove = []
                for peer_id, sock in self.connected_peers.items():
                    if sock == target_socket:
                        to_remove.append(peer_id)
                for peer_id in to_remove:
                    del self.connected_peers[peer_id]

        # For certain message types, don't broadcast to avoid loops
        if message.msg_type in [MSG_USER_LOOKUP, MSG_PEER_DISCOVERY]:
            return False

        # Fallback: broadcast and let recipients filter
        self._broadcast_message(message)
        return False
    
    def connect_to_peer(self, ip, port, max_retries=3, retry_delay=2):
        """Connect to another peer with retry logic"""
        if (ip, port) == (self.ip, self.port):
            return False  # Don't connect to self
        
        peer_id = f"{ip}:{port}"
        if peer_id in self.connected_peers:
            return True  # Already connected
        
        # Try multiple times with delays
        for attempt in range(max_retries):
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.settimeout(5.0)  # 5 second timeout for connection
                peer_socket.connect((ip, port))
                
                # Store connection
                self.connected_peers[peer_id] = peer_socket
                
                # Start listening for messages from this peer
                thread = threading.Thread(target=self._listen_to_peer, 
                                        args=(peer_socket, peer_id))
                thread.daemon = True
                thread.start()
                
                # Exchange peer information
                self._exchange_peer_info(peer_socket)
                
                print(f"✅ Connected to peer {ip}:{port}")
                return True
                
            except Exception as e:
                if attempt < max_retries - 1:  # Don't print on last attempt
                    print(f"⚠️  Connection attempt {attempt + 1} failed: {e}")
                    print(f"   Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    if max_retries > 1:  # Only show error if we actually tried multiple times
                        print(f"❌ Failed to connect to {ip}:{port} after {max_retries} attempts")
                    return False
    
    def _exchange_peer_info(self, peer_socket):
        """Exchange peer information with newly connected peer"""
        info_msg = Message(MSG_PEER_DISCOVERY, self.username,
                          {"ip": self.ip, "port": self.port})
        try:
            peer_socket.send(info_msg.to_json().encode(ENCODING))
        except:
            pass
    
    def _listen_to_peer(self, peer_socket, peer_id):
        """Listen for messages from a specific peer"""
        buffer = b""
        try:
            while self.running and peer_socket.fileno() != -1:
                try:
                    data = peer_socket.recv(BUFFER_SIZE)
                    if not data:
                        break
                    buffer += data
                    
                    # Try to decode complete JSON messages
                    while buffer:
                        try:
                            decoded = buffer.decode(ENCODING)
                            # Handle multiple JSON messages
                            if '}{' in decoded:
                                message_str = decoded.split('}{', 1)[0] + '}'
                            else:
                                message_str = decoded
                            
                            message = Message.from_json(message_str)
                            self._process_message(message, peer_socket)
                            
                            # Remove processed message from buffer
                            remaining = buffer[len(message_str.encode(ENCODING)):]
                            buffer = remaining
                            
                        except (json.JSONDecodeError, KeyError) as e:
                            # Incomplete message, wait for more data
                            break
                            
                except socket.timeout:
                    continue
                except (BlockingIOError, ConnectionResetError, OSError):
                    break
                    
        except Exception as e:
            if self.running:
                print(f"Error listening to peer {peer_id}: {e}")
        finally:
            try:
                if peer_id in self.connected_peers:
                    del self.connected_peers[peer_id]
                peer_socket.close()
            except:
                pass
    
    def send_message_to_friend(self, friend_username, text):
        """Send message to a friend"""
        # Convert to lowercase for consistency
        friend_username = friend_username.lower()

        # Double-check friendship status with a small delay to ensure database is updated
        time.sleep(0.1)

        # Check if friend is in database
        friends = self.db.get_friends(self.username)
        if friend_username not in friends:
            print(f"❌ {friend_username} is not your friend!")
            print(f"   Your current friends: {friends}")
            print(f"   Send a friend request first: friend {friend_username}")
            return

        # Create message
        message = Message(MSG_TEXT, self.username, text, friend_username)
        self.db.store_message(message)

        # Send directly if possible, otherwise broadcast
        if not self.send_direct_message(friend_username, message):
            print(f"⚠️  Friend {friend_username} not directly connected. Message sent to network.")
        else:
            print(f"✅ Message sent to {friend_username}")
    
    def send_friend_request(self, target_username):
        """Send friend request to another user"""
        # Convert to lowercase for consistency
        target_username = target_username.lower()
        
        # Don't send to self
        if target_username == self.username:
            print("❌ You cannot send a friend request to yourself!")
            return
        
        # Check if already friends
        current_friends = self.db.get_friends(self.username)
        if target_username in current_friends:
            print(f"❌ You are already friends with {target_username}!")
            return
        
        # Check if request already pending
        pending = self.db.get_pending_requests(self.username)
        if target_username in pending:
            print(f"❌ You already have a pending friend request from {target_username}!")
            print(f"   Type: accept {target_username}")
            return
        
        message = Message(MSG_FRIEND_REQUEST, self.username, 
                         {"reason": f"Friend request from {self.username}"},
                         target_username)
        
        # Store locally
        self.db.add_friend_request(self.username, target_username)
        
        # Send directly if possible, otherwise broadcast
        if not self.send_direct_message(target_username, message):
            print(f"⚠️  User {target_username} not directly connected. Request sent to network.")
        else:
            print(f"✅ Friend request sent to {target_username}")
    
    def accept_friend_request(self, friend_username):
        """Accept a friend request from the specified user"""
        # Convert to lowercase for consistency
        friend_username = friend_username.lower()

        # Don't accept self
        if friend_username == self.username:
            print("❌ You cannot accept a friend request from yourself!")
            return

        # Check if request exists
        pending = self.db.get_pending_requests(self.username)
        if friend_username not in pending:
            print(f"❌ No pending friend request from {friend_username}!")
            print(f"   Your pending requests: {pending}")
            return

        # Accept the request
        self.db.accept_friend_request(self.username, friend_username)

        # Send acceptance message
        message = Message(MSG_FRIEND_ACCEPT, self.username,
                     {"ip": self.ip, "port": self.port},
                     friend_username)

        # Send directly if possible, otherwise broadcast
        if not self.send_direct_message(friend_username, message):
            print(f"⚠️  User {friend_username} not directly connected. Acceptance sent to network.")
        else:
            print(f"✅ Accepted friend request from {friend_username}")
    
    def create_group(self, group_name, initial_members=None):
        """Create a new group chat"""
        group_id = f"group_{int(time.time())}_{hash(group_name) % 10000}"
        self.groups[group_id] = set([self.username])
        
        if initial_members:
            for member in initial_members:
                member_lower = member.lower()
                if member_lower in self.db.get_friends(self.username):
                    self.groups[group_id].add(member_lower)
                    # Send invitation
                    invite_msg = Message(MSG_GROUP_INVITE, self.username,
                                        {"group_id": group_id, "group_name": group_name},
                                        member_lower)
                    self.send_direct_message(member_lower, invite_msg)
        
        print(f"✅ Group '{group_name}' created with ID: {group_id}")
        return group_id
    
    def send_group_message(self, group_id, text):
        """Send message to a group"""
        if group_id not in self.groups:
            print("❌ Group not found!")
            return
        
        message = Message(MSG_GROUP_MESSAGE, self.username, text, 
                         group_id=group_id)
        
        # Store locally and broadcast to all connected peers
        self.db.store_message(message)
        self._broadcast_message(message)
        print(f"✅ Group message sent to {group_id}")
    
    def _broadcast_message(self, message: Message):
        """Broadcast message to all connected peers"""
        message_json = message.to_json().encode(ENCODING)
        
        disconnected_peers = []
        for peer_id, peer_socket in self.connected_peers.items():
            try:
                if peer_socket.fileno() != -1:  # Check if socket is still valid
                    peer_socket.send(message_json)
                else:
                    disconnected_peers.append(peer_id)
            except (BrokenPipeError, ConnectionResetError, OSError):
                disconnected_peers.append(peer_id)
        
        # Clean up disconnected peers
        for peer_id in disconnected_peers:
            try:
                if peer_id in self.connected_peers:
                    sock = self.connected_peers[peer_id]
                    sock.close()
                    del self.connected_peers[peer_id]
            except:
                pass
    
    def get_online_friends(self):
        """Get list of online friends with status"""
        friends = self.db.get_friends(self.username)
        if not friends:
            print("🤷 You don't have any friends yet. Use 'friend [username]' to add someone!")
            return []
        
        print(f"🟢 Your friends: {friends}")
        
        # Check pending requests
        pending = self.db.get_pending_requests(self.username)
        if pending:
            print(f"⏳ Pending friend requests from: {pending}")
        
        return friends
    
    def search_users(self, search_term):
        """Search for users by name"""
        # This would normally query a distributed user directory
        # For demo, we'll return some mock results
        all_users = ["alice_smith", "bob_jones", "charlie_brown", 
                    "diana_ross", "evan_wright"]
        return search_users(search_term, all_users)
    
    def stop(self):
        """Stop the peer"""
        self.running = False
        
        # Close all peer connections
        for peer_id, peer_socket in list(self.connected_peers.items()):
            try:
                peer_socket.close()
            except:
                pass
        self.connected_peers.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        print("Peer stopped")