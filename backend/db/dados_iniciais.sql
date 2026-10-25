-- Dados iniciais do Irrigador Inteligente, tirados da tabela do projeto.
-- INSERT OR IGNORE: se a planta já existe no banco, ela é mantida como está.
-- Por isso, mudar um valor aqui NÃO altera um banco que já foi criado:
-- apague o arquivo db.sqlite3 para recriar do zero.

-- (nome, umidade mínima, ideal mínima, ideal máxima, umidade máxima, duração da rega em segundos)
INSERT OR IGNORE INTO plantas (nome, umidade_min, ideal_min, ideal_max, umidade_max, duracao_s) VALUES
    ('Suculenta',  20, 30, 50, 60, 3),
    ('Manjericão', 40, 50, 70, 80, 5),
    ('Alface',     50, 60, 80, 90, 5),
    ('Girassol',   45, 55, 75, 85, 6);

-- Planta ativa no primeiro uso: Manjericão (depois é trocada pela tela).
INSERT OR IGNORE INTO configuracao (chave, valor)
SELECT 'planta_ativa', CAST(id AS TEXT) FROM plantas WHERE nome = 'Manjericão';
