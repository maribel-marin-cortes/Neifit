-- Ejecutar después de 0005. No modifica pedidos ni datos existentes.
begin;
create table if not exists public.customer_addresses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  label text not null check(length(trim(label)) between 2 and 50),
  address text not null check(length(trim(address)) between 5 and 300),
  city text not null check(length(trim(city)) between 3 and 100),
  recipient text not null check(length(trim(recipient)) between 3 and 100),
  phone text not null check(length(trim(phone)) between 7 and 30),
  notes text not null default '' check(length(notes)<=500),
  created_at timestamptz not null default now()
);
create index if not exists customer_addresses_owner on public.customer_addresses(user_id);
alter table public.customer_addresses enable row level security;
revoke all on public.customer_addresses from public, anon, authenticated;
grant select on public.customer_addresses to authenticated;
grant select,insert,update,delete on public.customer_addresses to service_role;
drop policy if exists addresses_read_self on public.customer_addresses;
create policy addresses_read_self on public.customer_addresses for select to authenticated
using(user_id=(select auth.uid()) and public.neifit_has_permission('profile.read'));
notify pgrst,'reload schema';
commit;
