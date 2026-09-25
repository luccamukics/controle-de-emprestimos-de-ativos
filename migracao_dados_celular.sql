-- Execute uma única vez no banco controle_emprestimos antes de abrir a nova versão.
-- Faça um backup antes. Não execute novamente se as três colunas já existirem.
ALTER TABLE ativos
    ADD COLUMN imei_1 VARCHAR(15) NULL,
    ADD COLUMN imei_2 VARCHAR(15) NULL,
    ADD COLUMN numero_celular VARCHAR(20) NULL;
