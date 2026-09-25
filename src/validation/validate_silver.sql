WITH housing_stock_checks AS (
    SELECT
        'Housing stock - quarantine records' AS CHECK_NAME,
        COUNT(*) AS FAILURE_COUNT,
        CASE
            WHEN COUNT(*) = 0 THEN 'PASS'
            ELSE 'FAIL'
        END AS STATUS
    FROM RES_HOUSING.SILVER.QUARANTINE_SF_HOUSING_STOCK q
    WHERE q.LOAD_TIMESTAMP = (
        SELECT MAX(LOAD_TIMESTAMP)
        FROM RES_HOUSING.BRONZE.RAW_SF_HOUSING_STOCK
    )
),

portfolio_stock_checks AS (
    SELECT
        'Portfolio stock - quarantine records' AS CHECK_NAME,
        COUNT(*) AS FAILURE_COUNT,
        CASE
            WHEN COUNT(*) = 0 THEN 'PASS'
            ELSE 'FAIL'
        END AS STATUS
    FROM RES_HOUSING.SILVER.QUARANTINE_SF_PORTFOLIO_STOCK q
    WHERE q.LOAD_TIMESTAMP = (
        SELECT MAX(LOAD_TIMESTAMP)
        FROM RES_HOUSING.BRONZE.RAW_SF_PORTFOLIO_STOCK
    )
),

housing_events_checks AS (
    SELECT
        'Housing events - quarantine records' AS CHECK_NAME,
        COUNT(*) AS FAILURE_COUNT,
        CASE
            WHEN COUNT(*) = 0 THEN 'PASS'
            ELSE 'FAIL'
        END AS STATUS
    FROM RES_HOUSING.SILVER.QUARANTINE_SF_HOUSING_EVENTS q
    WHERE q.LOAD_TIMESTAMP = (
        SELECT MAX(LOAD_TIMESTAMP)
        FROM RES_HOUSING.BRONZE.RAW_SF_HOUSING_EVENTS
    )
)

SELECT * FROM housing_stock_checks
UNION ALL
SELECT * FROM portfolio_stock_checks
UNION ALL
SELECT * FROM housing_events_checks;