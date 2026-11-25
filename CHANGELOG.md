# Changelog

All notable changes to Airfinder. Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). Versions use `MAJOR.MINOR.PATCH`.

## [Unreleased]

### Added
- README, LICENSE, SECURITY.md, PR template, CI workflow and Dependabot config (project standard).
- `.env.example` now lists all 21 settings: the 12 that were missing (revenue `DEFAULT_*`, `QUOTE_ENFORCE`, mail server, `PORT`, `ALLOWED_ORIGINS`, `TRUSTED_PROXY_COUNT`, `RATELIMIT_STORAGE_URI`) are added commented out with their defaults. `backend/tests/test_env_example.py` fails when the code reads a setting that is not listed, or one is listed that the code no longer reads.

Earlier history is in the git log. The first tagged release will be `v0.1.0`.
