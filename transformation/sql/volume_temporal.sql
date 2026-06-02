-- ============================================================
-- KPI: Volume e Receita Mensal de Pedidos
-- Tabelas: raw.orders + raw.order_items
-- Regras de negócio:
--   - Apenas Jan/2017 a Ago/2018 (meses com dados completos)
--   - Receita = soma do valor dos produtos (excluindo frete)
--   - Ticket médio = receita / pedidos distintos no mês
-- ============================================================
SELECT
    DATE_TRUNC('month', o.order_purchase_timestamp::timestamp) AS mes,
    COUNT(DISTINCT o.order_id) AS total_pedidos,
    ROUND(SUM(i.price)::numeric, 2) AS receita_total,
    ROUND(
        SUM(i.price)::numeric / NULLIF(COUNT(DISTINCT o.order_id), 0),
        2
    ) AS ticket_medio
FROM raw.orders o
LEFT JOIN raw.order_items i ON o.order_id = i.order_id
WHERE o.order_purchase_timestamp::timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp::timestamp  < '2018-09-01'
GROUP BY 1
ORDER BY 1;
