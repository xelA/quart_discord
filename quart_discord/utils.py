from datetime import datetime

DISCORD_EPOCH = 1420070400000


def parse_time(timestamp: str):
    if not timestamp:
        return None
    return datetime.fromisoformat(timestamp)


def snowflake_time(id: int):
    timestamp = ((id >> 22) + DISCORD_EPOCH) / 1000
    return datetime.utcfromtimestamp(timestamp)
