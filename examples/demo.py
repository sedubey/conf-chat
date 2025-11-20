"""
Universal Peer Demo Script
"""

def print_demo_instructions():
    print("\n" + "="*70)
    print("🎯 P2P CHAT SYSTEM - UNIVERSAL PEER DEMO")
    print("="*70)
    
    print("\nSTEP 1: Start the first peer (Bootstrap Node)")
    print("  Terminal 1:")
    print("  py peer.py --username alice --port 8888")
    print("")
    print("  This peer will show its connection info for other peers")
    
    print("\nSTEP 2: Start the second peer")
    print("  Terminal 2:")
    print("  py peer.py --username bob --port 8889 --connect localhost:8888")
    print("")
    print("  Bob will automatically connect to Alice's peer")
    
    print("\nSTEP 3: Start additional peers")
    print("  Terminal 3:")
    print("  py peer.py --username charlie --port 8890 --connect localhost:8888")
    print("")
    print("  Charlie will connect to the existing network")
    
    print("\nSTEP 4: Demo Commands")
    print("  In any peer:")
    print("    friend [username]  - Send friend request")
    print("    accept [username]  - Accept friend request")
    print("    msg [friend] [msg] - Send message")
    print("    online             - Show friends")
    print("    help               - Show all commands")
    
    print("\n" + "="*70)
    print("Key Features Demonstrated:")
    print("✅ True P2P - No central server")
    print("✅ Bootstrap node discovery")
    print("✅ Dynamic peer joining")
    print("✅ Multi-peer communication")
    print("="*70 + "\n")

if __name__ == "__main__":
    print_demo_instructions()