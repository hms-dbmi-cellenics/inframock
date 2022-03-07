-- To re run these files on next inframock start: "docker rm -f -v biomage-inframock-postgres"

CREATE DATABASE aurora_db;

\c aurora_db;

-- The role used by the api & develop
CREATE ROLE api_role WITH LOGIN PASSWORD 'password';
CREATE ROLE dev_role WITH LOGIN PASSWORD 'password';

GRANT USAGE ON SCHEMA public TO api_role;
GRANT USAGE ON SCHEMA public TO dev_role;

-- Gives these privileges to api_role on any table that we create in public
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO api_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO dev_role;