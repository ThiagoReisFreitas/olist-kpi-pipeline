-- ============================================================
-- KPI: Correlação Atraso × Satisfação
-- Tabelas: raw.orders + raw.order_reviews
-- Join: order_id
-- Solução: subquery classifica a faixa primeiro, query externa agrupa
-- ============================================================
SELECT faixa_atraso,
    COUNT(*) AS total_pedidos,
    ROUND(AVG(review_score)::numeric, 2) AS nota_media,
    COUNT(*) FILTER (
        WHERE review_score = 5
    ) AS nota_5,
    COUNT(*) FILTER (
        WHERE review_score = 4
    ) AS nota_4,
    COUNT(*) FILTER (
        WHERE review_score = 3
    ) AS nota_3,
    COUNT(*) FILTER (
        WHERE review_score = 2
    ) AS nota_2,
    COUNT(*) FILTER (
        WHERE review_score = 1
    ) AS nota_1,
    ROUND(
        COUNT(*) FILTER (
            WHERE review_score <= 2
        )::numeric / COUNT(*) * 100,
        1
    ) AS pct_negativas
FROM (
        -- Subquery: classifica cada pedido na sua faixa de atraso
        SELECT r.review_score,
            CASE
                WHEN o.order_delivered_customer_date::timestamp <= o.order_estimated_delivery_date::timestamp THEN 'No prazo'
                WHEN EXTRACT(
                    EPOCH
                    FROM (
                            o.order_delivered_customer_date::timestamp - o.order_estimated_delivery_date::timestamp
                        )
                ) / 86400 <= 3 THEN 'Atraso leve (1-3 dias)'
                WHEN EXTRACT(
                    EPOCH
                    FROM (
                            o.order_delivered_customer_date::timestamp - o.order_estimated_delivery_date::timestamp
                        )
                ) / 86400 <= 7 THEN 'Atraso moderado (4-7 dias)'
                ELSE 'Atraso grave (8+ dias)'
            END AS faixa_atraso
        FROM raw.orders o
            JOIN raw.order_reviews r ON o.order_id = r.order_id
        WHERE o.order_status = 'delivered'
            AND o.order_delivered_customer_date IS NOT NULL
    ) classified
GROUP BY faixa_atraso
ORDER BY CASE
        faixa_atraso
        WHEN 'No prazo' THEN 1
        WHEN 'Atraso leve (1-3 dias)' THEN 2
        WHEN 'Atraso moderado (4-7 dias)' THEN 3
        ELSE 4
    END;