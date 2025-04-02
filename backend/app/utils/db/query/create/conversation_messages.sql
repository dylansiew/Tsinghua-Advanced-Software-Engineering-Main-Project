CREATE TABLE IF NOT EXISTS conversation_messages (
    conversation_id VARCHAR(150),
    created_at TIMESTAMP,
    message_role VARCHAR(20),
    message_content TEXT,
    PRIMARY KEY (conversation_id, message_role, created_at)
);