-- Ejecutar una vez en SQL Editor si ya instalaste neifit_inicial.sql.
-- No reinstalar el esquema ni borrar datos.
-- La landing recibe una muestra controlada desde FastAPI /site/featured-products.
begin;
revoke select on table public.products from anon;
alter policy products_public on public.products to authenticated;
commit;

select has_table_privilege('anon','public.products','SELECT') as anon_puede_leer_catalogo;
-- Debe devolver false. El contenido institucional sigue siendo público.
