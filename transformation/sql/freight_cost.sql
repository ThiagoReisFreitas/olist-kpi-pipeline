-- ============================================================
-- KPI: Custo de Frete por estado
-- Tabelas: raw.orders + raw.order_items + raw.customers
-- Joins: order_id, customer_id
-- Regras de negócio:
--   - Apenas pedidos com status 'delivered'
--   - proporção frete/preço mostra o peso logístico por estado
-- ============================================================
SELECT c.customer_state AS estado,
    COUNT(DISTINCT o.order_id) AS total_pedidos,
    -- Frete médio por pedido
    ROUND(AVG(i.freight_value)::numeric, 2) AS frete_medio,
    -- Frete mediano (menos sensível a outliers)
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY i.freight_value
        )::numeric,
        2
    ) AS frete_mediano,
    -- Ticket médio do produto
    ROUND(AVG(i.price)::numeric, 2) AS ticket_medio,
    -- Proporção frete / preço do produto (%)
    -- Cast ::numeric envolve toda a expressão
    ROUND(
        (AVG(i.freight_value / NULLIF(i.price, 0)) * 100)::numeric,
        1
    ) AS proporcao_frete_pct,
    -- Frete total arrecadado no estado
    ROUND(SUM(i.freight_value)::numeric, 2) AS frete_total,
    -- Receita total de produtos no estado
    ROUND(SUM(i.price)::numeric, 2) AS receita_total
FROM raw.orders o
    JOIN raw.order_items i ON o.order_id = i.order_id
    JOIN raw.customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY frete_medio DESC;