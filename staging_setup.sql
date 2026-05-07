alter table staging_products enable row level security;

create policy "Allow read staging" on staging_products for select using (true);

create policy "Allow insert staging" on staging_products for insert with check (true);

create policy "Allow update staging" on staging_products for update using (true);

create policy "Allow delete staging" on staging_products for delete using (true);

create index if not exists idx_staging_status on staging_products(status);

create index if not exists idx_staging_fonte on staging_products(fonte_volantino_link);