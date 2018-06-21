CREATE TABLE IF NOT EXISTS messages (
  message_id BIGINT NOT NULL,
  guild_id BIGINT NOT NULL,
  channel_id BIGINT NOT NULL,
  author_id BIGINT NOT NULL,

  content TEXT NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  edited_timestamp TIMESTAMP,
  edit_count INTEGER NOT NULL,
  deleted BOOLEAN NOT NULL,

  mentions BIGINT[] NOT NULL,
  emojis BIGINT[] NOT NULL,
  attachments TEXT[] NOT NULL,
  embeds JSONB NOT NULL,
  metadata JSONB NOT NULL,

  PRIMARY KEY (message_id, channel_id)
);

CREATE TABLE IF NOT EXISTS reactions (
  message_id BIGINT NOT NULL,
  channel_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  emoji_id BIGINT,
  emoji_name TEXT,

  PRIMARY KEY (message_id, channel_id, user_id, emoji_id, emoji_name)
);


SELECT create_distributed_table('messages', 'channel_id');
SELECT create_distributed_table('reactions', 'channel_id');
