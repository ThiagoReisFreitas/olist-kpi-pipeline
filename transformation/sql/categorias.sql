-- ============================================================
-- KPI: Performance por Categoria de Produto
-- Tabelas: raw.order_items + raw.orders + raw.products + translation
-- Regras de negócio:
--   - Apenas pedidos com status 'delivered'
--   - Ticket médio = receita / pedidos (não por item)
--   - Limitado ao top 20 por receita
-- ============================================================
SELECT
    COALESCE(
        t.product_category_name_english,
        p.product_category_name,
        'other'
    ) AS categoria,
    COUNT(DISTINCT o.order_id)        AS total_pedidos,
    ROUND(SUM(i.price)::numeric, 2)   AS receita_total,
    ROUND(
        SUM(i.price)::numeric / NULLIF(COUNT(DISTINCT o.order_id), 0),
        2
    )                                 AS ticket_medio,
    ROUND(AVG(i.freight_value)::numeric, 2) AS frete_medio,
    ROUND(
        (AVG(i.freight_value) / NULLIF(AVG(i.price), 0) * 100)::numeric,
        1
    )                                 AS proporcao_frete_pct
FROM raw.order_items i
JOIN raw.orders o
    ON i.order_id = o.order_id
JOIN raw.products p
    ON i.product_id = p.product_id
LEFT JOIN raw.product_category_name_translation t
    ON p.product_category_name = t.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY 1
ORDER BY receita_total DESC
LIMIT 20;
