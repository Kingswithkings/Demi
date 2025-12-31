CREATE TABLE IF NOT EXISTS action_logs (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  user_id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  channel TEXT NOT NULL,

  action_type TEXT NOT NULL,              -- schedule_meeting, cancel_meeting, etc.
  action_payload TEXT NOT NULL,           -- JSON
  confirmation_status TEXT NOT NULL,      -- awaiting_confirmation | confirmed | rejected
  executed INTEGER NOT NULL DEFAULT 0,    -- 0/1
  execution_result TEXT                   -- JSON or error string
);

CREATE TABLE IF NOT EXISTS pending_actions (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  user_id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  channel TEXT NOT NULL,

  action_type TEXT NOT NULL,
  action_payload TEXT NOT NULL,           -- JSON
  status TEXT NOT NULL                    -- awaiting_confirmation
);
