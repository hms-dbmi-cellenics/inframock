-- To re run these files on next inframock start: "docker rm -f -v biomage-inframock-postgres"

CREATE DATABASE aurora_db;

\c aurora_db;

-- The role used by the api & develop
CREATE ROLE api_role WITH LOGIN;
CREATE ROLE dev_role WITH LOGIN;
GRANT USAGE ON SCHEMA public TO api_role;
-- RDS doesnt allow master user some things, so we need to
-- grant and later revoke dev_role from postgres to move its privileges
GRANT dev_role TO postgres;
ALTER DEFAULT PRIVILEGES FOR USER dev_role IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO api_role;
REVOKE dev_role FROM postgres;
GRANT postgres TO dev_role;