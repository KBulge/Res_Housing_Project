-- ============================================================
-- GOLD CANDIDATE VALIDATION
-- Sources:
--   Bronze: RAW_MARKETS
--   Silver: SF_HOUSING_STOCK
--           SF_PORTFOLIO_STOCK
--           SF_HOUSING_EVENTS
-- ============================================================

WITH

-- ============================================================
-- CANDIDATE DIM_DATE
-- ============================================================

candidate_dates AS (

    SELECT DISTINCT DATE
    FROM RES_HOUSING.SILVER.SF_HOUSING_STOCK
    WHERE DATE IS NOT NULL

    UNION

    SELECT DISTINCT DATE
    FROM RES_HOUSING.SILVER.SF_PORTFOLIO_STOCK
    WHERE DATE IS NOT NULL

    UNION

    SELECT DISTINCT DATE
    FROM RES_HOUSING.SILVER.SF_HOUSING_EVENTS
    WHERE DATE IS NOT NULL
),

-- ============================================================
-- CANDIDATE DIM_MARKET
-- ============================================================

candidate_markets AS (

    SELECT
        PARCL_ID,
        NAME AS MARKET_NAME,
        LOCATION_TYPE
    FROM RES_HOUSING.BRONZE.RAW_MARKETS
    WHERE PARCL_ID IS NOT NULL
      AND NAME IS NOT NULL
      AND LOCATION_TYPE = 'CBSA'
),

-- ============================================================
-- CANDIDATE DIM_PORTFOLIO
-- ============================================================

candidate_portfolios AS (

    SELECT
        'PORTFOLIO_2_TO_9' AS PORTFOLIO_SIZE

    UNION ALL

    SELECT
        'PORTFOLIO_10_TO_99'

    UNION ALL

    SELECT
        'PORTFOLIO_100_TO_999'

    UNION ALL

    SELECT
        'PORTFOLIO_1000_PLUS'
),

-- ============================================================
-- CANDIDATE FACT_INVESTOR_HOUSING_STOCK
-- ============================================================

portfolio_unpivot AS (

    SELECT
        PARCL_ID,
        DATE,
        'PORTFOLIO_2_TO_9' AS PORTFOLIO_SIZE,
        COUNT_PORTFOLIO_2_TO_9 AS INVESTOR_OWNED_PROPERTIES,
        PCT_SF_HOUSING_STOCK_PORTFOLIO_2_TO_9
            AS PERCENT_OF_HOUSING_STOCK
    FROM RES_HOUSING.SILVER.SF_PORTFOLIO_STOCK

    UNION ALL

    SELECT
        PARCL_ID,
        DATE,
        'PORTFOLIO_10_TO_99',
        COUNT_PORTFOLIO_10_TO_99,
        PCT_SF_HOUSING_STOCK_PORTFOLIO_10_TO_99
    FROM RES_HOUSING.SILVER.SF_PORTFOLIO_STOCK

    UNION ALL

    SELECT
        PARCL_ID,
        DATE,
        'PORTFOLIO_100_TO_999',
        COUNT_PORTFOLIO_100_TO_999,
        PCT_SF_HOUSING_STOCK_PORTFOLIO_100_TO_999
    FROM RES_HOUSING.SILVER.SF_PORTFOLIO_STOCK

    UNION ALL

    SELECT
        PARCL_ID,
        DATE,
        'PORTFOLIO_1000_PLUS',
        COUNT_PORTFOLIO_1000_PLUS,
        PCT_SF_HOUSING_STOCK_PORTFOLIO_1000_PLUS
    FROM RES_HOUSING.SILVER.SF_PORTFOLIO_STOCK
),

candidate_stock AS (

    SELECT
        u.PARCL_ID,
        u.DATE,
        u.PORTFOLIO_SIZE,
        u.INVESTOR_OWNED_PROPERTIES,
        u.PERCENT_OF_HOUSING_STOCK
    FROM portfolio_unpivot u
),

-- ============================================================
-- CANDIDATE FACT_INVESTOR_HOUSING_EVENTS
-- ============================================================

candidate_events AS (

    SELECT
        PARCL_ID,
        DATE,
        PORTFOLIO_SIZE,
        ACQUISITIONS,
        DISPOSITIONS,
        NEW_LISTINGS_FOR_SALE,
        NEW_RENTAL_LISTINGS,
        TRANSFERS
    FROM RES_HOUSING.SILVER.SF_HOUSING_EVENTS
),

-- ============================================================
-- VALIDATION CHECKS
-- ============================================================

checks AS (

    -- ========================================================
    -- DIM_DATE
    -- ========================================================

    SELECT
        'DIM_DATE - Dates are not NULL' AS CHECK_NAME,
        CASE
            WHEN COUNT_IF(DATE IS NULL) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END AS STATUS
    FROM candidate_dates

    UNION ALL

    SELECT
        'DIM_DATE - Unique dates',
        CASE
            WHEN COUNT(*) = COUNT(DISTINCT DATE)
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_dates

    -- ========================================================
    -- DIM_MARKET
    -- ========================================================

    UNION ALL

    SELECT
        'DIM_MARKET - Required fields are not NULL',
        CASE
            WHEN COUNT_IF(
                PARCL_ID IS NULL
                OR MARKET_NAME IS NULL
                OR LOCATION_TYPE IS NULL
            ) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_markets

    UNION ALL

    SELECT
        'DIM_MARKET - Unique PARCL_ID',
        CASE
            WHEN COUNT(*) = COUNT(DISTINCT PARCL_ID)
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_markets

    UNION ALL

    SELECT
        'DIM_MARKET - Unique market name',
        CASE
            WHEN COUNT(*) = COUNT(DISTINCT MARKET_NAME)
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_markets

    UNION ALL

    SELECT
        'DIM_MARKET - Valid LOCATION_TYPE',
        CASE
            WHEN COUNT_IF(LOCATION_TYPE <> 'CBSA') = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_markets

    -- ========================================================
    -- DIM_PORTFOLIO
    -- ========================================================

    UNION ALL

    SELECT
        'DIM_PORTFOLIO - Expected categories',
        CASE
            WHEN COUNT(*) = 4
             AND COUNT(DISTINCT PORTFOLIO_SIZE) = 4
             AND COUNT_IF(
                    PORTFOLIO_SIZE IN (
                        'PORTFOLIO_2_TO_9',
                        'PORTFOLIO_10_TO_99',
                        'PORTFOLIO_100_TO_999',
                        'PORTFOLIO_1000_PLUS'
                    )
                 ) = 4
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_portfolios

    -- ========================================================
    -- FACT_STOCK
    -- ========================================================

    UNION ALL

    SELECT
        'FACT_STOCK - Four categories per source row',
        CASE
            WHEN (
                SELECT COUNT(*)
                FROM candidate_stock
            ) = (
                SELECT COUNT(*)
                FROM RES_HOUSING.SILVER.SF_PORTFOLIO_STOCK
            ) * 4
            THEN 'PASS'
            ELSE 'FAIL'
        END

    UNION ALL

    SELECT
        'FACT_STOCK - Valid market references',
        CASE
            WHEN COUNT(*) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_stock s
    LEFT JOIN candidate_markets m
        ON s.PARCL_ID = m.PARCL_ID
    WHERE m.PARCL_ID IS NULL

    UNION ALL

    SELECT
        'FACT_STOCK - Valid date references',
        CASE
            WHEN COUNT(*) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_stock s
    LEFT JOIN candidate_dates d
        ON s.DATE = d.DATE
    WHERE d.DATE IS NULL

    UNION ALL

    SELECT
        'FACT_STOCK - Valid portfolio references',
        CASE
            WHEN COUNT(*) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_stock s
    LEFT JOIN candidate_portfolios p
        ON s.PORTFOLIO_SIZE = p.PORTFOLIO_SIZE
    WHERE p.PORTFOLIO_SIZE IS NULL

    UNION ALL

    SELECT
        'FACT_STOCK - Unique fact grain',
        CASE
            WHEN COUNT(*) = COUNT(
                DISTINCT
                    PARCL_ID || '|' ||
                    DATE || '|' ||
                    PORTFOLIO_SIZE
            )
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_stock

    UNION ALL

    SELECT
        'FACT_STOCK - Valid measures',
        CASE
            WHEN COUNT_IF(
                INVESTOR_OWNED_PROPERTIES < 0
                OR PERCENT_OF_HOUSING_STOCK < 0
                OR PERCENT_OF_HOUSING_STOCK > 100
            ) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_stock

    -- ========================================================
    -- FACT_EVENTS
    -- ========================================================

    UNION ALL

    SELECT
        'FACT_EVENTS - Valid market references',
        CASE
            WHEN COUNT(*) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_events e
    LEFT JOIN candidate_markets m
        ON e.PARCL_ID = m.PARCL_ID
    WHERE m.PARCL_ID IS NULL

    UNION ALL

    SELECT
        'FACT_EVENTS - Valid date references',
        CASE
            WHEN COUNT(*) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_events e
    LEFT JOIN candidate_dates d
        ON e.DATE = d.DATE
    WHERE d.DATE IS NULL

    UNION ALL

    SELECT
        'FACT_EVENTS - Valid portfolio references',
        CASE
            WHEN COUNT(*) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_events e
    LEFT JOIN candidate_portfolios p
        ON e.PORTFOLIO_SIZE = p.PORTFOLIO_SIZE
    WHERE p.PORTFOLIO_SIZE IS NULL

    UNION ALL

    SELECT
        'FACT_EVENTS - Unique fact grain',
        CASE
            WHEN COUNT(*) = COUNT(
                DISTINCT
                    PARCL_ID || '|' ||
                    DATE || '|' ||
                    PORTFOLIO_SIZE
            )
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_events

    UNION ALL

    SELECT
        'FACT_EVENTS - Non-negative event counts',
        CASE
            WHEN COUNT_IF(
                ACQUISITIONS < 0
                OR DISPOSITIONS < 0
                OR NEW_LISTINGS_FOR_SALE < 0
                OR NEW_RENTAL_LISTINGS < 0
                OR TRANSFERS < 0
            ) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END
    FROM candidate_events
)

-- ============================================================
-- FINAL VALIDATION RESULT
-- ============================================================

SELECT
    CHECK_NAME,
    STATUS
FROM checks
ORDER BY CHECK_NAME;