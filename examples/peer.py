import sys
import os
import time
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.peer import P2PChatPeer

def print_help():
    print("\n💬 Available Commands:")
    print("  connect [ip] [port] - Connect to another peer")
    print("  friend [username]   - Send friend request")
    print("  accept [username]   - Accept friend request")
    print("  msg [friend] [text] - Send message")
    print("  group [name]        - Create group")
    print("  gmsg [group_id] [text] - Send group message")
    print("  search [name]       - Search users")
    print("  online              - Show online friends")
    print("  help                - Show this help message")
    print("  quit                - Exit")
    print("")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='P2P Chat Peer')
    parser.add_argument('--username', required=True, help='Your username')
    parser.add_argument('--port', type=int, default=8888, help='Port to listen on')
    parser.add_argument('--connect', help='Connect to peer (format: ip:port)')
    
    args = parser.parse_args()
    
    # Create and start the peer
    peer = P2PChatPeer(args.username, args.port)
    peer.start()
    
    time.sleep(2)
    
    print("\n" + "="*50)
    print(f"🎯 P2P Chat Peer: {args.username}")
    print("="*50)
    print(f"Peer ID: {args.username}@{peer.ip}:{args.port}")
    print("Status: Ready - waiting for connections")
    print("")
    
    # If this is not the first peer, connect to the bootstrap node
    # If this is not the first peer, connect to the bootstrap node
    if args.connect:
        ip, port = args.connect.split(":")
        port = int(port)
        print(f"🔄 Connecting to bootstrap node {ip}:{port}...")
        if peer.connect_to_peer(ip, port, max_retries=5, retry_delay=2):
            print(f"✅ Connected to bootstrap node {ip}:{port}")
            # After connecting to bootstrap, exchange peer info immediately
            time.sleep(1)
        else:
            print(f"❌ Failed to connect to bootstrap node")
            print("   Make sure the first peer is running")
    
    print("="*50)
    
    print_help()
    
    try:
        while True:
            try:
                cmd = input(f"{args.username}> ").strip()
            except EOFError:
                break
                
            if cmd == "quit":
                break
            elif cmd == "help":
                print_help()
            elif cmd.startswith("connect "):
                parts = cmd.split(" ")
                if len(parts) == 3:
                    ip, port = parts[1], int(parts[2])
                    print(f"🔄 Attempting to connect to {ip}:{port}...")
                    if peer.connect_to_peer(ip, port, max_retries=5, retry_delay=2):
                        print(f"✅ Successfully connected to {ip}:{port}")
                    else:
                        print(f"❌ Could not connect to {ip}:{port}")
                        print("   Make sure the peer is running and the port is correct")
                else:
                    print("❌ Usage: connect [ip] [port]")
            elif cmd.startswith("msg "):
                parts = cmd.split(" ", 2)
                if len(parts) == 3:
                    peer.send_message_to_friend(parts[1], parts[2])
                else:
                    print("❌ Usage: msg [friend] [message]")
            elif cmd.startswith("friend "):
                username = cmd.split(" ", 1)[1]
                peer.send_friend_request(username)
            elif cmd.startswith("accept "):
                username = cmd.split(" ", 1)[1]
                peer.accept_friend_request(username)
            elif cmd.startswith("group "):
                group_name = cmd.split(" ", 1)[1]
                group_id = peer.create_group(group_name)
                print(f"✅ Group '{group_name}' created with ID: {group_id}")
            elif cmd.startswith("gmsg "):
                parts = cmd.split(" ", 2)
                if len(parts) == 3:
                    peer.send_group_message(parts[1], parts[2])
                else:
                    print("❌ Usage: gmsg [group_id] [message]")
            elif cmd.startswith("search "):
                search_term = cmd.split(" ", 1)[1]
                results = peer.search_users(search_term)
                print(f"🔍 Search results: {results}")
            elif cmd == "online":
                peer.get_online_friends()
            elif cmd == "":
                continue
            else:
                print("❌ Unknown command. Type 'help' for available commands.")
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        peer.stop()

if __name__ == "__main__":
    main()