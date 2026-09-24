-- Execute uma única vez no banco controle_emprestimos, antes de iniciar
-- a interface atualizada. Os ativos existentes ficam com empresa NULL
-- até serem editados e associados à Arklok ou à Vivo.

USE controle_emprestimos;

ALTER TABLE ativos
    ADD COLUMN empresa VARCHAR(20) NULL FIRST,
    ADD COLUMN patrimonio VARCHAR(20) NULL AFTER serial_number,
    ADD UNIQUE KEY uq_ativos_patrimonio (patrimonio);
