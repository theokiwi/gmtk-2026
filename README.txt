├── main.py              ← só inicializa e roda o loop
├── config.py            ← constantes: GRAVIDADE, LARGURA, cores
├── jogo/
│   ├── __init__.py
│   ├── render.py        ← SpriteSheet, Animador
│   ├── fisica.py        ← Corpo, colisões
│   ├── entidades.py     ← Personagem, Inimigo
│   ├── recursos.py      ← carrega imagens e sons, monta ANIMACOES
│   └── nivel.py         ← mapa, tiles, câmera
└── assets/
    ├── sprites/
    └── sons/