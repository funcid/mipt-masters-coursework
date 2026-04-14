create schema if not exists exts;
create extension if not exists "uuid-ossp" with schema exts;

drop schema if exists tsaryuk_food cascade;
create schema tsaryuk_food;
set search_path to tsaryuk_food, public;

create type common_status as enum ('active', 'inactive', 'blocked');
create type order_status as enum ('created', 'accepted', 'delivering', 'delivered', 'cancelled');
create type pay_status as enum ('unpaid', 'paid', 'refunded');
create type payment_status as enum ('pending', 'success', 'failed');
create type review_entity_type as enum ('product', 'restaurant', 'order');

create table address (
    address_id uuid primary key default exts.uuid_generate_v4(),
    street varchar(100) not null check (length(trim(street)) > 0),
    house_number varchar(10) not null check (length(trim(house_number)) > 0),
    apartment_office varchar(10) not null check (length(trim(apartment_office)) > 0)
);

create table clients (
    client_id uuid primary key default exts.uuid_generate_v4(),
    login varchar(50) not null unique check (length(trim(login)) > 0),
    password varchar(100) not null check (length(trim(password)) > 0),
    phone_number char(11) not null unique check (phone_number ~ '^[0-9]{11}$'),
    fio varchar(120) not null check (length(trim(fio)) > 0)
);

create table courier (
    courier_id uuid primary key default exts.uuid_generate_v4(),
    fio varchar(120) not null check (length(trim(fio)) > 0),
    phone_number char(11) not null unique check (phone_number ~ '^[0-9]{11}$'),
    status common_status not null,
    hire_date date not null,
    dismissal_date date,
    check (dismissal_date is null or dismissal_date >= hire_date)
);

create table product_category (
    product_category_id uuid primary key default exts.uuid_generate_v4(),
    product_category_name varchar(100) not null unique check (length(trim(product_category_name)) > 0)
);

create table restaurant (
    restaurant_id uuid primary key default exts.uuid_generate_v4(),
    restaurant_name varchar(120) not null unique check (length(trim(restaurant_name)) > 0),
    address_id uuid not null references address(address_id),
    description text not null check (length(trim(description)) > 0),
    work_hours varchar(60) not null check (length(trim(work_hours)) > 0),
    company_details text not null check (length(trim(company_details)) > 0),
    rating numeric(3,2) not null default 0 check (rating between 0 and 5),
    status common_status not null
);

create table product (
    product_id uuid primary key default exts.uuid_generate_v4(),
    product_name varchar(120) not null check (length(trim(product_name)) > 0),
    product_category_id uuid not null references product_category(product_category_id),
    price numeric(10,2) not null check (price > 0),
    restaurant_id uuid not null references restaurant(restaurant_id),
    photo_url text not null check (length(trim(photo_url)) > 0),
    rating numeric(3,2) not null default 0 check (rating between 0 and 5),
    status common_status not null,
    description text not null check (length(trim(description)) > 0)
);

create table client_address (
    client_id uuid not null references clients(client_id) on delete cascade,
    address_id uuid not null references address(address_id) on delete cascade,
    primary key (client_id, address_id)
);

create table "order" (
    order_id uuid primary key default exts.uuid_generate_v4(),
    courier_id uuid not null references courier(courier_id),
    client_id uuid not null references clients(client_id),
    address_id uuid not null references address(address_id),
    restaurant_id uuid not null references restaurant(restaurant_id),
    order_timestamp timestamp not null,
    delivery_timestamp timestamp not null,
    order_amount numeric(10,2) not null check (order_amount > 0),
    commission numeric(10,2) not null check (commission >= 0),
    total_amount numeric(10,2) not null check (total_amount >= order_amount),
    rating numeric(3,2) not null default 0 check (rating between 0 and 5),
    status order_status not null,
    pay_status pay_status not null,
    description text not null check (length(trim(description)) > 0),
    check (delivery_timestamp >= order_timestamp)
);

create table order_structure (
    order_id uuid not null references "order"(order_id) on delete cascade,
    product_id uuid not null references product(product_id),
    quantity numeric(8,2) not null check (quantity > 0),
    primary key (order_id, product_id)
);

create table payment (
    payment_id uuid primary key default exts.uuid_generate_v4(),
    payment_transaction text not null unique check (length(trim(payment_transaction)) > 0),
    order_id uuid not null unique references "order"(order_id) on delete cascade,
    status payment_status not null
);

create table review (
    review_id uuid primary key default exts.uuid_generate_v4(),
    client_id uuid not null references clients(client_id),
    review_timestamp timestamp not null,
    entity_id uuid not null,
    entity_type review_entity_type not null,
    order_id uuid references "order"(order_id),
    description text not null check (length(trim(description)) > 0),
    photo_url text not null check (length(trim(photo_url)) > 0),
    rating numeric(2,1) not null check (rating between 1 and 5)
);

create table courier_pay (
    year int not null check (year between 2000 and 2100),
    month int not null check (month between 1 and 12),
    courier_id uuid not null references courier(courier_id) on delete cascade,
    amount numeric(12,2) not null check (amount >= 0),
    primary key (year, month, courier_id)
);

create index ix_order_restaurant on "order"(restaurant_id);
create index ix_order_courier on "order"(courier_id);
create index ix_order_client on "order"(client_id);
create index ix_review_entity on review(entity_type, entity_id);

create or replace function random_text(max_len int, min_len int default 1)
returns text
language plpgsql
as $$
declare
    alphabet constant text := 'abcdefghijklmnopqrstuvwxyz';
    target_len int := greatest(1, least(max_len, floor(random() * (max_len - min_len + 1) + min_len)::int));
    result text := '';
    i int;
begin
    for i in 1..target_len loop
        result := result || substr(alphabet, floor(random() * length(alphabet) + 1)::int, 1);
    end loop;
    return result;
end;
$$;

create or replace function random_phone11()
returns char(11)
language sql
as $$
    select ('79' || lpad(floor(random() * 999999999)::text, 9, '0'))::char(11);
$$;

create or replace procedure insert_test_data(value int)
language plpgsql
security definer
as $$
declare
    i int;
    j int;
    v_client_id uuid;
    v_restaurant_id uuid;
    v_order_id uuid;
    v_address_id uuid;
    v_order_ts timestamp;
    v_order_amount numeric(10,2);
    v_commission numeric(10,2);
    v_month date;
begin
    if value is null or value <= 0 then
        raise exception 'value must be > 0';
    end if;

    for i in 1..(value * 5) loop
        insert into address(street, house_number, apartment_office)
        values (
            random_text(40, 6),
            random_text(10, 1),
            random_text(10, 1)
        );
    end loop;

    for i in 1..value loop
        insert into clients(login, password, phone_number, fio)
        values (
            left(random_text(45, 6) || '_' || floor(random() * 100000)::int, 50),
            random_text(100, 12),
            random_phone11(),
            random_text(30, 8) || ' ' || random_text(30, 8)
        );

        insert into courier(fio, phone_number, status, hire_date, dismissal_date)
        values (
            random_text(30, 8) || ' ' || random_text(30, 8),
            random_phone11(),
            (enum_range(null::common_status))[floor(random() * cardinality(enum_range(null::common_status)) + 1)::int],
            current_date - floor(random() * 180)::int,
            null
        );

        insert into product_category(product_category_name)
        values (random_text(20, 5) || '_' || floor(random() * 10000)::int);

        select address_id
        into v_address_id
        from address
        order by random()
        limit 1;

        insert into restaurant(restaurant_name, address_id, description, work_hours, company_details, status)
        values (
            random_text(40, 6) || '_' || floor(random() * 10000)::int,
            v_address_id,
            random_text(150, 20),
            lpad((8 + floor(random() * 3))::text, 2, '0') || ':00-' || lpad((20 + floor(random() * 4))::text, 2, '0') || ':00',
            random_text(120, 20),
            (enum_range(null::common_status))[floor(random() * cardinality(enum_range(null::common_status)) + 1)::int]
        );
    end loop;

    for i in 1..(value * 5) loop
        insert into product(product_name, product_category_id, price, restaurant_id, photo_url, status, description)
        values (
            random_text(60, 5),
            (select product_category_id from product_category order by random() limit 1),
            round((100 + random() * 1900)::numeric, 2),
            (select restaurant_id from restaurant order by random() limit 1),
            'https://img.local/' || random_text(12, 6),
            (enum_range(null::common_status))[floor(random() * cardinality(enum_range(null::common_status)) + 1)::int],
            random_text(150, 20)
        );

        v_order_ts := current_timestamp - (floor(random() * (180 * 24 * 60))::int * interval '1 minute');
        v_order_amount := round((300 + random() * 2700)::numeric, 2);
        v_commission := round((v_order_amount * (0.08 + random() * 0.12))::numeric, 2);
        select r.restaurant_id
        into v_restaurant_id
        from restaurant r
        where exists (
            select 1
            from product p
            where p.restaurant_id = r.restaurant_id
        )
        order by random()
        limit 1;

        insert into "order"(
            courier_id, client_id, address_id, restaurant_id,
            order_timestamp, delivery_timestamp, order_amount, commission, total_amount,
            status, pay_status, description
        )
        values (
            (select courier_id from courier order by random() limit 1),
            (select client_id from clients order by random() limit 1),
            (select address_id from address order by random() limit 1),
            v_restaurant_id,
            v_order_ts,
            v_order_ts + ((20 + floor(random() * 90))::int * interval '1 minute'),
            v_order_amount,
            v_commission,
            v_order_amount + v_commission,
            (enum_range(null::order_status))[floor(random() * cardinality(enum_range(null::order_status)) + 1)::int],
            (enum_range(null::pay_status))[floor(random() * cardinality(enum_range(null::pay_status)) + 1)::int],
            random_text(120, 10)
        )
        returning order_id, client_id, restaurant_id into v_order_id, v_client_id, v_restaurant_id;

        for j in 1..(1 + floor(random() * 3))::int loop
            insert into order_structure(order_id, product_id, quantity)
            values (
                v_order_id,
                (
                    select p.product_id
                    from product p
                    where p.restaurant_id = v_restaurant_id
                    order by random()
                    limit 1
                ),
                (1 + floor(random() * 4))::numeric
            )
            on conflict (order_id, product_id) do update
            set quantity = order_structure.quantity + excluded.quantity;
        end loop;

        insert into payment(payment_transaction, order_id, status)
        values (
            'tx_' || replace(v_order_id::text, '-', '') || '_' || floor(random() * 1000)::int,
            v_order_id,
            (enum_range(null::payment_status))[floor(random() * cardinality(enum_range(null::payment_status)) + 1)::int]
        );

        insert into review(client_id, review_timestamp, entity_id, entity_type, order_id, description, photo_url, rating)
        values (
            v_client_id,
            v_order_ts + ((60 + floor(random() * 240))::int * interval '1 minute'),
            (
                case floor(random() * 3)::int
                    when 0 then (select product_id from order_structure where order_id = v_order_id order by random() limit 1)
                    when 1 then v_restaurant_id
                    else v_order_id
                end
            ),
            (
                case floor(random() * 3)::int
                    when 0 then 'product'::review_entity_type
                    when 1 then 'restaurant'::review_entity_type
                    else 'order'::review_entity_type
                end
            ),
            v_order_id,
            random_text(120, 20),
            'https://img.local/review_' || random_text(10, 5),
            round((1 + random() * 4)::numeric, 1)
        );
    end loop;

    insert into client_address(client_id, address_id)
    select c.client_id, a.address_id
    from clients c
    cross join lateral (
        select address_id from address order by random() limit 1
    ) a
    on conflict do nothing;

    for v_month in
        select date_trunc('month', current_date)::date - (s * interval '1 month')
        from generate_series(0, 5) s
    loop
        insert into courier_pay(year, month, courier_id, amount)
        select
            extract(year from v_month)::int,
            extract(month from v_month)::int,
            c.courier_id,
            round(
                (
                    count(o.order_id) * 140
                    + sum(coalesce(o.order_amount, 0)) * 0.03
                )::numeric,
                2
            ) as amount
        from courier c
        left join "order" o
            on o.courier_id = c.courier_id
            and date_trunc('month', o.delivery_timestamp) = date_trunc('month', v_month)
            and o.status = 'delivered'
        group by c.courier_id
        on conflict (year, month, courier_id) do update
        set amount = excluded.amount;
    end loop;
end;
$$;

create or replace procedure erase_test_data()
language plpgsql
security definer
as $$
begin
    delete from review;
    delete from payment;
    delete from order_structure;
    delete from client_address;
    delete from courier_pay;
    delete from "order";
    delete from product;
    delete from restaurant;
    delete from product_category;
    delete from courier;
    delete from clients;
    delete from address;
end;
$$;

create or replace function rating_change()
returns trigger
language plpgsql
as $$
declare
    v_entity_id uuid;
    v_entity_type review_entity_type;
begin
    v_entity_id := coalesce(new.entity_id, old.entity_id);
    v_entity_type := coalesce(new.entity_type, old.entity_type);

    if v_entity_type = 'product' then
        update product p
        set rating = coalesce((
            select round(avg(r.rating)::numeric, 2)
            from review r
            where r.entity_type = 'product'
              and r.entity_id = p.product_id
        ), 0)
        where p.product_id = v_entity_id;
    elsif v_entity_type = 'restaurant' then
        update restaurant rs
        set rating = coalesce((
            select round(avg(r.rating)::numeric, 2)
            from review r
            where r.entity_type = 'restaurant'
              and r.entity_id = rs.restaurant_id
        ), 0)
        where rs.restaurant_id = v_entity_id;
    elsif v_entity_type = 'order' then
        update "order" o
        set rating = coalesce((
            select round(avg(r.rating)::numeric, 2)
            from review r
            where r.entity_type = 'order'
              and r.entity_id = o.order_id
        ), 0)
        where o.order_id = v_entity_id;
    end if;

    return coalesce(new, old);
end;
$$;

drop trigger if exists trg_rating_change on review;
create trigger trg_rating_change
after insert or update or delete on review
for each row
execute function rating_change();

create or replace function get_statistic()
returns table(
    restaurant_name varchar,
    best_product_name varchar,
    total_amount numeric,
    avg_amount numeric,
    best_user varchar
)
language sql
as $$
    with base as (
        select
            r.restaurant_id,
            r.restaurant_name,
            o.order_id,
            o.client_id,
            o.total_amount
        from restaurant r
        left join "order" o on o.restaurant_id = r.restaurant_id
    ),
    best_product as (
        select
            b.restaurant_id,
            (
                select p.product_name
                from "order" o2
                join order_structure os on os.order_id = o2.order_id
                join product p on p.product_id = os.product_id
                where o2.restaurant_id = b.restaurant_id
                group by p.product_id, p.product_name
                order by sum(os.quantity) desc, random()
                limit 1
            ) as best_product_name
        from (select distinct restaurant_id from base) b
    ),
    best_client as (
        select
            b.restaurant_id,
            (
                select c.fio
                from "order" o3
                join clients c on c.client_id = o3.client_id
                where o3.restaurant_id = b.restaurant_id
                group by c.client_id, c.fio
                order by count(*) desc, random()
                limit 1
            ) as best_user
        from (select distinct restaurant_id from base) b
    )
    select
        r.restaurant_name,
        bp.best_product_name,
        coalesce(sum(b.total_amount), 0)::numeric(12,2) as total_amount,
        coalesce(avg(b.total_amount), 0)::numeric(12,2) as avg_amount,
        bc.best_user
    from restaurant r
    left join base b on b.restaurant_id = r.restaurant_id
    left join best_product bp on bp.restaurant_id = r.restaurant_id
    left join best_client bc on bc.restaurant_id = r.restaurant_id
    group by r.restaurant_id, r.restaurant_name, bp.best_product_name, bc.best_user;
$$;

create or replace procedure add_product(
    p_product_name varchar(120),
    p_product_category_id uuid,
    p_price numeric(10,2),
    p_restaurant_id uuid,
    p_photo_url text,
    p_rating numeric(3,2),
    p_status common_status,
    p_description text
)
language plpgsql
security definer
as $$
begin
    insert into product(
        product_name,
        product_category_id,
        price,
        restaurant_id,
        photo_url,
        rating,
        status,
        description
    )
    values(
        p_product_name,
        p_product_category_id,
        p_price,
        p_restaurant_id,
        p_photo_url,
        p_rating,
        p_status,
        p_description
    );
end;
$$;

create or replace procedure courier_salary()
language plpgsql
security definer
as $$
declare
    v_calc_month date := date_trunc('month', current_date) - interval '1 month';
begin
    insert into courier_pay(year, month, courier_id, amount)
    select
        extract(year from v_calc_month)::int,
        extract(month from v_calc_month)::int,
        c.courier_id,
        round(
            (
                count(o.order_id) * 150
                + sum(coalesce(o.order_amount, 0)) *
                    case
                        when count(o.order_id) >= 80 then 0.07
                        when count(o.order_id) >= 40 then 0.05
                        else 0.03
                    end
            )::numeric,
            2
        ) as amount
    from courier c
    left join "order" o
        on o.courier_id = c.courier_id
        and date_trunc('month', o.delivery_timestamp) = date_trunc('month', v_calc_month)
        and o.status = 'delivered'
    group by c.courier_id
    on conflict (year, month, courier_id) do update
    set amount = excluded.amount;
end;
$$;

create or replace view how_much_money as
with recursive monthly as (
    select
        extract(year from o.order_timestamp)::int as year,
        extract(month from o.order_timestamp)::int as month,
        sum(o.order_amount)::numeric(14,2) as amount_without_commission,
        sum(o.total_amount)::numeric(14,2) as amount_with_commission,
        sum(o.commission)::numeric(14,2) as commission_amount,
        coalesce(cp.courier_amount, 0)::numeric(14,2) as courier_amount
    from "order" o
    left join (
        select year, month, sum(amount) as courier_amount
        from courier_pay
        group by year, month
    ) cp on cp.year = extract(year from o.order_timestamp)::int
        and cp.month = extract(month from o.order_timestamp)::int
    group by extract(year from o.order_timestamp), extract(month from o.order_timestamp), cp.courier_amount
),
ordered as (
    select
        m.*,
        row_number() over (order by m.year, m.month) as rn
    from monthly m
),
recursive_report as (
    select
        o.rn,
        o.year,
        o.month,
        o.amount_without_commission,
        o.amount_with_commission,
        o.commission_amount,
        0::numeric(14,2) as prev_commission,
        o.commission_amount::numeric(14,2) as commission_diff,
        o.courier_amount,
        (o.commission_amount - o.courier_amount)::numeric(14,2) as net_profit
    from ordered o
    where o.rn = 1

    union all

    select
        o.rn,
        o.year,
        o.month,
        o.amount_without_commission,
        o.amount_with_commission,
        o.commission_amount,
        rr.commission_amount as prev_commission,
        (o.commission_amount - rr.commission_amount)::numeric(14,2) as commission_diff,
        o.courier_amount,
        (o.commission_amount - o.courier_amount)::numeric(14,2) as net_profit
    from recursive_report rr
    join ordered o on o.rn = rr.rn + 1
)
select
    year,
    month,
    amount_without_commission,
    amount_with_commission,
    commission_amount,
    prev_commission,
    commission_diff,
    courier_amount,
    net_profit
from recursive_report
order by year, month;

do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'reviewer') then
        create role reviewer login password 'NetoSQL2026';
    end if;
    if not exists (select 1 from pg_roles where rolname = 'inspector') then
        create role inspector login password 'NetoSQL2026';
    end if;
end
$$;

grant usage on schema tsaryuk_food to reviewer;
grant select, insert, update, delete on all tables in schema tsaryuk_food to reviewer;
grant usage, select on all sequences in schema tsaryuk_food to reviewer;
grant execute on all functions in schema tsaryuk_food to reviewer;
grant execute on all procedures in schema tsaryuk_food to reviewer;
alter default privileges in schema tsaryuk_food grant select, insert, update, delete on tables to reviewer;
alter default privileges in schema tsaryuk_food grant usage, select on sequences to reviewer;
alter default privileges in schema tsaryuk_food grant execute on functions to reviewer;

grant usage on schema exts to reviewer;
grant execute on function exts.uuid_generate_v4() to reviewer;

grant usage on schema pg_catalog to reviewer;
grant select on all tables in schema pg_catalog to reviewer;
grant usage on schema information_schema to reviewer;
grant select on all tables in schema information_schema to reviewer;

grant usage on schema tsaryuk_food to inspector;
grant select on all tables in schema tsaryuk_food to inspector;
grant usage, select on all sequences in schema tsaryuk_food to inspector;
grant execute on all functions in schema tsaryuk_food to inspector;
grant execute on all procedures in schema tsaryuk_food to inspector;
alter default privileges in schema tsaryuk_food grant select on tables to inspector;
alter default privileges in schema tsaryuk_food grant usage, select on sequences to inspector;
alter default privileges in schema tsaryuk_food grant execute on functions to inspector;
grant usage on schema exts to inspector;
grant execute on function exts.uuid_generate_v4() to inspector;
grant usage on schema pg_catalog to inspector;
grant select on all tables in schema pg_catalog to inspector;
grant usage on schema information_schema to inspector;
grant select on all tables in schema information_schema to inspector;
