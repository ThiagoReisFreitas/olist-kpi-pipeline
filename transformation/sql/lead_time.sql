-- ============================================================
-- KPI: Lead Time de Entrega por estado
-- Tabelas: raw.orders + raw.customers
-- Join: customer_id
-- Regras de negócio:
--   - Apenas pedidos com status 'delivered'
--   - Apenas pedidos com todas as datas de processo preenchidas
--   - Decompõe em 3 etapas: aprovação, despacho, trânsito
-- ============================================================
SELECT c.customer_state AS estado,
    COUNT(*) AS total_pedidos,
    -- Lead time total: compra → entrega ao cliente (dias)
    ROUND(
        AVG(
            EXTRACT(
                EPOCH
                FROM (
                        o.order_delivered_customer_date::timestamp - o.order_purchase_timestamp::timestamp
                    )
            ) / 86400
        )::numeric,
        1
    ) AS lead_time_total_dias,
    -- Lead time mediano (menos sensível a outliers)
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY EXTRACT(
                    EPOCH
                    FROM (
                            o.order_delivered_customer_date::timestamp - o.order_purchase_timestamp::timestamp
                        )
                ) / 86400
        )::numeric,
        1
    ) AS lead_time_mediana_dias,
    -- Etapa 1 — Aprovação do pagamento (horas)
    ROUND(
        AVG(
            EXTRACT(
                EPOCH
                FROM (
                        o.order_approved_at::timestamp - o.order_purchase_timestamp::timestamp
                    )
            ) / 3600
        )::numeric,
        1
    ) AS tempo_aprovacao_horas,
    -- Etapa 2 — Despacho ao transportador (dias)
    ROUND(
        AVG(
            EXTRACT(
                EPOCH
                FROM (
                        o.order_delivered_carrier_date::timestamp - o.order_approved_at::timestamp
                    )
            ) / 86400
        )::numeric,
        1
    ) AS tempo_despacho_dias,
    -- Etapa 3 — Trânsito até o cliente (dias)
    ROUND(
        AVG(
            EXTRACT(
                EPOCH
                FROM (
                        o.order_delivered_customer_date::timestamp - o.order_delivered_carrier_date::timestamp
                    )
            ) / 86400
        )::numeric,
        1
    ) AS tempo_transito_dias,
    -- Gargalo: etapa que mais consome tempo em % do total
    ROUND(
        AVG(
            EXTRACT(
                EPOCH
                FROM (
                        o.order_delivered_carrier_date::timestamp - o.order_approved_at::timestamp
                    )
            )
        ) / NULLIF(
            AVG(
                EXTRACT(
                    EPOCH
                    FROM (
                            o.order_delivered_customer_date::timestamp - o.order_purchase_timestamp::timestamp
                        )
                )
            ),
            0
        ) * 100::numeric,
        1
    ) AS pct_tempo_despacho
FROM raw.orders o
    JOIN raw.customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    AND o.order_approved_at IS NOT NULL
    AND o.order_delivered_carrier_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY lead_time_total_dias DESC;