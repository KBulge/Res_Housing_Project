-- ============================================================
-- SF HOUSING STOCK
-- ============================================================

WITH housing_stock_checks AS (
    SELECT
        'Housing stock - validation failures' AS CHECK_NAME,
        COUNT(*) AS FAILURE_COUNT,
        CASE
            WHEN COUNT(*) = 0 THEN 'PASS'
            ELSE 'FAIL'
        END AS STATUS
    FROM RES_HOUSING.SILVER.STAGING_SF_HOUSING_STOCK
    WHERE PARCL_ID IS NULL
       OR DATE IS NULL
       OR SINGLE_FAMILY < 0
       OR CONDO < 0
       OR TOWNHOUSE < 0
       OR OTHER < 0
       OR ALL_PROPERTIES < 0
       OR SINGLE_FAMILY + CONDO + TOWNHOUSE + OTHER
          <> ALL_PROPERTIES
),


-- ============================================================
-- SF PORTFOLIO STOCK
-- ============================================================

portfolio_stock_checks AS (
    SELECT
        'Portfolio stock - validation failures' AS CHECK_NAME,
        COUNT(*) AS FAILURE_COUNT,
        CASE
            WHEN COUNT(*) = 0 THEN 'PASS'
            ELSE 'FAIL'
        END AS STATUS
    FROM RES_HOUSING.SILVER.STAGING_SF_PORTFOLIO_STOCK
    WHERE PARCL_ID IS NULL
       OR DATE IS NULL
       OR COUNT_PORTFOLIO_2_TO_9 < 0
       OR COUNT_PORTFOLIO_10_TO_99 < 0
       OR COUNT_PORTFOLIO_100_TO_999 < 0
       OR COUNT_PORTFOLIO_1000_PLUS < 0
       OR COUNT_ALL_PORTFOLIOS < 0
       OR COUNT_PORTFOLIO_2_TO_9
          + COUNT_PORTFOLIO_10_TO_99
          + COUNT_PORTFOLIO_100_TO_999
          + COUNT_PORTFOLIO_1000_PLUS
          <> COUNT_ALL_PORTFOLIOS
       OR PCT_SF_HOUSING_STOCK_PORTFOLIO_2_TO_9 NOT BETWEEN 0 AND 100
       OR PCT_SF_HOUSING_STOCK_PORTFOLIO_10_TO_99 NOT BETWEEN 0 AND 100
       OR PCT_SF_HOUSING_STOCK_PORTFOLIO_100_TO_999 NOT BETWEEN 0 AND 100
       OR PCT_SF_HOUSING_STOCK_PORTFOLIO_1000_PLUS NOT BETWEEN 0 AND 100
       OR PCT_SF_HOUSING_STOCK_ALL_PORTFOLIOS NOT BETWEEN 0 AND 100
),


-- ============================================================
-- SF HOUSING EVENTS
-- ============================================================

housing_events_checks AS (
    SELECT
        'Housing events - validation failures' AS CHECK_NAME,
        COUNT(*) AS FAILURE_COUNT,
        CASE
            WHEN COUNT(*) = 0 THEN 'PASS'
            ELSE 'FAIL'
        END AS STATUS
    FROM RES_HOUSING.SILVER.STAGING_SF_HOUSING_EVENTS
    WHERE PARCL_ID IS NULL
       OR DATE IS NULL
       OR PORTFOLIO_SIZE IS NULL
       OR PORTFOLIO_SIZE NOT IN (
            'PORTFOLIO_2_TO_9',
            'PORTFOLIO_10_TO_99',
            'PORTFOLIO_100_TO_999',
            'PORTFOLIO_1000_PLUS'
       )
       OR ACQUISITIONS < 0
       OR DISPOSITIONS < 0
       OR NEW_LISTINGS_FOR_SALE < 0
       OR NEW_RENTAL_LISTINGS < 0
       OR TRANSFERS < 0
)

SELECT * FROM housing_stock_checks

UNION ALL

SELECT * FROM portfolio_stock_checks

UNION ALL

SELECT * FROM housing_events_checks;