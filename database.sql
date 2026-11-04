CREATE TABLE IF NOT EXISTS produtos (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    nome     TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    enjoei   REAL    CHECK (enjoei   > 0),
    olx      REAL    CHECK (olx      > 0),
    facebook REAL    CHECK (facebook > 0),
    shopee   REAL    CHECK (shopee   > 0),
    vendido  INTEGER NOT NULL DEFAULT 0 CHECK (vendido IN (0, 1))
);

SELECT id, nome, enjoei, olx, facebook, shopee, vendido
FROM produtos
WHERE nome LIKE :busca
  AND (:vendido IS NULL OR vendido = :vendido)
ORDER BY nome;

UPDATE produtos SET vendido = 1 - vendido WHERE id = ?