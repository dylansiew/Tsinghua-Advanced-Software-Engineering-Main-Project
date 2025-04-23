SELECT *
FROM conversation_messages
WHERE conversation_id = ?
ORDER BY created_at ASC;