alter table dedup_feedback enable row level security;

create policy "Allow read dedup_feedback" on dedup_feedback for select using (true);

create policy "Allow insert dedup_feedback" on dedup_feedback for insert with check (true);