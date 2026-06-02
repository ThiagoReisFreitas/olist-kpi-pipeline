-- ============================================================
-- KPI: Análise de Meios de Pagamento
-- Tabela: raw.order_payments
-- Regras de negócio:
--   - Exclui registros com payment_type = 'not_defined'
--   - parcelas_medias considera apenas transações acima de 1x
--     (parcela única não é "parcelamento", é pagamento à vista)
-- ============================================================
SELECT
    CASE payment_type
        WHEN 'credit_card' THEN 'Cartão de Crédito'
        WHEN 'boleto'      THEN 'Boleto'
        WHEN 'voucher'     THEN 'Voucher'
        WHEN 'debit_card'  THEN 'Cartão de Débito'
        ELSE payment_type
    END AS tipo_pagamento,
    COUNT(*)                                     AS total_transacoes,
    ROUND(SUM(payment_value)::numeric,  2)       AS valor_total,
    ROUND(AVG(payment_value)::numeric,  2)       AS ticket_medio,
    ROUND(
        AVG(payment_installments) FILTER (
            WHERE payment_installments > 1
        )::numeric,
        1
    )                                            AS parcelas_medias,
    COUNT(*) FILTER (
        WHERE payment_installments > 1
    )                                            AS transacoes_parceladas,
    ROUND(
        COUNT(*) FILTER (WHERE payment_installments > 1)::numeric
        / COUNT(*) * 100,
        1
    )                                            AS pct_parcelado
FROM raw.order_payments
WHERE payment_type != 'not_defined'
GROUP BY 1
ORDER BY total_transacoes DESC;
