-- On creation we are connected to development
CREATE DATABASE development;

\c development;

REVOKE ALL ON DATABASE development FROM public;

-- The role used by the api
CREATE ROLE read_write_role WITH LOGIN PASSWORD 'password';

GRANT CONNECT ON DATABASE development TO read_write_role;

GRANT USAGE ON SCHEMA public TO read_write_role;

-- Gives these privileges to read_write_role on any table that we create in public
ALTER DEFAULT PRIVILEGES 
  FOR ROLE read_write_role
  IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO read_write_role;

-- Tables
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

