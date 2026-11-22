# Como contribuir com Puerto Bravo

Estas são as orientações de contribuição do autor, traduzidas do [original em espanhol](CONTRIBUTING.md).

Obrigado por querer ajudar. Não é preciso saber programar: neste momento, a maior necessidade é de sons.

## Sons: a ajuda mais valiosa

Os sons do jogo podem melhorar bastante, e isso faz muita diferença em um jogo feito para ser ouvido. Você pode ajudar de três formas:

- Um som avulso: substitua o arquivo em `data\sonidos\por_defecto` e informe qual alterou.
- Um pacote completo ou parcial: crie uma pasta dentro de `data\sonidos` com os sons que quiser trocar. Os sons ausentes usam os arquivos originais.
- Conte quais sons incomodam, confundem ou são difíceis de distinguir.

A guia `data\docs\cambiar_sonidos_pt.html` descreve os sons e explica como preparar cada tipo. Dois pontos importantes:

- Os efeitos devem ser mono, pois o jogo os posiciona ao redor do jogador. Os sons ambientes (`amb_...`) e a chuva permanecem em estéreo.
- Só podem ser incluídos sons que possam ser distribuídos livremente: gravados por você, de domínio público ou com licença CC0. Informe a origem de cada um.

## Vozes

Qualquer missão pode ter vozes gravadas. No editor de mods, Ctrl G gera o roteiro: cada frase, quem a diz e o nome do arquivo correspondente. Grave com sua voz ou com vozes sintéticas que você tenha autorização para usar. Não são aceitas vozes clonadas de pessoas reais nem retiradas de outros jogos ou filmes.

## Mods

Com `EditorMods.exe`, você cria lugares, missões, veículos, armas e cidades inteiras sem programar. O conteúdo precisa ser original: não são aceitos mods que copiem mapas, personagens, nomes ou missões de outros jogos.

## Relatar uma falha

Abra uma issue e anexe a pasta compactada da sessão em que ocorreu a falha. Ela fica em `data\logs`, com uma pasta por sessão, e não contém dados pessoais. Se perceber algo estranho durante o jogo, pressione F12 para deixar uma marca no registro.

## Código

- Python 3.15. `entorno.bat` cria o ambiente e `python -m pytest pruebas` executa os testes, que devem continuar passando.
- A acessibilidade é obrigatória: tudo que for novo precisa ser falado, ter seu som e funcionar apenas com teclado.
- Toda mudança percebida pelo jogador deve ser registrada em `data\docs\novedades.html` e no manual. As guias atuais têm o código do idioma no nome, como `novedades_es.html`.
- Dados do jogador não devem aparecer no registro: use `registro.privado()` ou `registro.ocultar()`.
- O README explica a estrutura, a compilação e a publicação.

## O que falta

O trabalho pendente está no `README.md` e nas issues abertas. As maiores necessidades mencionadas pelo autor são sons, tradução para inglês e jogo on-line sem abrir portas.
