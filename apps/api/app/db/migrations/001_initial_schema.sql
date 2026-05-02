-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

-- Create shared updated_at trigger function
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Table: plcs
CREATE TABLE plcs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER plcs_updated_at
BEFORE UPDATE ON plcs
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

-- Table: smes
CREATE TABLE smes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plc_id UUID NOT NULL REFERENCES plcs(id) ON DELETE CASCADE,
    company_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_smes_plc_id ON smes(plc_id);

CREATE TRIGGER smes_updated_at
BEFORE UPDATE ON smes
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

-- Table: authorized_emails
CREATE TABLE authorized_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sme_id UUID NOT NULL REFERENCES smes(id) ON DELETE CASCADE,
    email_address CITEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_authorized_emails_email_address ON authorized_emails(email_address);

CREATE TRIGGER authorized_emails_updated_at
BEFORE UPDATE ON authorized_emails
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

-- Table: utility_bills
CREATE TABLE utility_bills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sme_id UUID NOT NULL REFERENCES smes(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    raw_file_url TEXT NOT NULL,
    original_filename TEXT,
    extracted_provider TEXT,
    extracted_period TEXT,
    extracted_usage NUMERIC,
    extracted_usage_unit TEXT,
    calculated_co2e NUMERIC,
    emission_factor_used NUMERIC,
    reviewer_id UUID,
    validation_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_status CHECK (
        status IN (
            'pending',
            'success',
            'flagged_low_confidence',
            'flagged_unreadable',
            'resolved_by_client'
        )
    )
);

CREATE INDEX idx_utility_bills_sme_id ON utility_bills(sme_id);
CREATE INDEX idx_utility_bills_status ON utility_bills(status);
CREATE INDEX idx_utility_bills_updated_at ON utility_bills(updated_at);

CREATE TRIGGER utility_bills_updated_at
BEFORE UPDATE ON utility_bills
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();
