--
-- Drop all tables (if they exist)
--
DROP TABLE IF EXISTS benchmark_run;
DROP TABLE IF EXISTS team_member;
DROP TABLE IF EXISTS team;
DROP TABLE IF EXISTS benchmark;
DROP TABLE IF EXISTS password_request;
DROP TABLE IF EXISTS user_key;
DROP TABLE IF EXISTS registered_user;

--
-- Each registered user has a unique internal identifier and a unique user name
--
CREATE TABLE registered_user(
    id CHAR(32) NOT NULL,
    email VARCHAR(255) NOT NULL,
    secret VARCHAR(255) NOT NULL,
    active INTEGER NOT NULL,
    PRIMARY KEY(id),
    UNIQUE(email)
);

--
-- Maintain API keys for users that are currently logged in
--
CREATE TABLE user_key(
    user_id CHAR(32) NOT NULL REFERENCES registered_user (id),
    api_key CHAR(32) NOT NULL,
    expires CHAR(26) NOT NULL,
    PRIMARY KEY(user_id),
    UNIQUE (api_key)
);

--
-- Manage requests to reset a user password.
--
CREATE TABLE password_request(
    user_id CHAR(32) NOT NULL REFERENCES registered_user (id),
    request_id CHAR(32) NOT NULL,
    expires CHAR(26) NOT NULL,
    PRIMARY KEY(user_id),
    UNIQUE (request_id)
);

--
-- Each benchmark has a unique name, a short descriptor and a set of
-- instructions.
--
CREATE TABLE benchmark(
    id CHAR(32) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    instructions TEXT,
    PRIMARY KEY(id),
    UNIQUE(name)
);

--
-- Benchmark runs maintain the run status and timestamps
--
CREATE TABLE benchmark_run(
    run_id CHAR(32) NOT NULL,
    benchmark_id CHAR(32) NOT NULL,
    user_id CHAR(32) NOT NULL,
    state VARCHAR(8) NOT NULL,
    started_at CHAR(26) NOT NULL,
    finished_at CHAR(26) NOT NULL,
    PRIMARY KEY(run_id)
);

--
-- Each team has a unique identifier and a unique name. All identifiers are
-- expected to be created using the benchtmpl.util.core.get_unique_identifier
-- method which returns string of 32 characters.
--
CREATE TABLE team(
    id CHAR(32) NOT NULL,
    name VARCHAR(255) NOT NULL,
    owner_id CHAR(32) NOT NULL REFERENCES registered_user (id),
    PRIMARY KEY(id),
    UNIQUE(name)
);

--
-- Mapping of users to teams
--
CREATE TABLE team_member(
    team_id CHAR(32) NOT NULL REFERENCES team (id),
    user_id CHAR(32) NOT NULL REFERENCES registered_user (id),
    PRIMARY KEY(team_id, user_id)
);
