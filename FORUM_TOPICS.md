# Forum Topic Message Filtering

## Overview

The Telegram MCP server now supports filtering messages by forum topic in supergroups that have the forum feature enabled.

## How It Works

In Telegram forums:
- Each topic has a unique ID
- The **General topic** always has ID `1` and is special - its messages don't have a reply_to reference
- Other topics have messages that reference the topic's root message ID via `reply_to.reply_to_top_id`

## Usage

### 1. List Available Topics

First, discover topics in a forum-enabled supergroup:

```python
list_topics(chat_id=-1001234567890)
```

Output example:
```
Topic ID: 1 | Title: General | Messages: 150 | Unread: 5
Topic ID: 42 | Title: Patreon Events | Messages: 89 | Unread: 12
Topic ID: 99 | Title: Announcements | Messages: 25 | Unread: 0
```

### 2. Filter Messages by Topic

Use the `topic_id` parameter with `list_messages` or `get_history`:

```python
# Get messages from General topic
list_messages(chat_id=-1001234567890, topic_id=1, limit=20)

# Get messages from a specific topic
list_messages(chat_id=-1001234567890, topic_id=42, limit=20)

# Also works with get_history
get_history(chat_id=-1001234567890, topic_id=99, limit=50)
```

### 3. Combine with Other Filters

Topic filtering works alongside other filters:

```python
# Search within a specific topic
list_messages(
    chat_id=-1001234567890,
    topic_id=42,
    search_query="event",
    limit=20
)

# Filter by date range in a topic
list_messages(
    chat_id=-1001234567890,
    topic_id=1,
    from_date="2026-01-01",
    to_date="2026-01-31",
    limit=50
)
```

## Technical Details

### General Topic (ID=1)
- Messages in the General topic have no `reply_to` reference or `reply_to.reply_to_top_id`
- The implementation fetches messages and filters out those belonging to other topics
- May retrieve up to `limit * 2` messages to ensure enough General messages are found

### Other Topics
- Uses Telethon's `reply_to` parameter in `get_messages()`
- Maps to Telegram's `GetRepliesRequest` API under the hood
- More efficient as filtering happens server-side

## Example Workflow

```python
# 1. Find the chat
list_chats(chat_type="group")

# 2. Check if forum-enabled and list topics
list_topics(chat_id=-1001234567890)

# 3. Read messages from specific topic
list_messages(chat_id=-1001234567890, topic_id=42, limit=20)

# 4. Reply to a topic (use topic ID as message_id)
reply_to_message(
    chat_id=-1001234567890,
    message_id=42,  # Topic ID
    text="This message will appear in the topic"
)
```

## References

- [Telethon iter_messages documentation](https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.messages.MessageMethods.iter_messages)
- [Telegram API: channels.getForumTopics](https://core.telegram.org/method/channels.getForumTopics)
- [Related Telethon issue #4675](https://github.com/LonamiWebs/Telethon/issues/4675)
