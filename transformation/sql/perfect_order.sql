-- ============================================================
-- KPI: Perfect Order Rate por estado
-- Tabelas: raw.orders + raw.customers + raw.order_reviews
-- Joins: customer_id, order_id
-- Regras de negócio:
--   - Apenas pedidos com status 'delivered'
--   - Pedido perfeito: entregue no prazo AND review_score >= 4
-- ============================================================
SELECT c.customer_state AS estado,
    COUNT(*) AS total_pedidos,
    -- Pedidos perfeitos: no prazo + nota >= 4
    COUNT(*) FILTER (
        WHERE o.order_delivered_customer_date::timestamp <= o.order_estimated_delivery_date::timestamp
            AND r.review_score >= 4
    ) AS pedidos_perfeitos,
    -- Perfect Order Rate %
    ROUND(
        COUNT(*) FILTER (
            WHERE o.order_delivered_customer_date::timestamp <= o.order_estimated_delivery_date::timestamp
                AND r.review_score >= 4
        )::numeric / COUNT(*) * 100,
        2
    ) AS perfect_order_pct,
    -- Nota média geral do estado
    ROUND(AVG(r.review_score)::numeric, 2) AS nota_media,
    -- Nota média separada: pedidos no prazo vs atrasados
    ROUND(
        AVG(r.review_score) FILTER (
            WHERE o.order_delivered_customer_date::timestamp <= o.order_estimated_delivery_date::timestamp
        )::numeric,
        2
    ) AS nota_media_no_prazo,
    ROUND(
        AVG(r.review_score) FILTER (
            WHERE o.order_delivered_customer_date::timestamp > o.order_estimated_delivery_date::timestamp
        )::numeric,
        2
    ) AS nota_media_atrasado,
    -- Contagem por faixa de avaliação
    COUNT(*) FILTER (
        WHERE r.review_score >= 4
    ) AS avaliacoes_positivas,
    COUNT(*) FILTER (
        WHERE r.review_score = 3
    ) AS avaliacoes_neutras,
    COUNT(*) FILTER (
        WHERE r.review_score <= 2
    ) AS avaliacoes_negativas
FROM raw.orders o
    JOIN raw.customers c ON o.customer_id = c.customer_id
    JOIN raw.order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY perfect_order_pct DESC;