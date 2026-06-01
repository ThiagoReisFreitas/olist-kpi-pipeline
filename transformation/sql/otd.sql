-- ============================================================
-- KPI: On-Time Delivery (OTD) por estado
-- Tabelas: raw.orders + raw.customers
-- Join: customer_id
-- Regras de negócio:
--   - Apenas pedidos com status 'delivered'
--   - Apenas pedidos com data de entrega real preenchida
--   - No prazo: order_delivered_customer_date <= order_estimated_delivery_date
-- ============================================================
SELECT c.customer_state AS estado,
    COUNT(*) AS total_pedidos,
    -- Pedidos no prazo
    COUNT(*) FILTER (
        WHERE o.order_delivered_customer_date::timestamp <= o.order_estimated_delivery_date::timestamp
    ) AS pedidos_no_prazo,
    -- Pedidos atrasados
    COUNT(*) FILTER (
        WHERE o.order_delivered_customer_date::timestamp > o.order_estimated_delivery_date::timestamp
    ) AS pedidos_atrasados,
    -- % OTD
    ROUND(
        COUNT(*) FILTER (
            WHERE o.order_delivered_customer_date::timestamp <= o.order_estimated_delivery_date::timestamp
        )::numeric / COUNT(*) * 100,
        2
    ) AS otd_pct,
    -- Atraso médio em dias (apenas pedidos que atrasaram)
    ROUND(
        AVG(
            CASE
                WHEN o.order_delivered_customer_date::timestamp > o.order_estimated_delivery_date::timestamp THEN EXTRACT(
                    EPOCH
                    FROM (
                            o.order_delivered_customer_date::timestamp - o.order_estimated_delivery_date::timestamp
                        )
                ) / 86400
            END
        )::numeric,
        1
    ) AS atraso_medio_dias,
    -- Pior atraso registrado no estado (dias)
    ROUND(
        MAX(
            CASE
                WHEN o.order_delivered_customer_date::timestamp > o.order_estimated_delivery_date::timestamp THEN EXTRACT(
                    EPOCH
                    FROM (
                            o.order_delivered_customer_date::timestamp - o.order_estimated_delivery_date::timestamp
                        )
                ) / 86400
            END
        )::numeric,
        1
    ) AS pior_atraso_dias
FROM raw.orders o
    JOIN raw.customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY otd_pct DESC;