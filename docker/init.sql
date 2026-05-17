-- Script executado automaticamente quando o container sobe pela primeira vez
-- Cria os schemas que vão organizar as camadas do pipeline

-- Camada raw: dados brutos do Olist exatamente como vieram
CREATE SCHEMA IF NOT EXISTS raw;

-- Camada analytics: tabelas de KPIs calculados
CREATE SCHEMA IF NOT EXISTS analytics;

-- Confirma no log do container que o setup rodou
DO $$
BEGIN
  RAISE NOTICE 'Schemas criados: raw, analytics';
END $$;