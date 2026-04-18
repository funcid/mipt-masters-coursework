create schema if not exists exts;
create extension if not exists "uuid-ossp" with schema exts;

drop schema if exists tsaryuk_food cascade;
create schema tsaryuk_food;
set search_path to tsaryuk_food, public;

create type common_status as enum ('активен', 'неактивен', 'заблокирован');
create type order_status as enum ('создан', 'принят', 'в_доставке', 'доставлен', 'отменён');
create type pay_status as enum ('не_оплачен', 'оплачен', 'возврат');
create type payment_status as enum ('в_обработке', 'успешно', 'ошибка');
create type payment_method as enum ('банковская_карта', 'наличные', 'сбп');
create type review_entity_type as enum ('блюдо', 'заведение', 'заказ');

create table address (
    address_id uuid primary key default exts.uuid_generate_v4(),
    street varchar(100) not null check (length(trim(street)) > 0),
    house_number varchar(10) not null check (length(trim(house_number)) > 0),
    apartment_office varchar(10) null check (apartment_office is null or length(trim(apartment_office)) > 0)
);

create table clients (
    client_id uuid primary key default exts.uuid_generate_v4(),
    login varchar(50) not null unique check (length(trim(login)) > 0),
    password varchar(100) not null check (length(trim(password)) > 0),
    phone_number char(11) not null unique check (phone_number ~ '^7[0-9]{10}$'),
    last_name varchar(60) not null check (length(trim(last_name)) > 0),
    first_name varchar(60) not null check (length(trim(first_name)) > 0),
    middle_name varchar(60) null check (middle_name is null or length(trim(middle_name)) > 0)
);

create table courier (
    courier_id uuid primary key default exts.uuid_generate_v4(),
    last_name varchar(60) not null check (length(trim(last_name)) > 0),
    first_name varchar(60) not null check (length(trim(first_name)) > 0),
    middle_name varchar(60) null check (middle_name is null or length(trim(middle_name)) > 0),
    phone_number char(11) not null unique check (phone_number ~ '^7[0-9]{10}$'),
    status common_status not null,
    hire_date date not null,
    dismissal_date date null,
    delivery_rate_percent numeric(6,4) not null default 0.0300
        check (delivery_rate_percent > 0 and delivery_rate_percent <= 1),
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
    description text null check (description is null or length(trim(description)) > 0),
    rating numeric(3,2) not null default 0 check (rating between 0 and 5),
    status common_status not null
);

create table restaurant_work_hours (
    restaurant_id uuid not null references restaurant(restaurant_id) on delete cascade,
    weekday smallint not null check (weekday between 1 and 7),
    opens_at time not null,
    closes_at time not null,
    check (closes_at > opens_at),
    primary key (restaurant_id, weekday)
);

create table restaurant_legal_info (
    restaurant_id uuid primary key references restaurant(restaurant_id) on delete cascade,
    legal_name varchar(500) not null check (length(trim(legal_name)) > 0),
    inn varchar(12) not null check (inn ~ '^[0-9]{10}$' or inn ~ '^[0-9]{12}$'),
    kpp varchar(9) null check (kpp is null or kpp ~ '^[0-9]{9}$'),
    ogrn varchar(15) not null check (ogrn ~ '^[0-9]{13}$' or ogrn ~ '^[0-9]{15}$')
);

create table product (
    product_id uuid primary key default exts.uuid_generate_v4(),
    product_name varchar(120) not null check (length(trim(product_name)) > 0),
    product_category_id uuid not null references product_category(product_category_id),
    price numeric(15,2) not null check (price > 0),
    restaurant_id uuid not null references restaurant(restaurant_id),
    photo_url text null check (photo_url is null or length(trim(photo_url)) > 0),
    rating numeric(3,2) not null default 0 check (rating between 0 and 5),
    status common_status not null,
    description text null check (description is null or length(trim(description)) > 0)
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
    order_amount numeric(15,2) not null check (order_amount > 0),
    commission numeric(15,2) not null check (commission >= 0),
    total_amount numeric(15,2) not null check (total_amount >= order_amount),
    rating numeric(3,2) not null default 0 check (rating between 0 and 5),
    status order_status not null,
    pay_status pay_status not null,
    description text null check (description is null or length(trim(description)) > 0),
    check (delivery_timestamp >= order_timestamp)
);

create table order_structure (
    order_id uuid not null references "order"(order_id) on delete cascade,
    product_id uuid not null references product(product_id),
    quantity numeric(10,2) not null check (quantity > 0),
    primary key (order_id, product_id)
);

create table payment (
    payment_id uuid primary key default exts.uuid_generate_v4(),
    order_id uuid not null unique references "order"(order_id) on delete cascade,
    amount_paid numeric(15,2) not null check (amount_paid > 0),
    payment_method payment_method not null,
    payment_transaction text null check (payment_transaction is null or length(trim(payment_transaction)) > 0),
    status payment_status not null,
    paid_at timestamp not null
);

create table review (
    review_id uuid primary key default exts.uuid_generate_v4(),
    client_id uuid not null references clients(client_id),
    review_timestamp timestamp not null,
    entity_id uuid not null,
    entity_type review_entity_type not null,
    order_id uuid references "order"(order_id),
    description text null check (description is null or length(trim(description)) > 0),
    photo_url text null check (photo_url is null or length(trim(photo_url)) > 0),
    rating numeric(2,1) not null check (rating between 1 and 5)
);

create table courier_pay (
    year int not null check (year between 2000 and 2100),
    month int not null check (month between 1 and 12),
    courier_id uuid not null references courier(courier_id) on delete cascade,
    amount numeric(15,2) not null check (amount >= 0),
    primary key (year, month, courier_id)
);

create index ix_order_restaurant on "order"(restaurant_id);
create index ix_order_courier on "order"(courier_id);
create index ix_order_client on "order"(client_id);
create index ix_review_entity on review(entity_type, entity_id);

create or replace procedure insert_test_data(value int)
language plpgsql
security definer
set search_path to tsaryuk_food, public
as $$
declare
    i int;
    j int;
    v_client_id uuid;
    v_restaurant_id uuid;
    v_order_id uuid;
    v_address_id uuid;
    v_order_ts timestamp;
    v_lines_sum numeric(15,2);
    v_commission numeric(15,2);
    v_total numeric(15,2);
    v_month date;
    v_pick uuid;
    v_qty numeric(10,2);
    v_surname text;
    v_first text;
    v_mid text;
    v_street text;
    v_login text;
    v_pass text;
    v_phone text;
    v_inn text;
    v_kpp text;
    v_ogrn text;
    v_legal text;
    v_cat uuid;
    v_commission_rate numeric := 0.10;
    v_pay_st pay_status;
    streets text[] := array[
        'ул. Тверская', 'ул. Арбат', 'пр-кт Мира', 'ул. Садовая', 'наб. Фонтанки',
        'ул. Красная', 'пр-кт Ленина', 'ул. Пушкина', 'ул. Гагарина', 'ул. Мира'
    ];
    surnames text[] := array[
        'Иванов','Петров','Сидоров','Смирнов','Кузнецов','Попов','Васильев','Соколов','Михайлов','Новиков'
    ];
    names_m text[] := array[
        'Александр','Дмитрий','Максим','Сергей','Андрей','Алексей','Иван','Евгений','Николай','Михаил'
    ];
    names_f text[] := array[
        'Анна','Мария','Елена','Ольга','Татьяна','Наталья','Ирина','Светлана','Екатерина','Юлия'
    ];
    patronymics text[] := array[
        'Александрович','Дмитриевич','Сергеевич','Иванович','Петрович',
        'Александровна','Дмитриевна','Сергеевна','Ивановна','Петровна'
    ];
begin
    if value is null or value <= 0 then
        raise exception 'value must be > 0';
    end if;

    for i in 1..(value * 5) loop
        v_street := streets[1 + floor(random() * cardinality(streets))::int];
        insert into address(street, house_number, apartment_office)
        values (
            v_street || ', д. ' || (1 + floor(random() * 120))::text,
            (1 + floor(random() * 200))::text,
            case when random() < 0.3 then null else (1 + floor(random() * 400))::text end
        );
    end loop;

    for i in 1..value loop
        v_surname := surnames[1 + floor(random() * cardinality(surnames))::int];
        v_first := names_m[1 + floor(random() * cardinality(names_m))::int];
        v_mid := patronymics[1 + floor(random() * cardinality(patronymics))::int];
        v_login := left(
            lower(translate(v_surname || '_' || v_first || '_' || md5(random()::text), 'ё', 'е')),
            45
        ) || '_' || floor(random() * 100000)::text;
        v_login := left(v_login, 50);
        v_pass := substring(md5((random()::text || clock_timestamp()::text)) from 1 for 12)
            || substring(md5((random()::text || i::text)) from 1 for 12);
        v_phone := '7' || lpad((floor(random() * 1e9))::bigint::text, 10, '0');

        insert into clients(login, password, phone_number, last_name, first_name, middle_name)
        values (v_login, v_pass, v_phone::char(11), v_surname, v_first, v_mid);

        v_surname := surnames[1 + floor(random() * cardinality(surnames))::int];
        v_first := names_f[1 + floor(random() * cardinality(names_f))::int];
        v_mid := patronymics[1 + floor(random() * cardinality(patronymics))::int];
        v_phone := '7' || lpad((floor(random() * 1e9))::bigint::text, 10, '0');
        insert into courier(last_name, first_name, middle_name, phone_number, status, hire_date, dismissal_date, delivery_rate_percent)
        values (
            v_surname,
            v_first,
            case when random() < 0.2 then null else v_mid end,
            v_phone::char(11),
            (enum_range(null::common_status))[1 + floor(random() * cardinality(enum_range(null::common_status)))::int],
            current_date - floor(random() * 180)::int,
            null,
            0.0300
        );

        insert into product_category(product_category_name)
        values (
            'Категория ' || (1 + floor(random() * 9000))::text || ' '
            || left(md5(random()::text), 8)
        );

        select address_id into v_address_id from address order by random() limit 1;

        insert into restaurant(restaurant_name, address_id, description, rating, status)
        values (
            'Кафе «' || left(md5(random()::text), 10) || '»',
            v_address_id,
            case when random() < 0.15 then null else 'Доставка блюд. Зона: Москва и МО.' end,
            0,
            (enum_range(null::common_status))[1 + floor(random() * cardinality(enum_range(null::common_status)))::int]
        )
        returning restaurant_id into v_restaurant_id;

        for j in 1..7 loop
            insert into restaurant_work_hours(restaurant_id, weekday, opens_at, closes_at)
            values (
                v_restaurant_id,
                j,
                make_time(9 + (j % 2), 0, 0),
                make_time(22, 0, 0)
            );
        end loop;

        v_inn := case when random() < 0.5
            then lpad((floor(random() * 1e10))::bigint::text, 10, '0')
            else lpad((floor(random() * 1e12))::bigint::text, 12, '0')
        end;
        v_kpp := case when length(v_inn) = 10 then lpad((floor(random() * 1e9))::bigint::text, 9, '0') else null end;
        v_ogrn := case when random() < 0.5
            then lpad((floor(random() * 1e13))::bigint::text, 13, '0')
            else lpad((floor(random() * 1e15))::bigint::text, 15, '0')
        end;
        v_legal := 'ООО «' || left(md5(random()::text), 12) || '»';
        insert into restaurant_legal_info(restaurant_id, legal_name, inn, kpp, ogrn)
        values (v_restaurant_id, v_legal, v_inn, v_kpp, v_ogrn);
    end loop;

    for i in 1..(value * 5) loop
        select product_category_id into v_cat from product_category order by random() limit 1;
        select restaurant_id into v_restaurant_id from restaurant order by random() limit 1;

        insert into product(product_name, product_category_id, price, restaurant_id, photo_url, status, description)
        values (
            case when i = 1
                then 'Дегустационный сет «Премиум»'
                else 'Блюдо №' || i::text || ' «' || left(md5(random()::text), 8) || '»'
            end,
            v_cat,
            case when i = 1 then 80000000.00 else round((150 + random() * 3500)::numeric, 2) end,
            v_restaurant_id,
            case when random() < 0.1 then null else 'https://cdn.example.ru/dish/' || left(md5(random()::text), 16) end,
            (enum_range(null::common_status))[1 + floor(random() * cardinality(enum_range(null::common_status)))::int],
            case when random() < 0.1 then null else 'Блюдо из меню заведения.' end
        );

        v_order_ts := current_timestamp - (floor(random() * (180 * 24 * 60))::int * interval '1 minute');

        select r.restaurant_id
        into v_restaurant_id
        from restaurant r
        where exists (select 1 from product p where p.restaurant_id = r.restaurant_id)
        order by random()
        limit 1;

        insert into "order"(
            courier_id, client_id, address_id, restaurant_id,
            order_timestamp, delivery_timestamp,
            order_amount, commission, total_amount,
            status, pay_status, description
        )
        values (
            (select courier_id from courier order by random() limit 1),
            (select client_id from clients order by random() limit 1),
            (select address_id from address order by random() limit 1),
            v_restaurant_id,
            v_order_ts,
            v_order_ts + ((25 + floor(random() * 85))::int * interval '1 minute'),
            0.01,
            0,
            0.01,
            case
                when random() < 0.72 then 'доставлен'::order_status
                else (
                    array['создан', 'принят', 'в_доставке', 'отменён']::order_status[]
                )[1 + floor(random() * 4)::int]
            end,
            'не_оплачен'::pay_status,
            case when random() < 0.2 then null else 'Заказ через приложение.' end
        )
        returning order_id, client_id into v_order_id, v_client_id;

        v_lines_sum := 0;
        for j in 1..(1 + floor(random() * 3))::int loop
            select p.product_id into v_pick
            from product p
            where p.restaurant_id = v_restaurant_id
            order by random()
            limit 1;

            v_qty := (1 + floor(random() * 4))::numeric;
            insert into order_structure(order_id, product_id, quantity)
            values (v_order_id, v_pick, v_qty)
            on conflict (order_id, product_id) do update
            set quantity = order_structure.quantity + excluded.quantity;

            v_lines_sum := v_lines_sum + (select price * v_qty from product where product_id = v_pick);
        end loop;

        v_commission := round(v_lines_sum * v_commission_rate, 2);
        v_total := v_lines_sum + v_commission;

        update "order"
        set order_amount = v_lines_sum,
            commission = v_commission,
            total_amount = v_total
        where order_id = v_order_id;

        v_pay_st := case when random() < 0.85 then 'оплачен'::pay_status else 'не_оплачен'::pay_status end;

        update "order"
        set pay_status = v_pay_st
        where order_id = v_order_id;

        if v_pay_st = 'оплачен'::pay_status then
            insert into payment(order_id, amount_paid, payment_method, payment_transaction, status, paid_at)
            values (
                v_order_id,
                v_total,
                (enum_range(null::payment_method))[1 + floor(random() * cardinality(enum_range(null::payment_method)))::int],
                'TXN-' || replace(v_order_id::text, '-', '') || '-' || floor(random() * 10000)::text,
                'успешно'::payment_status,
                v_order_ts + interval '5 minute'
            );
        end if;

        insert into review(client_id, review_timestamp, entity_id, entity_type, order_id, description, photo_url, rating)
        values (
            v_client_id,
            v_order_ts + ((45 + floor(random() * 200))::int * interval '1 minute'),
            case floor(random() * 3)::int
                when 0 then (select product_id from order_structure where order_id = v_order_id order by random() limit 1)
                when 1 then v_restaurant_id
                else v_order_id
            end,
            case floor(random() * 3)::int
                when 0 then 'блюдо'::review_entity_type
                when 1 then 'заведение'::review_entity_type
                else 'заказ'::review_entity_type
            end,
            v_order_id,
            case when random() < 0.15 then null else 'Заказ доставлен вовремя, всё отлично.' end,
            case when random() < 0.2 then null else 'https://cdn.example.ru/rev/' || left(md5(random()::text), 12) end,
            round((1 + random() * 4)::numeric, 1)
        );
    end loop;

    insert into client_address(client_id, address_id)
    select c.client_id, a.address_id
    from clients c
    cross join lateral (select address_id from address order by random() limit 1) a
    on conflict do nothing;

    for v_month in
        select (date_trunc('month', current_date) - (s * interval '1 month'))::date
        from generate_series(0, 5) s
    loop
        insert into courier_pay(year, month, courier_id, amount)
        select
            extract(year from v_month)::int,
            extract(month from v_month)::int,
            c.courier_id,
            round(
                (
                    count(o.order_id) filter (where o.status = 'доставлен') * 200
                    + coalesce(
                        sum(o.order_amount) filter (where o.status = 'доставлен'),
                        0
                    ) * c.delivery_rate_percent
                )::numeric,
                2
            )
        from courier c
        left join "order" o
            on o.courier_id = c.courier_id
            and date_trunc('month', o.delivery_timestamp) = date_trunc('month', v_month::timestamp)
        group by c.courier_id, c.delivery_rate_percent
        on conflict (year, month, courier_id) do update
        set amount = excluded.amount;
    end loop;
end;
$$;

create or replace procedure erase_test_data()
language plpgsql
security definer
set search_path to tsaryuk_food, public
as $$
begin
    delete from review;
    delete from payment;
    delete from order_structure;
    delete from client_address;
    delete from courier_pay;
    delete from "order";
    delete from product;
    delete from restaurant_work_hours;
    delete from restaurant_legal_info;
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
security definer
set search_path to tsaryuk_food, public
as $$
declare
    v_entity_id uuid;
    v_entity_type review_entity_type;
begin
    v_entity_id := coalesce(new.entity_id, old.entity_id);
    v_entity_type := coalesce(new.entity_type, old.entity_type);

    if v_entity_type = 'блюдо' then
        update product p
        set rating = coalesce((
            select round(avg(r.rating)::numeric, 2)
            from review r
            where r.entity_type = 'блюдо' and r.entity_id = p.product_id
        ), 0)
        where p.product_id = v_entity_id;
    elsif v_entity_type = 'заведение' then
        update restaurant rs
        set rating = coalesce((
            select round(avg(r.rating)::numeric, 2)
            from review r
            where r.entity_type = 'заведение' and r.entity_id = rs.restaurant_id
        ), 0)
        where rs.restaurant_id = v_entity_id;
    elsif v_entity_type = 'заказ' then
        update "order" o
        set rating = coalesce((
            select round(avg(r.rating)::numeric, 2)
            from review r
            where r.entity_type = 'заказ' and r.entity_id = o.order_id
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
stable
set search_path to tsaryuk_food, public
as $$
    with ord as (
        select restaurant_id, order_id, client_id, total_amount
        from "order"
    ),
    totals as (
        select restaurant_id, sum(total_amount) as total_amount, count(*)::numeric as order_cnt
        from ord
        group by restaurant_id
    ),
    line_qty as (
        select o.restaurant_id, os.product_id, sum(os.quantity) as qty_sum
        from ord o
        join order_structure os on os.order_id = o.order_id
        group by o.restaurant_id, os.product_id
    ),
    best_pid as (
        select distinct on (restaurant_id)
            restaurant_id,
            product_id
        from line_qty
        order by restaurant_id, qty_sum desc, product_id desc
    ),
    best_pname as (
        select bp.restaurant_id, p.product_name
        from best_pid bp
        join product p on p.product_id = bp.product_id
    ),
    client_cnt as (
        select restaurant_id, client_id, count(*) as c_cnt
        from ord
        group by restaurant_id, client_id
    ),
    best_cid as (
        select distinct on (restaurant_id)
            restaurant_id,
            client_id
        from client_cnt
        order by restaurant_id, c_cnt desc, client_id desc
    ),
    best_display as (
        select
            bc.restaurant_id,
            trim(c.last_name || ' ' || c.first_name || ' ' || coalesce(c.middle_name, '')) as best_user
        from best_cid bc
        join clients c on c.client_id = bc.client_id
    )
    select
        r.restaurant_name::varchar,
        coalesce(bp.product_name, ''::varchar)::varchar as best_product_name,
        coalesce(t.total_amount, 0)::numeric(18,2) as total_amount,
        case
            when coalesce(t.order_cnt, 0) = 0 then 0::numeric(18,2)
            else round(t.total_amount / t.order_cnt, 2)::numeric(18,2)
        end as avg_amount,
        coalesce(bd.best_user, ''::varchar)::varchar as best_user
    from restaurant r
    left join totals t on t.restaurant_id = r.restaurant_id
    left join best_pname bp on bp.restaurant_id = r.restaurant_id
    left join best_display bd on bd.restaurant_id = r.restaurant_id;
$$;

create or replace procedure add_product(
    p_product_name varchar(120),
    p_product_category_id uuid,
    p_price numeric(15,2),
    p_restaurant_id uuid,
    p_photo_url text,
    p_rating numeric(3,2),
    p_status common_status,
    p_description text
)
language plpgsql
security definer
set search_path to tsaryuk_food, public
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
set search_path to tsaryuk_food, public
as $$
declare
    v_calc_month date := (date_trunc('month', current_date) - interval '1 month')::date;
    v_y int := extract(year from v_calc_month)::int;
    v_m int := extract(month from v_calc_month)::int;
begin
    insert into courier_pay(year, month, courier_id, amount)
    select
        v_y,
        v_m,
        c.courier_id,
        round(
            (
                count(o.order_id) filter (where o.status = 'доставлен') * 250
                + coalesce(
                    sum(o.order_amount) filter (where o.status = 'доставлен'),
                    0
                ) * c.delivery_rate_percent
            )::numeric,
            2
        )
    from courier c
    left join "order" o
        on o.courier_id = c.courier_id
        and date_trunc('month', o.delivery_timestamp) = v_calc_month
    group by c.courier_id, c.delivery_rate_percent
    on conflict (year, month, courier_id) do update
    set amount = excluded.amount;

    update courier c
    set delivery_rate_percent = sub.new_rate
    from (
        select
            c2.courier_id,
            case
                when cnt >= 60 then 0.0700
                when cnt >= 30 then 0.0500
                else 0.0300
            end as new_rate
        from courier c2
        left join lateral (
            select count(*)::int as cnt
            from "order" o
            where o.courier_id = c2.courier_id
              and o.status = 'доставлен'
              and date_trunc('month', o.delivery_timestamp) = v_calc_month
        ) d on true
    ) sub
    where c.courier_id = sub.courier_id;
end;
$$;

create or replace view how_much_money as
with recursive bounds as (
    select
        coalesce(
            (select date_trunc('month', min(order_timestamp))::date from "order"),
            date_trunc('month', current_timestamp)::date
        ) as d0,
        coalesce(
            (select date_trunc('month', max(order_timestamp))::date from "order"),
            date_trunc('month', current_timestamp)::date
        ) as d1
),
month_seq(d) as (
    select d0 from bounds
    union all
    select (month_seq.d + interval '1 month')::date
    from month_seq
    cross join bounds b
    where month_seq.d < b.d1
),
monthly as (
    select
        extract(year from ms.d)::int as year,
        extract(month from ms.d)::int as month,
        coalesce(sum(o.order_amount), 0)::numeric(18,2) as amount_without_commission,
        coalesce(sum(o.total_amount), 0)::numeric(18,2) as amount_with_commission,
        coalesce(sum(o.commission), 0)::numeric(18,2) as commission_amount,
        coalesce(cp.courier_amount, 0)::numeric(18,2) as courier_amount
    from month_seq ms
    left join "order" o
        on date_trunc('month', o.order_timestamp) = ms.d
    left join (
        select year, month, sum(amount) as courier_amount
        from courier_pay
        group by year, month
    ) cp on cp.year = extract(year from ms.d)::int
        and cp.month = extract(month from ms.d)::int
    group by ms.d, cp.courier_amount
),
fin as (
    select
        year,
        month,
        amount_without_commission,
        amount_with_commission,
        commission_amount,
        lag(commission_amount) over (order by year, month) as prev_commission,
        courier_amount
    from monthly
)
select
    year,
    month,
    amount_without_commission,
    amount_with_commission,
    commission_amount,
    coalesce(prev_commission, 0::numeric(18,2)) as prev_commission,
    (commission_amount - coalesce(prev_commission, 0::numeric(18,2)))::numeric(18,2) as commission_diff,
    courier_amount,
    (commission_amount - courier_amount)::numeric(18,2) as net_profit
from fin
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
grant execute on function get_statistic() to inspector;
alter default privileges in schema tsaryuk_food grant select on tables to inspector;
grant usage on schema pg_catalog to inspector;
grant select on all tables in schema pg_catalog to inspector;
grant usage on schema information_schema to inspector;
grant select on all tables in schema information_schema to inspector;
