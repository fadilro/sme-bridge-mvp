from pathlib import Path

def test_migration_file_exists() -> None:
    migration_path = Path("app/db/migrations/001_initial_schema.sql")
    assert migration_path.exists(), "Migration file does not exist at expected path"

def test_migration_content() -> None:
    migration_path = Path("app/db/migrations/001_initial_schema.sql")
    content = migration_path.read_text()

    # Verify tables
    assert "CREATE TABLE plcs" in content
    assert "CREATE TABLE smes" in content
    assert "CREATE TABLE authorized_emails" in content
    assert "CREATE TABLE utility_bills" in content

    # Verify extensions
    assert "CREATE EXTENSION IF NOT EXISTS pgcrypto" in content
    assert "CREATE EXTENSION IF NOT EXISTS citext" in content

    # Verify check constraint
    assert "'pending'" in content
    assert "'success'" in content
    assert "'flagged_low_confidence'" in content
    assert "'flagged_unreadable'" in content
    assert "'resolved_by_client'" in content

    # Verify indexes
    assert "idx_smes_plc_id" in content
    assert "idx_authorized_emails_email_address" in content
    assert "idx_utility_bills_sme_id" in content
    assert "idx_utility_bills_status" in content
    assert "idx_utility_bills_updated_at" in content

    # Verify triggers
    assert "CREATE OR REPLACE FUNCTION set_updated_at()" in content
    assert "EXECUTE PROCEDURE set_updated_at()" in content
