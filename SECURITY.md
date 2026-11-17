# Security policy

## Reporting a problem

Please do not open a public issue for a security problem. Email **info@facyke.com** with what you found and where, how to reproduce it, and what an attacker could do with it. You will get a first reply within 5 working days.

## Running it safely

- Set long random values for `SECRET_KEY` and `JWT_SECRET`, and a strong `SUPER_ADMIN_PASSWORD`. Never commit `.env`.
- Run behind HTTPS and set `TRUSTED_PROXY_COUNT` to the number of reverse proxies in front of the app.
- Do not use the built-in mock flight data as if it were real availability or pricing.

## Supported versions

Only `main` receives fixes.
