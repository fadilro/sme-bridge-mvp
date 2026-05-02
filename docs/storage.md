# Storage Architecture

The SME Bridge platform manages raw user uploads (such as PDF utility bills) securely and reliably.

## Environments

### Local Testing (LocalStorageService)
In testing and local development, files are saved locally. 
- By default, files are saved to `.data/storage/utility-bills/raw/`.
- The storage implementation ensures that traversal attacks (e.g. `../../../`) are aggressively blocked.
- Filenames are sanitized to prevent operating system injection.

### Production (SupabaseStorageService)
In production environments, we use Supabase Storage to store files durably.
- **Bucket:** Configured via `SUPABASE_STORAGE_BUCKET`.
- **Path Convention:** `utility-bills/raw/{sme_id}/{bill_id}/{safe_filename}`
- Uploads are mapped accurately via the `supabase-py` SDK utilizing the application's injected client instance.

## Path Conventions
To ensure all bill artifacts are globally unique and cleanly scoped per-tenant, we inject the `sme_id` and the `bill_id` directly into the path hierarchy before the file name.
