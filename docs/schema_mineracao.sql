-- DataPlanner - Grupo EngKids
-- Banco de dados (MySQL / MariaDB - XAMPP)
-- Dominio: operacoes de uma empresa de mineracao (Base 14)
--
-- 6 tabelas em 3a Forma Normal. Os CSVs de carga (pasta tabelas_normalizadas/)
-- sao gerados pela secao 15 do notebook Limpeza_de_Dados_Base14_Mineracao.ipynb.
--
-- A ordem importa: toda tabela "pai" vem antes da que a referencia.

CREATE DATABASE IF NOT EXISTS dataplanner_mineracao;
USE dataplanner_mineracao;

-- =========================================================
-- 1. MINA - estado depende so da mina (mina -> estado),
--    por isso sai da tabela de operacoes
-- =========================================================
CREATE TABLE mina (
  mina_id INT AUTO_INCREMENT PRIMARY KEY,
  nome    VARCHAR(80) NOT NULL UNIQUE,
  estado  CHAR(2)     NOT NULL
);

-- =========================================================
-- 2. FRENTE_LAVRA - a frente F01 da Mina Azul nao e a mesma
--    frente F01 da Mina Brucutu
-- =========================================================
CREATE TABLE frente_lavra (
  frente_id INT AUTO_INCREMENT PRIMARY KEY,
  mina_id   INT        NOT NULL,
  codigo    VARCHAR(5) NOT NULL,
  UNIQUE (mina_id, codigo),
  FOREIGN KEY (mina_id) REFERENCES mina(mina_id)
);

-- =========================================================
-- 3. TIPO_MINERIO
-- =========================================================
CREATE TABLE tipo_minerio (
  tipo_minerio_id INT AUTO_INCREMENT PRIMARY KEY,
  nome            VARCHAR(40) NOT NULL UNIQUE
);

-- =========================================================
-- 4. EQUIPAMENTO - escavadeiras (ESC-xx) e caminhoes (CAM-xxx)
-- =========================================================
CREATE TABLE equipamento (
  equipamento_id INT AUTO_INCREMENT PRIMARY KEY,
  codigo         VARCHAR(10) NOT NULL UNIQUE,
  tipo           VARCHAR(20) NOT NULL  -- escavacao, transporte
);

-- =========================================================
-- 5. OPERADOR
-- =========================================================
CREATE TABLE operador (
  operador_id INT AUTO_INCREMENT PRIMARY KEY,
  codigo      VARCHAR(10) NOT NULL UNIQUE
);

-- =========================================================
-- 6. OPERACAO - tabela principal
--    cada linha e uma operacao: uma frente de lavra, num turno, numa data
--
--    NAO armazenados (derivados, calculados na consulta):
--      rejeito_gerado_t            = massa_processada_t - massa_produto_t
--      recuperacao_metalurgica_pct = massa_produto_t / massa_processada_t * 100
--      ano, mes, dia da semana     = YEAR(), MONTH(), DAYOFWEEK() de data_operacao
--      operacao_com_restricao      = status_operacao <> 'Operação normal'
-- =========================================================
CREATE TABLE operacao (
  registro_id                   VARCHAR(12)   PRIMARY KEY,  -- REG-0000001
  data_operacao                 DATE          NOT NULL,
  frente_id                     INT           NOT NULL,
  turno                         VARCHAR(10)   NOT NULL,     -- Manhã, Tarde, Noite
  tipo_minerio_id               INT           NULL,
  escavadeira_id                INT           NULL,
  caminhao_id                   INT           NULL,
  operador_id                   INT           NOT NULL,
  status_operacao               VARCHAR(30)   NOT NULL,
  -- qualidade do minerio
  teor_fe_pct                   DECIMAL(5,2)  NULL,
  teor_si_pct                   DECIMAL(5,2)  NULL,
  umidade_minerio_pct           DECIMAL(5,2)  NULL,
  granulometria_media_mm        DECIMAL(6,2)  NOT NULL,
  indice_qualidade_minerio      DECIMAL(5,1)  NULL,
  -- producao
  massa_extraida_t              DECIMAL(10,2) NOT NULL,
  massa_processada_t            DECIMAL(10,2) NOT NULL,
  massa_produto_t               DECIMAL(10,2) NOT NULL,
  produtividade_t_h             DECIMAL(8,2)  NOT NULL,
  -- transporte
  distancia_transporte_km       DECIMAL(6,2)  NULL,
  tempo_ciclo_min               DECIMAL(6,1)  NOT NULL,
  qtd_viagens                   INT           NOT NULL,
  -- consumo e emissao
  consumo_diesel_l              DECIMAL(10,2) NULL,
  consumo_diesel_estimado_l     DECIMAL(10,2) NOT NULL,
  consumo_energia_kwh           DECIMAL(10,2) NULL,
  emissao_co2_kg                DECIMAL(10,2) NOT NULL,
  -- equipamento e manutencao
  horas_operacao                DECIMAL(5,2)  NOT NULL,
  horas_parada                  DECIMAL(5,2)  NOT NULL,
  qtd_falhas_equipamento        INT           NOT NULL,
  horas_desde_manutencao        DECIMAL(6,1)  NULL,
  -- custos
  custo_manutencao_rs           DECIMAL(12,2) NULL,
  custo_operacional_rs          DECIMAL(12,2) NOT NULL,
  custo_operacional_estimado_rs DECIMAL(12,2) NOT NULL,
  FOREIGN KEY (frente_id)       REFERENCES frente_lavra(frente_id),
  FOREIGN KEY (tipo_minerio_id) REFERENCES tipo_minerio(tipo_minerio_id),
  FOREIGN KEY (escavadeira_id)  REFERENCES equipamento(equipamento_id),
  FOREIGN KEY (caminhao_id)     REFERENCES equipamento(equipamento_id),
  FOREIGN KEY (operador_id)     REFERENCES operador(operador_id)
);
