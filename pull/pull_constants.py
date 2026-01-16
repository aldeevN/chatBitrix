"""
Constants for Bitrix Pull client
"""

# Constants from JavaScript client
REVISION = 19
JSON_RPC_VERSION = "2.0"
JSON_RPC_PING = "ping"
JSON_RPC_PONG = "pong"

class PullStatus:
    Offline = 'offline'
    Online = 'online'
    Connecting = 'connect'

class CloseReasons:
    NORMAL_CLOSURE = 1000
    SERVER_DIE = 1001
    CONFIG_REPLACED = 3000
    CHANNEL_EXPIRED = 3001
    SERVER_RESTARTED = 3002
    CONFIG_EXPIRED = 3003
    MANUAL = 3004
    STUCK = 3005
    WRONG_CHANNEL_ID = 4010

class ConnectionType:
    WebSocket = 'webSocket'
    LongPolling = 'longPolling'

class SenderType:
    Unknown = 0
    Client = 1
    Backend = 2