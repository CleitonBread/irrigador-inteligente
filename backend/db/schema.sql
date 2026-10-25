-- Estrutura do banco de dados do Irrigador Inteligente (SQLite).
-- Pode ser executado várias vezes: só cria o que ainda não existe.

CREATE TABLE IF NOT EXISTS plantas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nome         TEXT    NOT NULL UNIQUE,
    umidade_min  REAL    NOT NULL,   -- abaixo disso a bomba liga
    ideal_min    REAL    NOT NULL,
    ideal_max    REAL    NOT NULL,
    umidade_max  REAL    NOT NULL,
    duracao_s    INTEGER NOT NULL DEFAULT 5   -- tempo de cada rega, em segundos
);

-- Configurações gerais (por enquanto, só a planta ativa).
CREATE TABLE IF NOT EXISTS configuracao (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leituras (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora  TEXT    NOT NULL,     -- formato AAAA-MM-DDTHH:MM:SS
    umidade    REAL    NOT NULL,     -- em %
    bruto      INTEGER,              -- valor cru do A0 (opcional)
    planta_id  INTEGER NOT NULL REFERENCES plantas(id)
);

CREATE TABLE IF NOT EXISTS irrigacoes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora  TEXT    NOT NULL,
    duracao_s  INTEGER NOT NULL,
    motivo     TEXT    NOT NULL,
    planta_id  INTEGER NOT NULL REFERENCES plantas(id)
);
