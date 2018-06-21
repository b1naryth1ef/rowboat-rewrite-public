CREATE TABLE IF NOT EXISTS users (
  user_id BIGINT NOT NULL,
  username TEXT NOT NULL,
  discriminator SMALLINT NOT NULL,
  avatar TEXT,
  bot BOOLEAN NOT NULL,
  admin BOOLEAN NOT NULL,

  PRIMARY KEY (user_id)
);

SELECT create_distributed_table('users', 'user_id');
