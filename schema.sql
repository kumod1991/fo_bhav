create table if not exists fut_bhav_copy (
  trade_date       date    not null,
  instrument_type  text    not null,   -- STF / IDF
  symbol           text    not null,
  expiry_date      date    not null,
  open             numeric,
  high             numeric,
  low              numeric,
  close            numeric,
  last_price       numeric,
  prev_close       numeric,
  settle_price     numeric,
  underlying_price numeric,
  open_interest    bigint,
  chg_in_oi        bigint,
  volume           bigint,             -- contracts
  turnover         numeric,            -- INR (TtlTrfVal)
  trades           bigint,
  lot_size         int,
  primary key (trade_date, instrument_type, symbol, expiry_date)
);

create index if not exists fut_bhav_copy_symbol_date_idx
  on fut_bhav_copy (symbol, trade_date desc);

alter table fut_bhav_copy enable row level security;

drop policy if exists "public read" on fut_bhav_copy;
create policy "public read" on fut_bhav_copy for select using (true);
