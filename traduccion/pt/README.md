# Português do Brasil (pt-BR)

Esta tradução usa a versão inglesa como base e o espanhol para conferir o contexto. O código da pasta é `pt`, pois o jogo usa códigos de duas letras e reduz o idioma do sistema a esse código. Os textos são do Brasil; `br` é o código de bretão.

- `pt.json`: catálogo de trabalho completo, com as chaves espanholas intactas.
- `correcciones.json`: correções manuais com prioridade sobre os lotes de tradução. A fusão aplica essas correções aos catálogos de trabalho e do jogo.
- `../../data/idiomas/pt/textos.json`: catálogo carregado pelo jogo, sincronizado com `pt.json`.
- `../../data/idiomas/pt/idioma.json`: identificação da variante brasileira.
- `../../data/idiomas/pt/palabras.json`: glossário auxiliar, com as mesmas chaves da versão inglesa.
- `nombres.json`: glossário dos nomes exibidos. Preserva cidades, bairros, ruas, personagens, marcas e títulos próprios dos mods; traduz o tipo do local e os conectivos ao redor do nome próprio.
- `mods/marisma_negra.json`: tradução do componente opcional, distribuída pelo respectivo `componente.json`.
- As seis guias ficam em `../../data/docs/*_pt.html`. Há instruções de uso em `../../README_pt.txt`, `../../README_pt.md` e `../../data/mods/README_mods_pt.txt`.
- A referência técnica dos mods está em `../../desarrollo/formato_de_los_mods_pt.html`. As regras de contribuição estão em `../../CONTRIBUTING_pt.md`.

Foi usada tradução assistida, com correções de terminologia, instruções de teclado, gênero, nomes e instruções da conversa por IA. Não há gravações de voz em português: o jogo usa a alternativa do leitor de tela que já oferece para novos idiomas.

## Critérios de revisão

Português brasileiro natural, tratamento com «você» e frases claras ao ouvir. São mantidos o cenário litorâneo espanhol, a moeda em euros e o tom dos crimes e da história. Entre os termos revisados estão «gazua», «carregador», «submetralhadora», «lavagem de dinheiro», «acerto de contas», «blindagem» e «sinal sonoro».

Nos locais, traduza a parte descritiva e mantenha o nome próprio. Exemplos: `Cementerio de la Alameda` → `Cemitério da Alameda`, `Armería El Plomo` → `Loja de armas El Plomo`, `Farmacia Luna` → `Farmácia Luna`. `Puerto Bravo`, `Bahía del Ocaso`, `Calle de la Sal`, `Dani Roca` e os títulos dos mods permanecem iguais. Use a mesma forma do glossário nos diálogos, nas missões e nas guias. Confira também a concordância: `ao Gimnasio El Yunque` passa a `à Academia El Yunque`.

Não altere chaves JSON do protocolo, identificadores, comandos, caminhos ou nomes de arquivos. Preserve as variáveis entre chaves e os campos `%s` e `%d`. As marcas `[masculino|feminino]` são resolvidas antes da leitura, assim como no espanhol.

## Verificações

A partir da raiz do projeto:

```bat
.venv\Scripts\python.exe herramientas\i18n\extraer.py --idioma pt
.venv\Scripts\python.exe herramientas\i18n\fusionar.py --idioma pt --instalar --estricto
.venv\Scripts\python.exe -m pytest pruebas\test_172_idiomas.py pruebas\test_172_i18n_servidor.py pruebas\test_traduccion_pt.py
.venv\Scripts\python.exe -m pytest pruebas
```

A extração deve indicar zero pendências. Os testes do português verificam cobertura, sincronização, variáveis, teclas, nomes originais, gênero, partidas entre idiomas, mensagens do servidor, guias e o componente opcional.
