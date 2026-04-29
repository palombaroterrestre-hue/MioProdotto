-- TASK 1: Check alias table state
select canonical_name, count(*) as alias_count
from product_aliases
group by canonical_name
order by alias_count desc
limit 20;