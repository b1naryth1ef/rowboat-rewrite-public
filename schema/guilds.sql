CREATE TABLE IF NOT EXISTS guilds (
  guild_id BIGINT NOT NULL,
  owner_id BIGINT NOT NULL,
  config_id UUID,
  name TEXT,

  -- Web Permissions
  web_viewers BIGINT[],
  web_editors BIGINT[],
  web_admins BIGINT[],

  -- Stats
  member_count INTEGER,
  channel_count INTEGER,
  role_count INTEGER,
  emoji_count INTEGER,

  PRIMARY KEY (guild_id)
);

CREATE TABLE IF NOT EXISTS guild_configs (
  config_id UUID NOT NULL,
  guild_id BIGINT NOT NULL,
  raw_content TEXT,
  config JSONB,

  PRIMARY KEY (guild_id, config_id)
);

CREATE TABLE IF NOT EXISTS guild_infractions (
  infraction_id BIGINT NOT NULL,

  guild_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  actor_id BIGINT NOT NULL,

  action INTEGER NOT NULL,
  reason TEXT,
  metadata JSONB,

  expires_at TIMESTAMP WITHOUT TIMEZONE,
  created_at TIMESTAMP WITHOUT TIMEZONE,

  deleted BOOLEAN,

  PRIMARY KEY (guild_id, infraction_id)
);

SELECT create_distributed_table('guilds', 'guild_id');
SELECT create_distributed_table('guild_configs', 'guild_id', colocate_with => 'guilds');
SELECT create_distributed_table('guild_infractions', 'guild_id', colocate_with => 'guilds');
