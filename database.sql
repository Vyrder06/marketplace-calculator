
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    marketplace TEXT NOT NULL,
    preco_venda REAL NOT NULL,
    taxa REAL NOT NULL,
    modo TEXT NOT NULL DEFAULT 'Clássico',
    valor_receber REAL NOT NULL
);
