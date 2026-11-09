# fut-bhav

Loads NSE futures bhavcopy (UDiFF) into Supabase table `fut_bhav_copy`.

1. Run `schema.sql` in the Supabase SQL editor.
2. Add repo secrets `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`.
3. Backfill: Actions -> "Futures bhavcopy -> Supabase" -> Run workflow, start `2024-07-08`.
4. Daily run is automatic (Mon-Fri, 19:00 IST).

Local: `pip install requests && python fetch_fut_bhav.py 2026-11-06`
