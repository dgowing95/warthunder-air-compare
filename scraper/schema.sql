CREATE TABLE IF NOT EXISTS aircraft (
    slug                TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    image_url           TEXT,
    nation              TEXT,
    rank                TEXT,
    br_rb               REAL,
    max_speed_min       REAL,
    max_speed_max       REAL,
    max_speed_alt       REAL,
    turn_time_min       REAL,
    turn_time_max       REAL,
    climb_rate_min      REAL,
    climb_rate_max      REAL,
    max_altitude        REAL,
    wing_loading        REAL,
    takeoff_run         REAL,
    crew                INTEGER,
    armament            TEXT,
    suspended_armament  TEXT,
    countermeasures     TEXT,
    last_scraped        TEXT,
    raw                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_aircraft_name ON aircraft (name);

CREATE TABLE IF NOT EXISTS scrape_state (
    slug          TEXT PRIMARY KEY,
    discovered_at TEXT,
    last_attempt  TEXT,
    last_success  TEXT,
    status        TEXT,
    error         TEXT
);
