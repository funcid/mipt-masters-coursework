SET search_path TO stroy;

SELECT COUNT(*)
FROM project
WHERE EXTRACT(YEAR FROM sign_date) = 2023;

SELECT SUM(AGE(CURRENT_DATE, p.birthdate))
FROM employee e
JOIN person p ON p.person_id = e.person_id
WHERE EXTRACT(YEAR FROM e.hire_date) = 2022;

SELECT
    p.first_name || ' ' || p.last_name AS full_name,
    e.hire_date
FROM employee e
JOIN person p ON p.person_id = e.person_id
WHERE p.last_name LIKE 'М%' 
  AND LENGTH(p.last_name) = 8
ORDER BY e.hire_date
LIMIT 1;

SELECT COALESCE(
    AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.birthdate))), 
    0
)
FROM employee e
JOIN person p ON p.person_id = e.person_id
WHERE e.dismissal_date IS NOT NULL
AND e.employee_id NOT IN (
    SELECT UNNEST(employees_id)
    FROM project
);

SELECT SUM(pp.amount)
FROM project_payment pp
JOIN project pr ON pr.project_id = pp.project_id
JOIN customer c ON c.customer_id = pr.customer_id
JOIN address a ON a.address_id = c.address_id
JOIN city ci ON ci.city_id = a.city_id
JOIN country co ON co.country_id = ci.country_id
WHERE ci.city_name = 'Жуковский'
AND co.country_name = 'Россия'
AND pp.fact_transaction_timestamp IS NOT NULL;

WITH bonuses AS (
    SELECT
        project_manager_id,
        project_cost * 0.01 AS bonus
    FROM project
    WHERE status = 'Завершен'
)
SELECT
    b.project_manager_id,
    per.full_fio,
    SUM(b.bonus) AS bonus_sum
FROM bonuses b
JOIN employee e ON e.employee_id = b.project_manager_id
JOIN person per ON per.person_id = e.person_id
GROUP BY b.project_manager_id, per.full_fio
HAVING SUM(b.bonus) = (
    SELECT MAX(total_bonus)
    FROM (
        SELECT
            project_manager_id,
            SUM(project_cost * 0.01) AS total_bonus
        FROM project
        WHERE status = 'Завершен'
        GROUP BY project_manager_id
    ) t
);

WITH payments AS (
    SELECT
        plan_payment_date,
        SUM(amount) OVER (
            ORDER BY plan_payment_date
        ) AS cumulative_sum
    FROM project_payment
    WHERE payment_type = 'Авансовый'
)
SELECT plan_payment_date
FROM payments
WHERE cumulative_sum > 30000000
ORDER BY plan_payment_date
LIMIT 1;

WITH RECURSIVE units AS (
    SELECT unit_id
    FROM company_structure
    WHERE unit_id = 17

    UNION ALL

    SELECT cs.unit_id
    FROM company_structure cs
    JOIN units u ON cs.parent_id = u.unit_id
)
SELECT SUM(ep.salary)
FROM units u
JOIN position p ON p.unit_id = u.unit_id
JOIN employee_position ep ON ep.position_id = p.position_id;

WITH numbered AS (
    SELECT
        project_id,
        amount,
        fact_transaction_timestamp,
        EXTRACT(YEAR FROM fact_transaction_timestamp) AS yr,
        ROW_NUMBER() OVER (
            PARTITION BY EXTRACT(YEAR FROM fact_transaction_timestamp)
            ORDER BY fact_transaction_timestamp
        ) AS rn
    FROM project_payment
    WHERE fact_transaction_timestamp IS NOT NULL
),
filtered AS (
    SELECT
        *,
        AVG(amount) OVER (
            ORDER BY fact_transaction_timestamp
            ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
        ) AS moving_avg
    FROM numbered
    WHERE rn % 5 = 0
),
avg_sum AS (
    SELECT SUM(moving_avg) AS total_avg
    FROM filtered
),
project_year_sum AS (
    SELECT
        EXTRACT(YEAR FROM sign_date) AS yr,
        SUM(project_cost) AS project_sum
    FROM project
    GROUP BY yr
)
SELECT pys.yr, pys.project_sum
FROM project_year_sum pys, avg_sum
WHERE pys.project_sum < avg_sum.total_avg;

CREATE MATERIALIZED VIEW IF NOT EXISTS project_report_mv AS
SELECT
    p.project_id,
    p.project_name,
    MAX(pp.fact_transaction_timestamp) AS last_payment_date,
    (
        SELECT amount
        FROM project_payment
        WHERE project_id = p.project_id
        ORDER BY fact_transaction_timestamp DESC
        LIMIT 1
    ) AS last_payment_amount,
    per.full_fio,
    c.customer_name,
    STRING_AGG(tw.type_of_work_name, ', ') AS works
FROM project p
LEFT JOIN project_payment pp ON pp.project_id = p.project_id
JOIN employee e ON e.employee_id = p.project_manager_id
JOIN person per ON per.person_id = e.person_id
JOIN customer c ON c.customer_id = p.customer_id
LEFT JOIN customer_type_of_work ctw ON ctw.customer_id = c.customer_id
LEFT JOIN type_of_work tw ON tw.type_of_work_id = ctw.type_of_work_id
GROUP BY
    p.project_id,
    p.project_name,
    per.full_fio,
    c.customer_name;

