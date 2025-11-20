# Conf-Chat: Pure Peer-to-Peer Chat System

A decentralized, serverless chat application built with pure Python that demonstrates true peer-to-peer architecture. No central servers, no intermediaries - just direct communication between users.

## Features

- **True P2P Architecture**: No central servers - all communication is direct between peers
- **Friend Management**: Send and accept friend requests in a distributed manner
- **Direct Messaging**: One-on-one encrypted-style messaging between friends
- **Group Chats**: Create and participate in multi-user conference chats
- **User Discovery**: Search and find users across the P2P network
- **Online Status**: See which of your friends are currently online
- **Fault Tolerant**: Network continues even if individual peers go offline
- **Offline Messaging**: Store and deliver messages when friends come online

## Architecture

Conf-Chat implements a pure P2P architecture where:
- Each peer acts as both client and server
- Peers discover each other through bootstrap connections
- All messaging is direct between users (no message relaying)
- Each peer maintains their own local database
- Network is resilient to individual peer failures

Network Topology:
    Peer A (Bootstrap)
    ↙       ↘
Peer B   Peer C
  ↓         ↓
Peer D   Peer E

## Requirements

- Python 3.8+
- No external dependencies - uses only Python standard library

## Installation

1. **Clone or download** this repository
2. **No additional installation required** - uses only Python built-in libraries


## Quick Start

### Starting the First Peer (Bootstrap Node)

python examples/peer_instance.py --username alice --port 8888

The first peer will display connection information that other peers can use to join the network.

### Starting Additional Peers

Connect to Alice's peer:
python examples/peer_instance.py --username bob --port 8889 --connect localhost:8888

Connect through any existing peer:
python examples/peer_instance.py --username charlie --port 8890 --connect localhost:8889


## Usage

### Available Commands

Once your peer is running, you can use these commands:

- `connect [ip] [port]` - Connect to another peer (e.g., `connect localhost 8888`)
- `friend [username]` - Send friend request (e.g., `friend bob`)
- `accept [username]` - Accept friend request (e.g., `accept alice`)
- `msg [friend] [message]` - Send direct message (e.g., `msg bob Hello!`)
- `group [name]` - Create group chat (e.g., `group MyGroup`)
- `gmsg [group_id] [message]` - Send group message (e.g., `gmsg group_123 Hello all!`)
- `search [name]` - Search for users (e.g., `search bob`)
- `online` - Show online friends
- `help` - Show all commands
- `quit` - Exit the application

### Demo Sequence

1. **Start Alice** (first peer):
python examples/peer_instance.py --username alice --port 8888


2. **Start Bob** (connect to Alice):
python examples/peer_instance.py --username bob --port 8889 --connect localhost:8888


3. **Establish Friendship**:
- In Alice: `friend bob`
- In Bob: `accept alice`

4. **Test Messaging**:
- In Alice: `msg bob Hello from Alice!`
- In Bob: `msg alice Hi from Bob!`

5. **Create Group Chat**:
- In Alice: `group OurGroup`
- Copy the group ID and: `gmsg [group_id] Welcome to the group!`


## Technical Details

### P2P Protocol
- **Socket-based Communication**: Raw TCP sockets for direct peer connections
- **JSON Message Format**: Structured messages for different types of communication
- **Connection Pooling**: Maintains multiple simultaneous peer connections
- **Message Routing**: Intelligent message forwarding and delivery

### Message Types
- `TEXT`: Direct text messages between friends
- `FRIEND_REQ`: Friend request management
- `FRIEND_ACC`: Friend request acceptance
- `GROUP_MSG`: Group chat messages
- `GROUP_INVITE`: Group participation invitations
- `PEER_DISCOVERY`: Network peer discovery
- `USER_LOOKUP`: Distributed user location

### Data Storage
Each peer maintains their own SQLite database with:
- User profiles and friend relationships
- Message history and delivery status
- Group chat memberships
- Known peer network information

## Network Architecture

### Bootstrap Mechanism
- First peer acts as initial contact point
- Subsequent peers can connect through any existing peer
- Peer information propagates through the network
- No single point of failure

### True P2P Evidence
1. **Direct Communication**: Messages go directly between users
2. **Decentralized Data**: Each peer has independent data store
3. **Fault Tolerance**: Network survives peer disconnections
4. **Dynamic Discovery**: Peers can join through multiple paths
5. **No Central Control**: No server manages users or messages

## Project Structure
conf-chat/
├── src/ # Core P2P implementation
│ ├── peer.py # Main P2P peer class
│ ├── database.py # Local data storage
│ ├── message.py # Message format handling
│ ├── config.py # Configuration constants
│ └── utils.py # Utility functions
├── examples/
│ └── peer_instance.py # Universal peer instance
├── tests/ # Test suite
│ ├── test_simple.py # Basic functionality tests
│ └── test_decentralized.py # P2P network tests
├── demo_final.py # Comprehensive demonstration
└── README.md # This file


## Implementation Scenario

This implementation presents a simplified yet fully functional P2P chat system that differs from the sample use case in several key ways:

### Key Design Choices:

1. **Simplified User Management**: 
   - No username/password registration system
   - Users identified by unique usernames only
   - Focus on P2P networking rather than authentication

2. **Dynamic Network Formation**:
   - Any peer can serve as bootstrap node
   - No dedicated registration server required
   - Network forms organically as peers connect

3. **Direct Peer Discovery**:
   - Manual connection initiation vs automated discovery
   - Clear demonstration of P2P connection establishment
   - Users explicitly manage their network connections

4. **Real-time Communication Focus**:
   - Immediate message delivery to online users
   - Simplified offline message handling
   - Emphasis on live P2P interaction

5. **Command-Line Interface**:
   - Interactive terminal-based interface
   - Clear demonstration of P2P commands and responses
   - Easy to understand and extend

### Preserved Core P2P Concepts:
- Pure decentralized architecture
- Friend-based communication
- Group chat functionality  
- User discovery and search
- Online status tracking
- No single point of failure

This implementation scenario prioritizes clarity of P2P concepts and ease of demonstration while maintaining all the essential features of a distributed chat system.

## Security Notes

This is a demonstration project focusing on P2P architecture. In a production environment, you would want to add:

- Message encryption
- User authentication
- Digital signatures
- Secure peer verification

## Contributing

This project demonstrates academic P2P concepts. Feel free to extend it with:

- NAT traversal techniques
- DHT-based peer discovery
- Message encryption
- File sharing capabilities
- Mobile client support

## License

Educational demonstration project - feel free to use for learning P2P concepts.

## Questions & Issues

For questions about the P2P implementation or architecture, please review the test files and demo scripts that demonstrate the decentralized nature of the system.

---

**Built for understanding true peer-to-peer networking principles**

## License
This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Portions of this implementation are original work building upon the initial Conf-Chat project structure.