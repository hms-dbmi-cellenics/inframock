-- To re run these files on next inframock start: "docker rm -f -v biomage-inframock-postgres"

CREATE DATABASE aurora_db;

\c aurora_db;

-- The role used by the api
CREATE ROLE api_role WITH LOGIN PASSWORD 'password';

GRANT USAGE ON SCHEMA public TO api_role;

-- Gives these privileges to api_role on any table that we create in public
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO api_role;

-- This isn't where we are going to create the tables and run the migrations
-- It should be done be in the python code once we have defined a mechanism for running migrations
CREATE TABLE "experiment" (
  "id" UUID,
  "name" VARCHAR,
  "description" VARCHAR,
  "processing_config" JSONB,
  "created_at" TIMESTAMP,
  "updated_at" TIMESTAMP,
  "notify_by_email" BOOLEAN,
  PRIMARY KEY ("id")
);

