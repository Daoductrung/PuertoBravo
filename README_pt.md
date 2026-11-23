# Puerto Bravo: Ley del Asfalto

**Idioma deste documento:** [Español](README.md) · [English](README_en.md) · [Tiếng Việt](README_vi.md) · Português do Brasil

> *Este README também está disponível em espanhol, inglês e vietnamita nos links acima.*

Documentação adicional em português: [como contribuir](CONTRIBUTING_pt.md), [formato técnico dos mods](desarrollo/formato_de_los_mods_pt.html), [instruções do servidor](servidor/despliegue/LEEME_servidor_pt.txt) e [servidor em outros sistemas](servidor/despliegue/LEEME_otros_sistemas_pt.txt).

Um audiogame de mundo aberto, em espanhol, inglês, vietnamita e português do Brasil, totalmente acessível. Você joga só pelo som, com o teclado ou um controle Xbox ou PlayStation e um leitor de tela (NVDA, JAWS ou a voz do Windows). Não é preciso enxergar a tela.

É um jogo original. Sua cidade, sua história, seus personagens e sua música são seus.

Este documento tem quatro partes:

1. [Para jogadores](#1-para-jogadores): o que é o jogo e o que você encontrará nele.
2. [Para desenvolvedores](#2-para-desenvolvedores): configuração do ambiente, teste, construção e publicação.
3. [Criando mods](#3-criando-mods): estendendo o jogo com seu próprio conteúdo.
4. [Pacotes de som e música](#4-pacotes-de-som-e-música): alterando a forma como soa.

---

## Uma nota sobre os sons

Quero ser sincero com quem leu até aqui: sou desenvolvedor e som não é meu forte. Por falta de tempo e conhecimento, a maioria dos sons do jogo são gerados pelo próprio programa ou retirados de sites que oferecem gravações isentas de royalties. Eu sei que eles são ruins, e que em um jogo de áudio som é quase tudo: com sons bons, escolhidos por pessoas que entendem de áudio e conhecem o jogo, o Puerto Bravo ganharia muito.

É por isso que estou aberto a qualquer colaboração com pacotes de sons, sejam pacotes completos ou apenas alguns sons. Se você gostaria de ajudar:

- O guia `data\docs\cambiar_sonidos_pt.html` (também em espanhol, `cambiar_sonidos_es.html`) explica o que é cada som, o que significa ouvi-lo, quanto tempo dura o original e como montar um pack. A seção [Pacotes de som e música](#4-pacotes-de-som-e-música) resume tudo.
- As gravações devem ser compartilháveis ​​com o jogo: próprias ou sob licença gratuita (CC0 ou similar), informando a origem de cada uma.
- Para enviá-lo para mim, abra um [issue no GitHub](https://github.com/hxebolax/PuertoBravo/issues) com um link para download do pacote (ou o ZIP anexado, se couber), ou escreva para mim em Mastodon em [@HXeBoLaX](https://comunidad.nvda.es/@HXeBoLaX). Se você conhece Git, uma pull request com o pacote em sua própria pasta em `data\sonidos` também é bem-vinda.

Qualquer ajuda, por menor que seja, será muito apreciada. Agradeço antecipadamente.

## Sobre as traduções

O autor preparou a versão inglesa do jogo e deste README com ajuda de inteligência artificial. A tradução para português do Brasil usa essa versão como base, com revisão de terminologia, instruções, gênero e nomes próprios. Os nomes próprios do jogo, das cidades, dos personagens, das marcas e dos mods foram preservados. Os tipos de locais são traduzidos, como Cemitério da Alameda, Farmácia Luna e Loja de armas El Plomo. Correções de linguagem são bem-vindas.

O pacote brasileiro usa o código `pt`, compatível com a seleção de idiomas do jogo. Inclui o catálogo, as seis guias, este README e as instruções de uso. Não inclui gravações de vozes em português: as cenas são faladas pelo leitor de tela.

Qualquer correção é muito bem-vinda, assim como qualquer pessoa que queira traduzir o jogo para outro idioma. Se você gostaria de ajudar:

- Para reportar um erro, abra um [issue no GitHub](https://github.com/hxebolax/PuertoBravo/issues) dizendo onde ele aparece e como deve ser lido, ou escreva para mim no Mastodon em [@HXeBoLaX](https://comunidad.nvda.es/@HXeBoLaX).
- Se desejar traduzir o jogo, o manual explica como funciona a tradução na seção “Traduzindo o jogo para outro idioma” (`data\docs\manual_pt.html`). Cada idioma é uma pasta em `data\idiomas`.
- Se você conhece Git, uma pull request também é bem-vinda.

Obrigado pela sua paciência e por qualquer ajuda.

## Este documento em outros idiomas

Cada idioma possui seu próprio arquivo próximo a este, com o código do idioma de duas letras no final do nome, assim como os guias do jogo: `README_en.md` é inglês e `README_it.md` seria italiano. Se você traduzir o README para outro idioma, adicione o link para a linha do idioma no topo de cada README existente.

---

## 1. Para jogadores

### A história

Você escolhe um personagem ou cria o seu próprio com nome, habilidades e uma vantagem inicial, e decide se será tratado como homem ou como mulher. Com o primeiro personagem você é Dani Roca e acaba de ser libertado da prisão após cumprir três anos por um roubo que não cometeu. Você retorna para sua cidade, Puerto Bravo, que agora é controlada pelo empresário Octavio Belmonte. A partir daí, faça o que quiser: acompanhe a história, ganhe a vida honestamente, ganhe fama nas ruas ou passe os dias pescando. O jogo nunca força você a nada.

### Como jogar sem visão

Tudo o que acontece tem um som próprio, colocado ao seu redor: o que soa à direita está à direita, e o que soa abafado está atrás de você. É por isso que você precisa de fones de ouvido. Você também tem muitas ajudas, todas opcionais:

- Uma tecla que informa onde você está: a rua, em quais avenidas você está, o bairro e para que lado você está voltado.
- Um scanner direcional que funciona como uma bengala: o que está na frente, atrás e nas laterais e a quantos metros está a parede.
- Um radar que varre o que está próximo, com distância e direção, reproduzindo cada coisa de onde está.
- GPS falado, com sinal sonoro que marca o caminho, para qualquer lugar de qualquer cidade.
- Um explorador de mapas para conhecer as ruas sem mover seu personagem.
- Caminhando sozinho e no piloto automático do GPS: o personagem ou o carro segue o percurso enquanto você ouve.
- Condução assistida: o automóvel mantém-se na sua faixa; você decide a velocidade e para onde virar.
- Semáforos sonoros, passos que soam diferentes em cada superfície e um som próprio para cada tipo de local.
- Duas assistências para explorar sem pressão: não sofrer danos e jogar sem polícia.

### O que há no mundo

- Nove mapas como padrão: as cidades Puerto Bravo, San Lucero e Monteferro; os municípios de Villaseca, Cala Brava e Fuentefría; Isla Tortuga, o Plataforma Neptuno e o Mar de Poniente, que você pode navegar. Os mods incluídos adicionam mais três cidades e uma ilha.
- Mais de 300 locais padrão: casas, lojas, bancos, oficinas, casinos, ginásios, cinemas, hospitais, cais, helipontos, paragens de eléctrico, estações ferroviárias, aeroportos e monumentos, cada um com som e descrição próprios. Quase todos os locais e casas podem ser percorridos por dentro, cômodo por cômodo.
- 75 missões padrão na história principal, missões secundárias e cinco tutoriais jogáveis, além de trabalhos que se repetem indefinidamente. Os mods adicionam quase setenta a mais. Algumas missões são jogadas de ouvido (seguir os passos de alguém, vigiar, entrar sem fazer barulho, corridas contra rivais), e algumas decisões mudam o que vem a seguir: quatro delas abrem ramificações diferentes, com dez finais.
- 39 veículos: automóveis, motos, bicicletas, caminhões, veículos de emergência, barcos, helicóptero e avião leve. 22 armas, com silenciadores e carregadores estendidos.
- Transporte público: bonde com paradas em todos os bairros das cidades e trilhos que você atravessa a pé, trens entre cidades, ônibus, táxis e aviões de passageiros, todos com viagens reais.
- Você pode navegar no mar, além de nadar e mergulhar nele.
- Polícia com cinco níveis de procurados, dia e noite, chuva, trânsito com semáforos e pedestres.

### O que você pode fazer

- Uma vida honesta: centro de emprego, comércios com promoções (taxista, motorista de ambulância e ônibus, bombeiro, operador de guindaste, entregador, transportador, vendedor de sorvete, pescador), cursos, voluntariado e negócios próprios.
- Uma vida de crime: a história, contratos, empregos em automóveis, roubos e guerras territoriais.
- Lazer: corridas e regatas, casino, bingo, lotaria, sete e meio, dominó, jogo de adivinhação de moedas, boxe, campo de tiro, pesca, caça ao tesouro, cinema, salões de jogos e bolsa de valores.
- Casas com garagens, um cachorro que te faz companhia e encontra coisas, guarda-costas, uma gangue própria, bairros para defender, atualizações de veículos na oficina, conquistas e habilidades que melhoram com a prática.
- Conversar com qualquer pessoa na rua: cada pessoa tem seu nome, profissão e personalidade. Você pode fazer perguntas, comprar um café para eles, fazer amigos ou digitar o que quiser. Um modo opcional permite que eles respondam como se fossem jogados por uma inteligência artificial: um modelo local gratuito que não precisa de internet, Google AI Studio, OpenAI, Anthropic ou outro serviço compatível. O jogo escolhe sozinho o modelo mais barato.
- Vozes nas cenas: cada personagem da história e dos mods incluídos possui sua própria voz, gerada por computador. Eles chamam você pelo nome do personagem que você está interpretando e se dirigem a você como homem ou como mulher; com um personagem que você criou, as linhas que dizem o seu nome são geradas no seu computador. Qualquer pessoa pode adicionar suas próprias gravações. Eles podem ser desligados nas opções.
- Dois motores de som: o clássico e um surround, binaural, com eco diferente em cada local.
- Sem inteligência artificial, uma base de mais de mil e cem linhas em quase setenta tópicos (`juego/respuestas.py`) responde o que você digita, de acordo com a personalidade de cada pessoa.
- Uma cidade que nunca se repete: cada dia é diferente (vendas, dia de mercado, festival, greve, correria de férias), e os preços, as pessoas e o trânsito mudam. Não existem dois jogos iguais.
- Realismo ao seu gosto, tudo opcional: fome, sede, sono e higiene; postos de combustível e gasolina; avarias, pneus furados e manutenção; e regras de trânsito com multas e licença por pontos.
- Jogando em um servidor: um mundo que permanece vivo com jogadores, gangues, territórios, casas e negócios reais, e com trânsito, pessoas e polícia iguais para todos. Qualquer um pode configurar o seu: o servidor acompanha o jogo, com painel acessível para executá-lo e passo a passo.
- O rádio faz uma pausa quando você sai e continua de onde parou; com um player e fones de ouvido você também pode ouvi-lo a pé, e ele toca ao fundo dentro dos locais.
- Jogar com amigos, sem servidores de mais ninguém: o seu próprio jogo hospeda a sessão, com ou sem senha, e você fornece um endereço a eles. Vocês se ouvem, se encontram com o radar e o GPS, se escrevem, andam no mesmo carro, correm com apostas e fazem entregas em equipe.
- Sete rádios com músicas originais, uma emissora de notícias que comenta o que você faz e outra com sua própria música. Música ambiente que muda conforme a situação.
- Modo opcional para maiores de 18 anos, desativado por padrão: relacionamentos, vida noturna, substâncias e suas consequências, contadas sem cenas explícitas.

### Requisitos e primeiros passos

- Windows 10 ou 11.
- Fones de ouvido estéreo.
- Um leitor de tela em execução, como NVDA ou JAWS. Se não houver, o jogo fala com a voz Windows.

Baixe a versão mais recente, descompacte a pasta onde quiser e execute `PuertoBravo.exe`. Não instala nada: é portátil. Dentro do jogo, `F1` informa as teclas a qualquer momento, e o menu principal abre o manual completo, que está em `data\docs\manual_pt.html` (e em espanhol, `manual_es.html`) e pode ser navegado por títulos. O jogo usa o idioma do Windows, espanhol, inglês, vietnamita ou português do Brasil, e você pode escolher em Opções, Idioma. As novidades de cada versão são escritas em espanhol e em inglês: com o jogo em espanhol você as lê em espanhol, e com qualquer outro idioma, em inglês.

Se algo der errado, o jogo mantém um log de cada sessão em `data\logs`, sem dados pessoais: compacte a pasta da sessão e anexe-a a um [issue](https://github.com/hxebolax/PuertoBravo/issues), ou envie em Mastodon para [@HXeBoLaX](https://comunidad.nvda.es/@HXeBoLaX). O manual explica como.

O jogo se atualiza a partir de suas próprias opções. Você pode escolher de onde: o servidor do jogo, GitHub, ambos, ou um endereço próprio. Seus jogos salvos, suas opções, suas músicas e seus mods permanecem intactos.

---

## 2. Para desenvolvedores

### Requisitos

- Windows 10 ou 11.
- Python 3.13 ou posterior. É desenvolvido com Python 3.15.

### Primeiros passos

Tudo é feito com os arquivos `.bat` na pasta raiz:

```bat
entorno.bat    :: cria o ambiente virtual .venv e instala as dependências
jugar.bat      :: abre o jogo a partir do código-fonte
editor.bat     :: abre o editor de mods
probar.bat     :: executa os testes automatizados
compilar.bat   :: gera dist\PuertoBravo, portátil e pronto para distribuir
publicar.bat   :: compacta, assina e publica a versão compilada
```

Na ordem: `entorno.bat` cria o ambiente virtual `.venv` e instala as dependências; `jugar.bat` abre o jogo a partir do código-fonte; `editor.bat` abre o editor de mod; `probar.bat` executa os testes automatizados; `compilar.bat` constrói `dist\PuertoBravo`, portátil e pronto para compartilhar; `publicar.bat` compacta, assina e publica a versão construída.

Dependências (`requirements.txt`): pygame-ce, numpy, sounddevice, soundfile, accessible-output2, wxPython, cx_Freeze e pytest. O modo AI não precisa de nenhum pacote: ele conversa com os serviços via HTTPS com a biblioteca padrão (`juego/ia.py`), pede a cada um sua lista de modelos e escolhe um da linha mais barata.

O repositório inclui o áudio: os sons padrão e os quatro packs em `data/sonidos` (o pack Envolvente vem junto com `herramientas/crear_pack_envolvente.py`), a música de rádio em `data/radio` e a música ambiente em `data/musica`. Se algum som padrão estiver faltando, o jogo o gera novamente na inicialização.

### Estrutura

- `juego/`: código do jogo. `app.py` é o loop e a pilha de telas; `partida.py` monta a sessão de jogo a partir de módulos por tópico (condução, combate, missões, empregos, vida honesta, conversação, jogo em rede, aleatoriedade diária...); `sintesis.py` gera os sons padrão; `audio.py` é o mixer com som posicional.
- `editor/`: o editor de mod, com wxPython.
- `herramientas/`: geração de som e guia, proteção e verificação da construção, montagem de pack, mods integrados e publicação.
- `pruebas/`: testes automatizados com pytest.
- `data/datos/`: mapas, locais, missões, armas, veículos, personagens e as pessoas na rua com seus inimigos, em JSON.
- `data/mods/`: os mods integrados, em JSON legível.
- `data/docs/`: documentação que acompanha o jogo, destinada apenas aos jogadores.
- `desarrollo/`: documentação técnica que não é enviada, como formato dos arquivos mod.

### O servidor on-line

O servidor (`servidor/`) usa apenas a biblioteca padrão do Python e funciona sem o jogo, em Windows, Linux, Mac, NAS ou Docker. Não carrega o conteúdo: locais, armas, veículos e missões são dados pelo jogo da primeira pessoa que adere a cada versão, assinada pela editora, e diferentes versões coexistem no mesmo servidor. Suas opções estão descritas em um único lugar, `servidor/opciones.py`, a partir do qual são produzidos o arquivo de exemplo, a validação, a caixa de diálogo de configuração do painel e o guia. O painel (`panel_servidor/`, `servidor_panel.py`) é uma janela wxPython que reutiliza a acessibilidade do editor de mod. Em desenvolvimento é iniciado com `servidor.bat` ou `servidor_panel.bat`. O guia para quem configura é `data\docs\servidor_pt.html`. `herramientas\prueba_servidor_real.py` inicia um servidor real como um processo separado e conecta dez clientes a ele pela rede.

#### Protocolo: o que foi adicionado em 1.7.1

A versão do protocolo não muda (`VERSION_RED = 2`). Tudo o que é novo é opcional: campos adicionados a mensagens que já existiam e novas mensagens que uma extremidade mais antiga ignora. A regra é dupla:

- O jogo diz em sua saudação o que entende: `hola.sabe`, uma lista (`enlinea.SABE`: `rol`, `radio`, `pasajeros`, `mis_vehiculos`, `topes`, `encargos`). Um servidor mais antigo não olha para isso. O novo servidor o armazena em `Jugador.sabe` e conversa com quem não o envia como faria com um jogo 1.7.0.
- O servidor diz o que pode fazer em `ok.funciones` (`nucleo.FUNCIONES`, com essas mesmas seis palavras adicionadas). O jogo verifica com `Partida.sv_sabe(que)` antes de usar qualquer coisa nova; com um servidor mais antigo, ele diz isso em uma frase e não envia a mensagem.

O que viaja:

- **Passageiros** (o passageiro atropelado). `estado.e.pj`: o identificador da sessão do jogador em cujo veículo você está. O servidor também sabe disso pelas mensagens `act` com `que` igual a `sube` ou `baja`, que 1.7.0 já enviou. `Servidor._va_con(o)` devolve o motorista caso ele ainda esteja ao volante, na mesma cidade e a menos de 45 metros de distância; com isso, `_m_atropello` não aceita atropelamento, `_m_atraco` não deixa que sejam assaltados “a pé”, e `_m_ataque` e `_m_explosion` lhes dão a proteção da carroceria. O registro de posição carrega `pj` quando relevante. No jogo, o motorista não relata atropelar quem está dentro (`sv["pasajeros"]`, atualizado com `act` e `Remoto.pasajero_de`): isso também funciona contra um servidor mais antigo.
- **Rádio veicular**. `estado.e.ra`: o identificador curto da estação, somente se for padrão (`Radio.comunes()`), ela está tocando e você está ao volante. O servidor o valida (texto de até 24 letras, números ou sublinhados), armazena em `Jugador.radio` e coloca no registro como `ra`. Nenhum áudio viaja, nem caminhos, nem nada de "Minha música". O jogo que o ouve carrega um trecho de sua própria cópia (`Radio.muestra`, em um thread) e faz um loop do veículo (`EnLinea._sv_radio_ajena`). Opção de jogo `radio_coches`; opção de servidor, `radio_coches`.
- **Roleplay**. `chat.canal` também aceita `ic` (em personagem), `yo` (ação) e `ooc` (fora de personagem). `ic` e `yo` alcançam `rol_metros`; `ooc`, pessoal. Para um jogo que não conhece `rol`, o servidor o envia através de `cerca` ou `todos` com algumas palavras na frente. Os comandos `/yo`, `/me`, `/ep`, `/ic`, `/fp`, `/ooc` e `/ficha` são interpretados pelo servidor em qualquer mensagem de chat, antes das de administração, portanto funcionam a partir de um jogo mais antigo. `rol_oido` (`canal`, `n`) informa ao palestrante quantas pessoas os ouviram. `ficha` com `texto` define seu próprio perfil (ele é armazenado na coluna `ficha` de `cuentas` e retorna em `ok.ficha`); com `a`, ele pede o de outra pessoa e a resposta é `ficha` com `de`, `nombre` e `texto`.
- **Meus veículos**. `veh_nombre` (`id`, `nombre`), `veh_traer` (`id`, `x`, `y`, `r`) e `veh_guardar` (`id`, `ref`), apenas para veículo estacionado cujo proprietário é quem solicita. A resposta é `veh_mio` com `que` igual a `nombre`, `traer`, `garaje` ou `no` (com `motivo`). Todos os outros recebem o `veh_libre` e `veh_fuera` habituais, então um jogo mais antigo vê isso corretamente. A garagem ainda é assunto do jogo: o servidor devolve o registro e retira o veículo da rua; o jogo coloca em `j.garajes`, carrega e salva.
- **Limites de dinheiro**. `ok.servidor.economia`, a mensagem `saldo` e a resposta a `economia` carregam `tope`, `acumula`, `horas`, `margen`, `por_minuto`, `encargos_hora` e `encargo_max`; `saldo` também carrega `ganado` e `aceptado`. A margem é armazenada na conta (colunas `margen` e `t_margen`) e acumulada por até `ganancia_acumula` horas.
- **Trabalhos repetíveis**. `mision_ok` com `encargo: 1` e `n` (o pagamento) para uma missão que o mundo do servidor não conhece: o `id` é do tipo (`contrato`, `atraco_banco`, `atraco_local`, `asalto_proveedor`, `encargo_coche`, `conquista`, `defensa` ou o identificador de uma luta). O servidor reconhece até `encargos_hora` por hora e tipo, sendo o máximo dado por `mundo["encargos"]` (calculado por `enlinea.encargos_para_servidor` a partir dos dados do jogo) ou, se o mundo não incluir, `nucleo.ENCARGOS_DE_SERIE`, e nunca mais que `encargo_max`. O pagamento reconhecido é válido por trinta segundos (`Jugador.fiado`).
- **Compras e queda de conexões**. No jogo, `_sv_vigilar_gasto` envia um `guardar` dois segundos e meio depois que o dinheiro cai (e não mais do que um a cada doze segundos se os gastos continuarem). No servidor, `Jugador.gasto_pend` soma o que o jogador vê gastando por conta própria desde o último `guardar`, e `total_guardado` é o dinheiro economizado do personagem; ao sair (`_salida`), `_devolver_sin_guardar` retorna a menor das duas lacunas à balança. Nem o que o servidor leva (`Jugador.descuento`) nem as casas já pagas contam.
- **Grupo da missão**. Os inimigos relatados aos companheiros de equipe também carregam `deportivo`, `punteria` e `tono`.
- **Polícia compartilhada**. A fileira de cada oficial carrega um sexto valor, sua saúde.
- **Mundo**. `mundo_servidor()` adiciona `encargos` e `gente.frases` (o que dizem os personagens do servidor, por classe). Eles não fazem parte da impressão digital.

#### Versões diferentes no mesmo servidor (1.7.1)

Princípio: duas pessoas com versões diferentes do jogo devem poder jogar juntas e, além disso, em pé de igualdade possível. Uma conexão só é rejeitada por versão com a opção `version_minima`. O protocolo permanece na versão 2; o servidor adiciona `equivalencias` e `nominas` a `ok.funciones`. A parte do servidor que não depende do resto está em `servidor/compat.py`.

**O que viaja do jogo para o servidor e o que não.** O servidor não possui o jogo: o que ele conhece do mundo é o texto de `enlinea.mundo_servidor()`, que o jogo de quem entra lhe dá (`pide_mundo` e `mundo`, compactado) ou que acompanha em `servidor/mundo.json`.

- O que viaja: para cada cidade, seus locais (identificador, tipo, nome, coordenadas, preço, renda), seus bairros, suas ruas e seus carros; para cada arma, seu tipo, dano, alcance, cadência de tiro, precisão, raio e se é automática; para cada veículo, sua saúde, velocidade, aceleração, frenagem e se voa; para cada missão, seu título, seu salário e se ela se repete; os nomes e falas dos personagens do servidor, a tabela policial, o máximo que cada cargo repetível paga (`encargos`) e os contratos fixos com suas folhas de pagamento (`empleos`: período, bônus e, por cargo, os turnos e salário de cada cargo).
- O que não viaja: sons, textos de missão, etapas de missão e inimigos, lojas e preços, itens, roupas, comida, empregos, toda a vida honesta exceto folhas de pagamento, opções de cada jogador ou qualquer coisa de seu computador. Tudo isso é fornecido pelo jogo de cada jogador.
- A impressão digital (`enlinea.huella_datos`) abrange apenas identificadores de cidades, lugares, bairros, veículos e missões, e os números das armas. Tudo o mais que o mundo inclui (`encargos`, `gente`, `policia`, `empleos`) não faz parte dele: é por isso que, se o mundo salvo pelo servidor (`mundo_actual.json`) e aquele que o acompanha (`mundo.json`) tiverem a mesma impressão digital, aquele com o qual ele é enviado vence na inicialização.

**Quem fornece o mundo** (`Servidor._admitir_mundo`). É chamado quando a impressão digital de quem entra não é a do servidor, se `comprobar_datos` for `si` ou o servidor não tiver mundo.

| Caso | O que o servidor faz |
|---|---|
| Servidor vazio, mundo assinado | Adota. |
| Servidor vazio, mundo não assinado | Com `mundo_distinto = admitir` e `actualizar_mundo` diferentes de `no`, adota-o marcado como `provisional`; é substituído pelo primeiro assinado que chegar, qualquer que seja sua versão, ou por um administrador com `actualizar_mundo = admin`. Caso contrário, rejeita-o com uma mensagem clara. |
| Mundo assinado de uma versão mais recente | Adota (`actualizar_mundo` definido como `firmado` ou `admin`), anuncia e não expulsa ninguém. |
| Mundo conhecido (`mundos_conocidos`, ou `compat.CATALOGOS`, que são os das versões publicadas) | Deixa o jogador entrar sem pedir nada. |
| Mundo assinado que não conhecia, da mesma idade ou mais | Verifica, lembra e deixa o jogador entrar. |
| Mundo não assinado (mods) | Com `mundo_distinto = admitir`, o padrão, o jogador entra: o servidor pede seu mundo apenas para saber o que seu jogo sabe durante aquela sessão (`Jugador.cat`), e nada dele é salvo. Com `rechazar`, ou com `versiones = iguales`, o jogador não entra. |

**Equivalências.** De cada mundo verificado o servidor mantém um catálogo (`compat.catalogo_de`: identificadores de armas e veículos; `meta.catalogos` e `compat.CATALOGOS` para as versões publicadas). `Servidor._cat(j)` fornece o catálogo do jogo de um jogador se sua impressão digital não for a do servidor. Com isso:

- `Servidor._enviar` passa as mensagens em `TRADUCIBLES` através de `_traducir`: `tiro`, `herido` e `po_disparo` (a arma), `evento` com `d:<arma>`, `veh_ocupado`, `veh_libre`, `veh_ok` e `veh_mio` (o modelo), `ok` (os veículos estacionados) e `grupo_msg` com os inimigos de uma missão (sua arma). Tudo o que o jogo não conhece é substituído pela coisa mais próxima que ele conhece (`compat.arma_equivalente`: mesma classe, depois números, nome e se é automático; `compat.modelo_equivalente`: se voa ou não, depois números e nome). `_repartir_estados` faz o mesmo com o veículo que cada jogador dirige.
- O dano não é tocado: `_m_ataque` e `_m_explosion` calculam com os números do mundo do servidor antes de traduzir qualquer coisa, e os demais recebem o nome da arma que o servidor contou, não aquela que diz a mensagem.
- `_m_dar` devolve ao doador uma arma ou munição que o outro jogador não pode receber.
- Se for o servidor que não sabe de algo (seu mundo é mais antigo que o do jogador), nenhuma equivalência se aplica: a arma conta como mãos nuas, o veículo como `utilitario` e a cidade fica de fora, com aviso ao jogador. É o mesmo para todos.
- Na adesão, `ok.mundo.distinto` (`faltan` e `sobran`, com nomes de armas e veículos) e um `aviso` com o mesmo conteúdo em uma frase (`compat.texto_diferencias`).

**O personagem.** `cuentas.partida` armazena todo o JSON que o jogo envia, incluindo tudo o que o servidor não conhece (limite: `MAX_LINEA`, 600 KB; se não couber, não é salvo e um aviso é dado). `cuentas.partida_juego` é a versão mais recente do jogo que salvou esse personagem.

- Ao ingressar em um jogo que não sabe tudo o que o personagem carrega, `compat.adaptar_partida` lhe dá uma cópia sem as armas ou veículos de garagem que ele não possui (um jogo 1.7.0 falha ao trocar de armas se estiver segurando uma que não conhece). O banco de dados não é tocado.
- Ao salvar com um jogo anterior a `partida_juego`, `compat.fundir_partida` restaura o que aquele jogo não pode salvar: as chaves root e `jugador` que estão faltando (o jogo 1.7.0 descarta aquelas que não conhece ao carregar), as armas que não conhece e os veículos de garagem que não conhece. Pelo que sabe, o que diz vale.

**Folhas de pagamento** (`_m_contrato`, `cuentas.contrato`). A mensagem `contrato` com `que`: `firmar` (`empleo`, `puesto` 0 ou 1), `turno`, `cobrar` (`buena`, `mala`), `ascenso` e `dejar`. O servidor responde com `contrato` (`que`: `firmado`, `turno`, `puesto` ou `no` e `c` com `empleo`, `puesto`, `turnos`, `fin`, `periodo`, `tope`, `turnos_dia`) ou `nomina` (`n`, `turnos`, `cupo`, `faltan`). O dinheiro em `nomina` é registrado como crédito justificado (`_enviar`), assim como `dinero`. O que o servidor decide: turnos por dia (`nomina_turnos_dia`), o dia de pagamento (`fin`, em dias de servidor), o valor (salário do cargo em `mundo["empleos"]`, proporcional aos turnos, mais o bônus se a cota for cumprida e a avaliação for boa, limitado a `nomina_max`) e que uma posição só é elevada após um período com a cota atingida. O jogo (`honrado.py`: `_hon_sv_contrato`, `_hon_nomina`, `hon_sv_al_entrar`, `_svm_contrato`, `_svm_nomina`) cumpre o contrato da mesma forma que offline e só deixa o dinheiro nas mãos do servidor. `ok.servidor.nominas` e `ok.servidor.trato_prestigio` dizem se esse servidor cuida da folha de pagamento e se as lojas tratam você de acordo com seu prestígio; `Partida.sv_honrado(que)` verifica.

**Novas opções de servidor**: `mundo_distinto` (`admitir`), `nominas` (`si`), `nomina_max` (1500), `nomina_turnos_dia` (3) e `trato_prestigio` (`si`).

**Ao publicar uma versão que altere armas ou veículos**, registre o catálogo da versão deixada para trás em `compat.CATALOGOS`: `.venv\Scripts\python.exe herramientas\exportar_mundo_servidor.py --catalogo` escreve a entrada para o mundo atual, pronta para colar. Dessa forma, novos servidores conhecem essa versão sem precisar solicitar nada.

**Testes em relação à versão anterior real**: `pruebas/test_171_versiones.py` extrai o código 1.7.0 publicado com `git archive` para uma pasta temporária (`pruebas/banco_versiones.py`) e o executa em processos separados (`pruebas/agente_versiones.py`), nunca misturado com o código atual. Se não houver git ou faltar o commit, esses testes serão ignorados, informando o porquê.

**Limites conhecidos.** Um servidor 1.7.0 não traduz nada e não restaura o personagem: quem entra nele com um jogo mais antigo que seu mundo não ouve as novas armas (seu jogo as ignora) e não vê os novos veículos estacionados. As novas cidades não têm equivalente: quem não as tem não consegue ver quem está nelas. Itens, roupas e alimentos não estão no mundo do servidor, por isso não é verificado se o destinatário os conhece (o jogo 1.7.0 já diz que não pode recebê-los). O tráfego do servidor utiliza os modelos do seu mundo; um jogo mais antigo coloca um `utilitario` onde não conhece o modelo.

#### Desligamento ordenado, aviso de atualização e reconexão (1.7.1)

A versão do protocolo também não muda aqui. O jogo adiciona `reconexion` a `hola.sabe` e o servidor a `ok.funciones`.

**O servidor.** `Servidor.detener(motivo, causa, aviso, vuelve, espera, codigo)` é a única maneira de parar e agora faz as coisas em ordem:

1. Se `causa` for `actualizacion` ou `reinicio` e houver um `aviso`, uma contagem regressiva: para cada jogo que conhece `reconexion` ele envia `parada` (`causa`, `en` segundos, `vuelve` segundos estimados); para o resto, um `aviso` normal com o mesmo conteúdo do texto. É repetido quando restam 60, 30 e 10 segundos (`AVISOS_PARADA`). Qualquer pessoa que ingressar durante a contagem regressiva receberá ao ingressar.
2. `cerrando = True` (ninguém mais entra: `rechazo` com `codigo: "reiniciando"`) e envia a todos `cerrado` com `motivo` (texto que um jogo mais antigo entende), `causa` (`apagado`, `actualizacion`, `reinicio`) e `vuelve`.
3. Aguarda o último `guardar` de cada jogo com `ya` (`_guardan`), por até `parada_espera` segundos e nunca menos que dois décimos de segundo. Um jogo, novo ou 1.7.0, responde a `cerrado` salvando e dizendo adeus, portanto nenhuma outra mensagem é necessária.
4. Leva cada jogador para fora pelo `_salida` (veículo estacionado, `_devolver_sin_guardar`, `_guardar_saldo`), registra em `meta.buscados` quem era procurado pela polícia, salva tudo e fecha. Deixa `causa_parada` e `codigo_salida` (75, `CODIGO_VUELVE`, se parou para voltar; 0 caso contrário).

Como é solicitado de fora do processo: o arquivo `parar.txt` (`ARCHIVO_ORDEN`) na pasta de dados, que o próprio servidor verifica a cada segundo em `_bucle_lento` (`_mirar_orden`, `orden_externa`). Sua primeira palavra é `parar`, `actualizar` ou `reiniciar`, seguida opcionalmente pelos segundos de aviso prévio. `python -m servidor --parar | --actualizar | --reiniciar` grava e espera que seja atendido. Os comandos de console e chat `actualizar` e `reiniciar` fazem o mesmo (`parar_para_volver`). O sinal de encerramento (systemd, Docker) e o logoff ou desligamento Windows param com `causa="reinicio"`, sem contagem regressiva e aguardando no máximo três segundos; Control+C e fechando a janela, com `apagado`. O painel não utiliza `__main__`: com o servidor rodando o servidor vê o arquivo, e com ele parado a janela verifica (`Motor.orden_pendiente`); se `Motor.causa_parada` for `actualizacion` a janela fecha e se for `reinicio` ela inicia novamente.

Outras alterações no servidor: `rechazo` carrega `codigo` (`version` com `minima`, `lleno`, `reiniciando`); `veh_no` carrega `por` (`no_esta`, `ocupado`, `lejos`); alguém que volta enquanto a sessão anterior ainda está por aí quando um "fantasma" de luta a substitui, herda `golpeado` e `agredio` e entra sem proteção de chegada.

**O jogo.** `enlinea.conectar` retorna o motivo como `Motivo`, uma string com `codigo` e `minima`. `_svm_cerrado` (com um `causa` diferente de `apagado`, ou sem `causa`, o que significa um servidor mais antigo) e `_svm_desconectado` chamam `sv_cortado`: envia um último `guardar` se a conexão ainda estiver ativa, registra em `sv_espera` o que será necessário ser reconstruído (grupo, passageiro, quando foi o último save), limpa o que o servidor configurou (`_sv_limpiar_mundo`), invalida os identificadores dos outros jogadores e abre `reconexion.Espera`. `_svm_expulsado` nunca espera. A sessão de jogo permanece na memória com `en_servidor = True` e `red = None`.

`reconexion.Espera` tenta novamente com as esperas em `ESPERAS` (3, 5, 8, 12 e 15 segundos), em um encadeamento, para `cfg["reconectar_minutos"]`. Dependendo de `codigo_de(motivo)`: `red`, `reiniciando` e `lleno` continue tentando; `version` para de tentar e se oferece para atualizar (deixa `data/config/volver_servidor.json` com o nome e o endereço, e depois de `--tras-actualizar` o jogo se oferece para voltar); `certificado` e qualquer outra rejeição saem para o menu, explicando o porquê. Ao entrar, chama `sv_entrar(enlace, vuelta=True)`: não carrega `ok.partida`, não corta dinheiro com `ok.saldo` (o servidor julga isso com `_cuadrar_saldo` ao receber a posição, como sempre), envia a posição e, quatro décimos de segundo depois, um `guardar` com a sessão de jogo ao vivo. O veículo em que o jogador estava é recuperado com `veh_subir` através do seu número (`sv["reenganche"]`): se o servidor não o tiver mais ou estiver longe, ele é registrado novamente com `veh_tomar`; se outra pessoa estiver dirigindo, o jogador fica a pé. O grupo é reconstruído por nomes (`sv["regrupo"]`): quem o lidera reenvia `grupo_invitar` à medida que os demais entram, e os demais respondem ao convite daquele nome automaticamente, por 180 segundos.

O que não se reconstrói: andar de passageiro (fica a pé), um assalto a empresa em andamento, convites pendentes e a contagem horária de trabalhos repetíveis, que fica na memória do servidor.

**O atualizador.** Cada servidor em execução do jogo construído deixa um registro em `servidor\en_marcha\<pid>.json` (`servidor/enmarcha.py`): tipo (`consola` ou `panel`), executável, argumentos, pasta de trabalho, pasta de dados, configuração, se o servidor está em execução e a sessão Windows. `actualizador.servidores_en_marcha()` os lê, exclui aqueles de processos inativos e marca aqueles de outra sessão como `servicio`. `menus_actualizar._instalar` pede confirmação e `pedir_parada_servidores()` escreve `data\actualizacion\servidores_abiertos.json` e deixa `actualizar` no `parar.txt` de cada pasta de dados. O `.bat` espera os programas fecharem (até três minutos), instala e, dando certo ou não, chama `PuertoBravo.exe --relanzar-servidores <nota>` antes de abrir o jogo: `relanzar_servidores()` inicia cada um com seus argumentos e sua pasta (o painel com `--arrancar` se seu servidor estava rodando), minimizado e sem roubar o foco, e escreve em `actualizacion.log` uma linha `SERVIDOR relanzado tipo=...` ou `SERVIDOR sin_relanzar tipo=... motivo=...`. Apenas inicia o `PuertoBravoServidor.exe` e `PuertoBravoServidorPanel.exe` na própria pasta do jogo. Os testes podem alterar a pasta de registros com a variável de ambiente `PUERTOBRAVO_EN_MARCHA`.

Limites que permanecem: em um servidor, os inimigos da missão chegam a pé mesmo que seu tipo viaje de veículo, e a polícia compartilhada sempre dirige uma viatura; da mesa da polícia tiram a arma, o estado de saúde e quantos policiais tem.

Todo o conteúdo e preços do jogo estão nos arquivos JSON em `data\datos` (o mais novo, em `vida.json`), e o editor de mod possui uma seção para cada coisa.

### Pessoas, inimigos, polícia e caixas registradoras

`data/datos/gente.json` e `juego/gente.py` guardam tudo o que costumavam ser listas escritas no código: nomes, sobrenomes, cargos e linhas de pessoas, personalidades, gangues, o catálogo de tipos de inimigos, a tabela policial por nível de procurado e a caixa registradora de cada tipo de local. `gente.configurar(datos)` é chamado no final de `mundo.cargar_datos()`; tudo o que falta nos dados assume o valor padrão. O que o resto do código usa:

-`gente.lista(cual)`, `gente.nombres(genero)`, `gente.oficio_para(edad, genero, rng)`, `gente.caracter(id)`.
- `gente.enemigo(grupo)` resolve um grupo de uma etapa `eliminar` (com `clase`, ou com nome, arma e saúde como sempre) e `gente.vestir(persona, ficha)` aplica em um `Persona`. `gente.grupo(clase, n, **serie)` grava um grupo que funciona mesmo que o tipo não esteja nos dados.
- `gente.agentes_nivel(nivel)` indica o tipo de oficial para uma patrulha; `gente.banda(nombre)` e `gente.tipos_de_banda(nombre)`, os dados da turma.
- `gente.caja_local(tipo)` e, na sessão de jogo, `caja_de_local(lugar)`: o que está hoje no registro e quem o guarda.
- `Partida.llegar_en_vehiculo(modelo, personas)` traz um grupo em um veículo, com a mesma condução das patrulhas (`ia == "enemigos"`), e `bajar_enemigos(v)` os retira.

Os upgrades de oficina (`juego/sistemas.py`) também vêm dos dados: cada um informa seu `efecto`, da lista `sistemas.EFECTOS`, seus níveis e quanto cada nível dá.

### Meus veículos e o motorista

`juego/misvehiculos.py` (o mixin `MisVehiculos` da sessão de jogo e os menus do telefone):

- O veículo do jogador carrega `v.mio = True` e `v.mio_n` (ordem de idade). `Partida.hacer_mio(v)` marca: é chamado comprando, a primeira atualização da oficina, tirando da garagem, trazendo para você e nomeando. `_poblar` não remove os marcados.
- Os da cidade atual são veículos ativos; aqueles em outras cidades aguardam dados em `Partida.mis_lejos` (`mis_al_cambiar_mapa`, `_reponer_mis_vehiculos`). No jogo salvo vão em `mis_vehiculos`, com `n` e, para o último utilizado, `ultimo`; aquele que você está dirigindo, em `veh` com `mio`. O número do formato não muda: uma versão mais antiga ignora as novas chaves e um jogo salvo mais antigo é carregado sem elas (`mis_cargar`).
- `ultimo_veh` e `veh_fuera` ainda são “o último que você usou”, seja seu ou não; se for seu, não está duplicado em `veh_fuera`.
- O limite (`vehiculos_propios.tope_calle` em `vida.json`) é aplicado por `_tope_mis_vehiculos`.
- Em um servidor nada é marcado ou salvo (`hacer_mio` retorna `False`): os veículos na rua pertencem ao servidor. O servidor adiciona `mis_vehiculos` à sua resposta de junção (os identificadores daqueles estacionados sob o nome da conta) e aceita `nombre` em `veh_dejar`; um jogo ou servidor mais antigo ignora ambos. A partir da lista, um veículo estacionado pode ser renomeado, trazido e enviado para a garagem (`veh_nombre`, `veh_traer`, `veh_guardar`; consulte o protocolo, em O servidor online). O jogo acompanha `sv["mios"]` e `sv_mis_vehiculos()`.
- Missões: `mision_vehiculo(m)` e `mision_vehiculo_txt(m)` dizem o que acontece com o veículo; com `vehiculo_libre`, a etapa `robar` aceita o veículo do jogador (`ms["veh_tuyo"]`) e `entregar` não o leva embora.
- Motorista: `Partida.chofer` é `None` ou um dicionário com `estado` (`espera`, `viene`, `aqui`, `contigo`). O veículo vem com `ia == "chofer"` (`_ia_chofer`); com você dentro, `chofer_conduce()` faz com que `piloto_puesto()` e `modo_asistido()` se apliquem mesmo que o jogador não tenha piloto automático nem direção assistida, e `conducir` ignora os pedais. O veículo da gangue carrega `tag == "banda"`; o da sua garagem não tem marca e é seu. Não é salvo com o jogo.

`mundo_servidor()` também informa ao servidor os nomes de seus personagens (`gente`) e as armas de seus oficiais por nível (`policia`). Estas são duas chaves extras: um servidor mais antigo não as examina e um novo usa as suas próprias se estiverem faltando. A impressão digital mundial não depende deles, mas depende das armas e dos veículos: ao adicionar qualquer um deles, `servidor/mundo.json` deve ser regenerado com `herramientas/exportar_mundo_servidor.py`.

### A rua: autodefesa, patrulhas, rendição, helicóptero e guerras de bairro

- `juego/calle.py` (mixin `Calle` da sessão de jogo) reúne o que acontece na rua sem que o jogador procure. Os números e linhas vêm de `vida.json`, seção `calle`; as opções do jogador, de `config.py` (`defensa_propia`, `frases_reacciones`, `charla_peatones`, `soltar_municion`, `soltar_armas`, `patrullas_calle`, `ambulancias`, `helicoptero_policia`).
- Autodefesa: é marcado um inimigo que ataca sem ter sido tocado (`p.agresor`, em `marcar_agresor`, que é chamado de `actualizar_personas` no momento do ataque). Embora haja um agressor vivo por perto, `_ruido_disparo` não registra nenhum crime, nem derrubá-lo. `agente_auxilia` envia um oficial atrás deles; `herir_por_otro` é a vítima que não conta contra o jogador. Não se aplica aos valores `tag` de missão ou guerra.
- Vozes por gênero: `calle.genero_de(p)` (o perfil se houver; caso contrário, o tom de voz) e `Calle.voz_persona`. `charla.ficha` dá o gênero de acordo com esse mesmo tom. `Calle.asustar` é o único local por onde um pedestre começa a fugir.
- As patrulhas itinerantes são veículos com `ia == "policia"` e `ronda = True`; com zero estrelas eles são movidos por `patrulla_sin_busqueda`, e quando for procurado, pelo código usual. Aqueles que respondem a uma luta carregam `auxilio` (no momento em que desistem).
- A ambulância é um veículo com `ia == "ambulancia"` e `tag == "ambulancia"`; seu estado está em `Partida.ambulancia`.
- Rendição: `Calle.rendirse` define `Partida.rendido`; `actualizar_personas` envia os oficiais para `agente_detiene` e `detener(rendicion=True)` aplica a penalidade de `_pena_rendicion`.
- O helicóptero é um veículo com `ia == "heli_policia"` e `volando = True`, que `actualizar_vehiculos` não se move: é conduzido por `Calle._helicoptero`. Tudo o que passa pelos veículos para bater, frear ou entrar pula aqueles com `volando`. `danar_vehiculo` desvia para `heli_danado`.
- `juego/guerra.py` (o mixin `Guerra`) é o modo de guerra de rua (`guerra_calle`, desativado por padrão; seção `guerra_barrios`). `banda_guerra` dá a cada bairro da cidade uma gangue estável usando a semente do jogo; `miembro_de_barrio` decide quem sai para a rua em `_poblar`; o estado da guerra em andamento está em `Partida.guerra` e não foi salvo.
- Em um servidor: com polícia compartilhada (`sv_policia_comun()`) não há patrulhas itinerantes, nem helicóptero e nem rendição; em qualquer servidor não há ambulâncias, nem armas caídas e nem guerra de vizinhança. `servidor/` não foi tocado.
- Ao tentar novamente uma missão, `Misiones._rebobinar_jugador` retorna o jogador ao que era, mas deixa as garagens como estão: os veículos não voltam.
- Viagens: `Partida.conexion_hacia` primeiro procura uma rota somente rodoviária quando você está ao volante (antes, o ônibus ganhava se fosse mais curto em saltos); `lugar_al_alcance` é o local que o Enter abre (ao volante, o destino GPS ou uma saída antes de outro local mais próximo) e `pista_de_llegada` a frase sobre o que fazer em uma saída, estação ou cais.
- `mundo.Lugar.nombre` e `.desc` são propriedades: com `nombre_conquistado` ou `desc_conquistado` nos dados, eles retornam esse texto quando `Partida.barrio_cambiado(barrio)` diz que o bairro não pertence mais à sua gangue padrão. A sessão do jogo é registrada em `Lugar.cambiado` quando é criada. `Mundo._separar` evita que dois locais compartilhem um ponto.
- `juego/escolta.py` (o mixin `Escolta`, opção `escolta_misiones`: não, moderado ou forte; seção `escolta_misiones`): `Misiones._generar_enemigos` pede `escolta_ajuste`, distribui os inimigos extras com `escolta_grupos` e aumenta a saúde e mira com `escolta_endurecer`.
- `juego/destinos.py` (o mixin `Destinos`, opção `ayuda_persecucion`, seção `persecuciones`): a tecla O (`decir_objetivo`, com `objetivo_donde` para a posição), Shift O (`enfocar_objetivo`), Shift G e Control G (`quitar_gps_jugador`, `recuperar_gps`) e os números de perseguição (`pers`). O modelo de destino está em `Partida.fijar_gps`: um único destino, `self.gps`, e abaixo dele aquele que está aguardando (`anterior`); `quitar_gps_auto` remove o destino da missão ou trabalho sem tocar no que o jogador definiu, e `_gps_cosa_acabada` fecha o desvio para um veículo, uma pessoa ou um item.
- Tentando novamente uma missão (`Misiones.fallar_mision`): `_rebobinar_jugador` não reverte garagens ou barcos; `MisVehiculos.preparar_traslado` e `llevarte_a` levam o veículo que você dirigia com você.
- `Guerra.buscar_pelea(banda, larga)` reutiliza `Partida.guerra` com `tipo == "pelea"`: uma ou duas rodadas, sem vizinhança em jogo e sem necessidade do modo `guerra_calle`.
- Autodefesa: `actualizar_personas` marca como agressor qualquer pessoa que se aproxime de você em um raio de 32 metros, sem esperar o primeiro golpe (`Calle.marcar_agresor`).
- Atualizador: `actualizador.error_de_disco` transforma um erro de gravação Windows em uma frase (`ErrorDisco`), `copias_del_juego` conta quantas vezes está aberto e `menus_actualizar.a_mano` são as etapas para atualizar sem ele.

### Entrega em domicílio, roubos, negócios, contratos, pessoas que atuam, convivência e carreira policial

Oito módulos de 1.7.1, cada um deles um mixin `Partida`, exceto `ajustes.py`:

- `juego/ajustes.py`: a classe `Ajustes(seccion, numeros, listas, cero)` lê dos dados uma seção de elemento único (`{"id": "general", ...}`) com números e listas de linhas, cada uma com seu valor padrão. Cada módulo cria o seu próprio (`AJ = Ajustes(...)`); `mundo.cargar_datos()` os atualiza com `ajustes.configurar_todos(d)`. `AJ("clave")` fornece o número, `AJ.lista("clave")` a lista e `AJ.frase("clave", hueco=valor)` uma linha aleatória com seus espaços reservados preenchidos.
-`juego/domicilio.py` (`Domicilio`): `casa_aqui()`, `pedir_domicilio(cosas)`, `actualizar_domicilio(dt)`. O pedido a caminho está em `Jugador.pedido` e está salvo. Seções `carta_domicilio` (lista) e `domicilio`; taxa `domicilio_envio`.
- `juego/atracos.py` (`Atracos`): `atracar_local(l)` generaliza o roubo de loja com `caja_de_local(l)`; `con_atraco()` adiciona a opção ao cardápio de qualquer local com caixa registradora (é chamada de `menus_juego.lugar`). `Jugador.locales_vetados` armazena o que cada local lembra e `entrada_vetada(l)` aplica quando você tenta entrar. `asaltar_proveedor(l)` é o raid, com `Jugador.proveedores` (banimento, preços) e `Jugador.represalias`. `mandar_enemigos(clase, n)` envia inimigos de um determinado tipo atrás do jogador, em seu veículo, se ele tiver um. Seção `atracos`.
- `juego/golpes.py` (`Golpes`, lote 19): assaltos planejados. `Jugador.banda_gente` é a lista das pessoas da gangue, uma por uma (`banda_fichas()` corresponde a `Jugador.banda`, que ainda é a contagem; `banda_alta`, `banda_quitar_ficha`, `banda_echar`, `banda_ligar()` dá a cada aliado presente seu perfil e seu nome). `golpes.preparar(p, lugar, empezar)` é o menu; o plano (`{"papeles": {identificador da ficha: papel}, "yo": {"dentro", "huida"}, "veh_id", "modelo"}`) é passado para `atracar_local(l, plan)`, `empezar_atraco_banco(l, plan)` ou `asaltar_proveedor(l, plan)`, que chama `golpe_adaptar(m, l, plan)`: a missão repetível carrega o plano em `m["golpe"]`, portanto, uma nova tentativa o repete. `iniciar_mision` chama `golpe_al_iniciar` e `_limpiar_mision` chama `golpe_fin(False)`; após a conclusão, `golpe_fin(True)` faz a divisão alterando a recompensa. `Partida.golpe` (não salvo) contém o estado: fase, alarme, quando a polícia chega, veículo e o que foi sorteado para dar errado (`_golpe_sortear`). Seções `golpes` e `papeles_golpe`. Somente off-line (`golpe_bloqueo()`).
- Motor de missão, dois novos campos de etapas: `tarda` em `recoger` (segundos necessários para abrir: `mision_abrir`, `_paso_abrir`, estado em `ms["abriendo"]`) e `retraso` em `policia` (segundos até o nível de procurado cair: `ms["policia_en"]`; até que chega, a etapa não é considerada concluída). Um aliado com `puesto` (um ponto) permanece lá em vez de seguir o jogador (`extras.actualizar_aliado`).
- `juego/vuelo.py` (`Vuelo`, lote 19) e `juego/vuelo_pantalla.py`: voo real. `vuelo_real()` informa se está ativo (opção `vuelo_real`; nos testes automatizados apenas com `app.vuelo_en_pruebas`, assim como viagens com `viajes_en_pruebas`). Cada aeronave transporta `alt`, `fase` (`tierra`, `despegue`, `vuelo`, `aterrizando`, `sin_motor`) e `queroseno` (0 a 100, salvo com o veículo em `averias_a_dict`); `conduccion.conducir` chama `vuelo_controles(v, dt, teclas)` antes de mover, `_entrar_salir` chama `vuelo_aterrizar(v)` e `_conducir_libre`, na borda, chama `vuelo_borde(v)`. O voo cross-country é a tela `vuelo_pantalla.Crucero` (posição em quilômetros no mapa regional, rumo, altitude, vento como vetor, eventos aleatórios sorteados em `_plan_sucesos`, aproximação em `_aproximacion`); quando termina chama `vuelo_llegar(v, datos)`, que faz o `cambiar_mapa`. `vuelo.AERONAVES` e `vuelo.MAPA_AIRE` vêm das seções `aeronaves` e `mapa_aire`; `colocar(mapas)` coloca as cidades que não estão listadas (aquelas dos mods) de acordo com suas docas e estradas, e `punto_aire(mapa)` também tem um último recurso fixo. Hangares: `Jugador.hangares` (`{campo: {"propia", "naves", "pagado", "debe"}}`), `hangar_guardar`, `hangar_sacar`, `mandar_al_hangar`, aluguel em `_hangares_dia`. Sequestro: `Partida.secuestro` (não salvo), `secuestrar(l, encargo)`, `radar_te_tiene()` (verificado por `combate.actualizar_policia`), `secuestro_encargo(l)` com a semente do dia. Piloto comercial: `Partida.vuelo_trabajo` (não salvo), `piloto_ofertas(l)`, `piloto_aceptar`, `_piloto_cobrar`; a qualificação é `piloto`, em `titulos`. Em um servidor: voos, voos cross-country e hangares funcionam sem tocar no servidor (o voo é uma tela local e a mudança de cidade é o `cambiar_mapa` usual); sequestros e voos comerciais não (`secuestro_motivo`, `piloto_motivo`). Não há novos modelos de veículos e nada exportado para o servidor muda: a impressão digital mundial é a mesma.
- `juego/pactos.py` (`Pactos`): `oferta_devolver`, `oferta_comprar`, `pedir_tributo`, `regatear`, `dia_pactos` (toda meia-noite). `fuerza_propia()` e `rep_banda()` decidem; a aleatoriedade de cada acordo vem da semente do jogo, do dia, da turma e do assunto, então a resposta é a mesma o dia todo. `Jugador.tributos` e `Jugador.tratos`. Seção `pactos`.
- `juego/contratos.py` (`Contratos`): `ofertas_contrato(l)` dá os três trabalhos do dia; `empezar_contrato_de(l, oferta)` constrói a missão com as etapas que já existiam (`eliminar`, `perseguir`, `seguir`, `escoltar`, `recoger`, `ir`). Seção `contratos` (lista; `situacion` é um dos `contratos.SITUACIONES`). `Extras2.empezar_contrato` ainda é o contrato clássico. Um grupo de inimigos com `intimidar` se rende em vez de cair (`Agente.se_rinde_con`, chamado de `danar_persona`).
- `juego/reacciones.py` (`Reacciones`): `reaccion_tras(q, intencion, antes)` e `insistir(q)` são o que as pessoas fazem por conta própria (opção `gente_actua`); `pedir_favor(q)` e `reclutar_persona(q)` são as novas opções de conversação. Quem vai com o jogador carrega `estado == "sigue"` e é movido por `paso_seguidor` de `actualizar_personas`. `decidir_accion_ia(q, accion)` aplica as regras do jogo ao que o modelo propõe: `ia.py` só aceita ações de `ACCIONES` ou, com a opção `ia_acciones`, de `ACCIONES_AMPLIADAS`; qualquer outra coisa é “nada” e não há dinheiro ou itens na lista. Seção `reacciones`.
- `juego/convivencia.py` (`Convivencia`): `pedir_convivir(pers, casa)`, `saludo_de_casa`, `comer_en_casa`, `hacer_plan`, `peticion_cumplida(que)`, `dia_convivencia` (toda meia-noite), `aventura_en_casa`. Estado em `Jugador.convive`, `convive_casa`, `convive_hoy` e `peticion_pareja`. Opção `pareja_convive`; os planos não dependem disso. Seções `planes_pareja` (lista) e `convivencia`. As pessoas aceitam `convivir` (`facil`, `si`, `nunca`).
- `juego/agente.py` (`Agente`): o turno é um trabalho (`Partida.trabajo` com `tipo == "policia"`), então tudo que já conferiu `trabajo` o respeita. `empezar_turno`, `_aviso_nuevo`, `actualizar_agente`, `dar_alto`, `agente_intro`. `delito_de_servicio(puntos, texto)`, chamado de `Combate.delito` após verificar se há testemunhas, decide se se trata de força justificada, advertência ou demissão. Estado da posição em `Jugador.policia`; chamadas resolvidas em `stats["serv_policia"]`. Opção `oficio_policia`. Seções `policia_oficio` e `avisos_policia` (lista; `tipo` é uma de `agente.TIPOS`); taxa `academia_policia`.
- Tutoriais: o tipo de passo `practica` (`que`: `zarpar`, `timon`, `atracar`, `trabajar` ou `servicio`; `metros` e `giro` para o leme) é tratado por `Misiones._paso_practica`. Uma etapa `ir` com `"exige": "radar"` não será concluída na chegada se o radar não tiver sido usado nessa etapa (`ms["radar_usado"]`). Uma missão com `"explicacion": true` não é executada: `Misiones.explicacion(m)` lê seus passos de diálogo um após o outro. As vozes gravadas ainda são procuradas por missão, passo e linha, então ao tocar em um tutorial você deve ter certeza de que cada gravação ainda cai em sua linha (há um teste que observa isso).
- Num servidor online não existem a rusga a fornecedores, a negociação com gangues, o recrutamento na rua, a convivência e a carreira policial; todo o resto funciona da mesma forma. `servidor/` não foi tocado e a impressão digital mundial não muda.
- Novos sons: `timbre` e `emisora` (`VERSION_CACHE` 19). Nos pacotes estão gravações CC0 de bigsoundbank.com (veja "Sons de terceiros").

### Reconquistando bairros

`juego/reconquista.py` (o mixin `Reconquista` de `Partida`). Somente offline: `rec_nivel()` retorna vazio com a opção `reconquista` definida como `apagado`, em um servidor (`en_servidor`) ou com um jogo com amigos em andamento (`online_activo()`), e então nada avança.

- Estado: tudo em `Jugador.reconquista` (um dicionário simples, salvo com o jogo): `fase`, `calma`, `descanso`, `informantes`, `bandas` (força, moral, derrotas, `fuera`, `tregua`, `golpe`, `umbral`, `forastera`), `barrios` (lealdade, guarda, reforço, `pisado`, `de`), `asalto` e `partes`. Um jogo salvo mais antigo é carregado com `{}`; `rec()` preenche no primeiro uso e `cargar_dict` define `_rec_cargada` se já tiver vizinhanças suficientes (calma inicial e aviso, uma vez).
- Fase (`rec_fase`): `suave` com `suave_barrios` ou mais, `plena` com uma cidade inteira, `mundo` com todas elas. `reconquista_revisar()` é chamado a cada dois segundos e a cada meia-noite.
- Toda meia-noite (`dia_reconquista`, de `_cobrar_negocios`): pagamentos a guardas e informantes, lealdade, tréguas, crescimento (`_rec_crecer`), gangue de forasteiros e aviso de ataque pendente ou plano para um novo (`_rec_planear`, `rec_elegir_objetivo`). Com a reconquista ativa (`rec_activa()`), `sistemas.sucesos_territorio` não lança seus ataques pontuais: nunca são dois ao mesmo tempo.
- O assalto (`asalto`): `prepara` até o seu dia e hora; `en_curso` com `quedan` em minutos de jogo, que ocorre em `actualizar_reconquista` exceto durante uma missão ou luta. `rec_pasar_horas` (de `pasar_horas`) aplica o período de carência uma vez. A defesa presencial utiliza `guerra.empezar_guerra(..., rec=...)`, que independe da opção `guerra_calle`; `_guerra_ganada` chama `rec_defendido("persona")`. `rec_enviar_gente` e `_rec_vence` resolvem isso com `_rec_calculo`.
- A trégua está em `juego/pactos.py` (`oferta_tregua`, `pactar_tregua`, `menu_tregua`), com seus números na seção `pactos`. O ataque preventivo (`empezar_golpe`) é uma missão gerada repetível, com quatro variantes.
- Menus: `menu_reconquista` e `opciones_territorios` (o que é adicionado aos Territórios). Números e linhas: `data/datos/vida.json`, seção `reconquista` (`reconquista.AJ`); esquema do editor, `ajuste_reconquista`.
- Sons: `amenaza_barrio`, `barrio_perdido`, `barrio_defendido`.
- Testes: `pruebas/test_171_reconquista.py`, que inclui simulações de sessenta dias em cada intensidade.

### Vida, reputação e consequências (1.7.1)

`juego/honrado.py` (o mixin `Honrado` de `Partida`) e `juego/menus_honrado.py`. Conta com os dois medidores já existentes, `Jugador.ciudadania` (prestígio) e `Jugador.reputacion` (fama), que são independentes; não há terceiro.

- Nível: `hon_nivel()` retorna 0 a 3 conforme a opção `consecuencias` (`apagado`, `suave`, `normal`, `exigente`; `suave` por padrão) e sempre 0 em um servidor (`en_servidor`). `hon_f()` é o fator de penalidade (`factor_suave`, `factor_exigente`). As vantagens não são escalonadas. As outras opções: `impuestos_facturas`, `antecedentes`, `pareja_familiar`.
- Estado, tudo no player e salvo com o jogo: `antecedentes` (lista), `contrato`, `titulos`, `empresa` (por empresa), `creditos` (lista) e `honra` (cobranças, dívidas, crédito, apreensão, o boato `sospecha`, dinheiro inexplicável `negro`, pendente `asuntos`, advogado, cartas, proibições). `hon()` o cria pela primeira vez com o período de carência; um jogo salvo mais antigo carrega `_hon_cargada` e recebe um aviso único.
- Ganchos: `azar.mercado` (tratamento em lojas, `hon_trato`), `partida.pagar` (crédito, `hon_fiar`, com `_local` definido em `entrar_interior`), `combate.delito` (`hon_delito`: encobrimento, benefício da dúvida, reportagem, em arquivo, boato), `combate.detener` e `_trato_policia` (`hon_antecedente`), `vida.jornada` e `vida.servicio_hecho` (`hon_turno`), `partida._cobrar_negocios` (`ingreso_negocio`, `dia_honrado`), `extras3.repartir_ingresos_negocios` (tomadas e apreensões de período), `misiones` (`cumple_vida`, `hon_mision_completada`, `prestigio` nas decisões), `partida.interactuar` (`hon_ofrecer_mision`: a missão do caminho direto vai como última opção do cardápio do local), `agente.ingreso_motivo` e `hon_negro` em roubos, homenagens e repetíveis empregos.
- Toda meia-noite (`dia_honrado`): antecedentes criminais vencidos, avaliação de contratos, negócios (nome, frente, fiscalização), cobrança de contas e impostos, taxas, boatos e imprensa, extorsão e assuntos sem resposta. A cada vinte segundos (`actualizar_honrado`): o aviso de um jogo antigo salvo, aquele dos dois caminhos, dos checkpoints e das situações de rua.
- Pendências (`honra["asuntos"]`: fiscalização, imprensa, extorsão) são resolvidas com `hon_resolver(asunto, clave)`; passado o prazo eles se resolvem.
- O enredo: `data/datos/misiones_honrada.json` (capítulo 16), missões com `honrada`, `requiere_vida`, `epilogos`. Suas cenas possuem vozes gravadas como as demais (em `data/voces/historia_principal`). O final é armazenado em `decisiones["_final_honrado"]`, separado da história principal.
- Um relacionamento adequado para todos: `vida_sentimental()` substitui `modo_adulto()` nos relacionamentos (`adultos.dia_adultos`, `convivencia`, `sistemas.personas_aqui`, `menus_adultos.vida_social`); o noivado e o casamento vão no relacionamento (`compromiso`).
- Números e linhas: `data/datos/vida.json`, seções `vida_honrada` (`honrado.AJ`), `titulos`, `empleos_fijos`, `mejoras_negocio`, `incidencias_trabajo` e `buenas_acciones`; esquema do editor em `editor/esquema_honrado.py`.
- Sons: `despido`, `inspeccion`, `factura` e `titulo` (`VERSION_CACHE` 24).
- Testes: `pruebas/test_171_honrado.py`, com toda a campanha sem crimes e três simulações de sessenta dias (honesto, criminal e vida dupla).
- Servidor: nada disso chega ao servidor ainda; os novos campos do jogador e as novas receitas e despesas estão descritas nas notas de lançamento para quando for transferido.

### Compras, despensa e culinária

- `juego/compra.py` (o mixin `Compra` e a tela `Tienda`) e `juego/menus_cocina.py` (os menus e a tela `Cocinando`). Cinco seções de `vida.json`: `pasillos`, `productos`, `tipos_tienda` e `recetas` (listas) e `cocina` (o `Ajustes`). O conteúdo padrão também está no módulo (`PASILLOS`, `PRODUCTOS`, `TIPOS_TIENDA`, `RECETAS`), caso esteja faltando em dados mais antigos; existe um teste que verifica se eles correspondem.
- A loja: `tipo_tienda(l)` decide a classe da loja (o campo `surtido` do local, a lista `lugares` do tipo, o `palabras` do nome ou o tipo com `resto`) e `surtido(l)` fornece seus corredores com seus produtos. `precio_producto(l, prod)` aplica o swing do dia (`mercado`), o tipo `recargo` e a oferta especial. `oferta_de(l)` e `agotado(l, prod)` vêm da semente do jogo, do dia e da loja: são iguais o dia todo. `sistemas.con_recorrido` abre `compra.Tienda` (filho de `sistemas.Local`) em lojas com uma variedade de produtos; a cesta fica nessa tela e não é salva. `comprar_productos(l, cosas)` cobra e `robar_productos(l, cosas)` é furto em lojas (`delito` e `Jugador.locales_vetados` como em roubos).
- O que você compra vai para `Jugador.encima` e, quando você guarda (`guardar_compra(casa)`), para `Jugador.despensa[casa.id]`. Ambas são listas de lotes: `{"id": producto, "n": cantidad, "cad": dia de validade, ou 0}`; um prato cozido é `{"plato": receta, "nombre", "n", "cad", "hambre", "sed", "salud", "animo"}`, com seus efeitos já calculados, então ainda funciona mesmo que o mod da receita seja removido. Geladeira ou despensa é decidida pelo `sitio` do produto (`lote_info`); a capacidade, por `sitio_capacidad(casa, sitio)`. `tirar_caducado(lotes)` é chamado na abertura; um lote é válido até o dia `cad` inclusive.
- Cozinhar: `receta_falta(casa, r)` e `cocinar(casa, r, rng)`, que gasta ingredientes, passa o tempo, desenha a qualidade (`Jugador.cocina_practica`, de 0 a 100, e o móvel `cocina`), serve uma porção e armazena o restante. `sistemas.Interior` chama `menus_cocina.usar_cocina`, que, sem nada armazenado e sem comida consigo, faz o que fazia antes (`Interior._picar_algo`).
- Três novos campos de jogador (`despensa`, `encima`, `cocina_practica`), todos com valor padrão: o formato do jogo salvo não sobe. Não há novas opções. Depende apenas do jogador, então em um servidor funciona da mesma forma (o relógio não avança durante o cozimento) e `servidor/` não foi tocado; a impressão digital mundial não muda.
- Novos sons: `cesta`, `nevera`, `cocina_cortar`, `cocina_freir`, `cocina_hervir` e `plato_servido` (`VERSION_CACHE` 20). Nos pacotes estão gravações CC0 de bigsoundbank.com (veja "Sons de terceiros").

### O controle: todas as ações acessíveis (1.7.1)

- `juego/mando.py` traduz o controlador em chaves. O que não cabe em um botão ou combinação entra em `MENU_ACCIONES` (frase, tecla, modificador, onde se aplica, condição, explicação, se o menu permanece aberto): é o menu aberto pela ação `menu_acciones`, por padrão no botão combinar mais o gatilho direito, a pé e ao volante. `acciones_de(p)` fornece aqueles que se aplicam naquele momento.
- Regra: uma nova chave em `ayuda.TECLAS` precisa de um botão ou combinação em `POR_DEFECTO`, uma entrada em `MENU_ACCIONES` ou uma linha em `SIN_BOTON` com seu motivo (`SOLO_A_PIE` para os gerais que não fazem sentido ao volante). Nas telas que não são menus (`PANTALLA`), uma chave própria precisa de um alias de uma das teclas que o controlador envia para lá: o C da cesta é Tab (`ALIAS_PANTALLA`). Isso é assistido por `pruebas/test_171_mando.py`.
- Os eventos do controlador carregam `mando = True` (`_Ev`): não passam pelo remapeamento de teclas do teclado (`App.evento_tecla`), e em `menus.EntradaTexto` movimentam a roda de letras. `EntradaTexto(..., propuestas=lista ou função)` oferece textos já escritos com Tab (X ou Quadrado): as listas `frases_chat`, `rol_frases_ic`, `rol_frases_yo` e `rol_frases_ooc` em `gente.json`, e `nombres_propuestos` em `vehiculos_propios` em `vida.json`.
- Frases faladas: `textos_mando` troca teclas por botões também quando a função está em combinação. Para telas que falam com `app.decir`, `Mando.boton_pantalla(tecla, nombre)` fornece o nome da tecla ou do botão.

### Testes

`probar.bat` executa todo o conjunto. Os testes conduzem o jogo como uma pessoa, com teclas e frames: eles jogam todas as missões, percorrem os mapas com o GPS, acessam todos os menus e locais, jogam vinte dias com o tempo acelerado, conectam dois jogos entre si, operam um controle simulado e verificam a acessibilidade do editor. Eles também falham se um som for adicionado sem descrição ou uma chave sem documentação. Eles não usam rede nem placa de som.

### Compilação

`compilar.bat` usa cx_Freeze e deixa em `dist\PuertoBravo` uma pasta portátil com `PuertoBravo.exe` e `EditorMods.exe`. De antemão, ele regenera os mods integrados, quaisquer sons ausentes e os guias. Quando terminar:

- Protege os dados: cada arquivo JSON é compactado, criptografado e assinado, e altera a extensão (dados `.pbd`, mods `.pbm`, jogos salvos `.pbs`, opções `.pbc`). O código lê os dois formulários, então no código-fonte tudo permanece como JSON legível.
- Verifica por si mesmo se a pasta está completa, protegida e limpa: sem jogos salvos, opções, logs, músicas pessoais ou documentação de desenvolvimento.

A proteção utiliza uma chave que fica dentro do próprio programa. Impede a edição casual; não é uma barreira contra quem analisa o executável.

### Publicando uma versão

O jogo é atualizado lendo um arquivo `version.json` assinado com Ed25519. A fonte (o servidor, GitHub, ambos ou um endereço personalizado) apenas decide de onde será baixado: o que estiver instalado deve ser assinado com a chave privada do editor, cuja chave pública está em `juego/actualizador.py`.

1. Insira `VERSION` em `juego/__init__.py` e adicione as notas de versão na parte superior de `data/docs/novedades_es.html` e de `data/docs/novedades_en.html` (as novidades ficam só em espanhol e em inglês).
2. Execute `compilar.bat`.
3. Execute `publicar.bat`. Ele cria em `dist\publicar` o arquivo `PuertoBravo_v<versión>.zip` e seu `version.json` assinado, e os copia para a pasta escrita em `publicar_destino.txt`, que é a pasta web do servidor.
4. Para GitHub, crie a versão `v<versión>` e carregue esses mesmos dois arquivos.

A chave é criada apenas uma vez com `.venv\Scripts\python.exe herramientas\publicar.py clave` e é mantida em `herramientas\claves`. Essa pasta e `publicar_destino.txt` estão em `.gitignore`: a chave privada nunca deve estar no repositório ou no servidor. Mantenha uma cópia fora do computador. Se você bifurca o projeto e deseja publicar suas próprias versões, crie sua chave e altere, em `juego/actualizador.py`, a chave pública, o endereço do servidor e o repositório.

A verificação de assinatura é implementada com a biblioteca padrão, seguindo RFC 8032, e é verificada nos testes com seus vetores oficiais. Se o pacote `cryptography` estiver instalado, esse será usado.

### Processadores antigos: os dois numpys

O numpy oficial (2.4 em diante) requer um processador com as instruções x86-64-v2 (SSE4.2, SSSE3, POPCNT e o resto). Em um mais antigo, carregá-lo faz com que Windows feche o programa com o código 0xC000001D. Para Python 3.15 não há rodas numpy anteriores a esse requisito, então o jogo construído vem com dois:

- `lib\numpy`: o oficial do PyPI, para processadores atuais.
- `lib_antiguo\numpy`: a mesma versão, construída sem requisitos com `-Dcpu-baseline=none` e sem BLAS. Ele ainda usa as instruções modernas quando o processador as possui, porque as seleciona na inicialização.

`juego/procesador.py` pergunta a Windows quais instruções estão disponíveis (`IsProcessorFeaturePresent`) antes de importar numpy e coloca a pasta correta primeiro. Caso o escolhido não carregue, tenta o outro; se nenhum dos dois carregar, o jogo avisa em voz alta e fecha normalmente. A variável de ambiente `PUERTOBRAVO_NUMPY=antigua` (ou `oficial`) força um, para teste.

A roda para processadores antigos está em `terceros/numpy_antiguo`, pronta para uso: `compilar.bat` a coloca na construção com `herramientas/poner_numpy_antiguo.py`. Ele só precisa ser reconstruído se a versão numpy ou Python mudar, com `herramientas\compilar_numpy_antiguo.bat`, que precisa do Visual Studio com as ferramentas C++. numpy está sob a licença BSD de três cláusulas.

### Os dois motores de som

`juego/audio.py` é o mixer clássico: mistura em Python com numpy, com panorâmica estéreo, atraso interaural e atenuação de distância. `juego/audio_al.py` herda toda a lógica dele e altera apenas a saída: mantém uma fonte OpenAL Soft para cada som e deixa a biblioteca fazer a mixagem em binaural (HRTF). É chamado através de `ctypes`, sem pacotes Python, portanto não depende da versão do Python. `audio_al.crear()` decide qual será utilizado: o surround somente se o reprodutor tiver escolhido, a biblioteca estiver presente e o processador for moderno; em qualquer outro caso, ou se falhar na inicialização, o clássico.

A biblioteca, `soft_oal.dll` (OpenAL Soft 1.25.2, LGPL), está em `terceros/openal_soft` com sua licença e `compilar.bat` a copia para `lib`. `herramientas/probar_motor_envolvente.py` faz um teste real com o dispositivo de som.

### O instalador da atualização deixa um rastro

`juego/actualizador.py` escreve um `.bat` que substitui o programa assim que o jogo é fechado. Esse `.bat` registra cada etapa em `data/logs/actualizacion.log`: `PASO nombre`, `RESULTADO nombre codigo=N` (código do robocopy; 8 ou mais é uma falha), `FALLO paso=... codigo=... motivo=...` e `TERMINADA bien` ou `TERMINADA mal`. Robocopy grava nesse mesmo arquivo, com `/log+`, apenas os erros, com o arquivo e o erro Windows. `leer_registro_instalador()` interpreta e `motivo_del_fallo()` transforma em uma frase para o jogador; ao reabrir com `--actualizacion-fallida`, o jogo diz e guarda para Opções, Atualizações. `limpiar_registro_instalador()` reduz cada caminho ao nome do arquivo, para que o log possa ser enviado.

Antes de fechar, `problemas_para_instalar()` verifica se a pasta pode ser gravada, se nenhum outro programa do jogo está aberto (pela lista de processos e tentando abrir cada `.exe` para gravação; um servidor online com seu registro não conta: ele é parado e reiniciado sozinho, como explica a seção do servidor) e se há espaço: `espacio_para_instalar()` soma o backup, quanto cada arquivo cresce e uma margem. Antes de baixar, `problema_para_descargar()` faz a soma com o ZIP, a versão extraída e a cópia. Os testes (`pruebas/test_171_red_seguridad.py`) executam o `.bat` real em pastas fictícias, inclusive com um arquivo bloqueado; nenhum deles sai para a internet.

### O gerador de vozes e as proteções contra falhas

O mecanismo em `juego/vozgen.py` é código nativo: se o processador não tiver o que precisa (AVX2, FMA e F16C), ele pode fechar o processo sem gerar um erro Python. É por isso que `disponible()` primeiro verifica as três capacidades (`capacidades()`: AVX2 é solicitado a Windows; FMA e F16C, de numpy) e, pela primeira vez, testa o motor em um processo separado: o próprio jogo é lançado com `--probar-motor-voz`, que `main.py` manipula antes de abrir qualquer coisa e que termina com 0, 10 (não carrega) ou 11 (não gera). Construído com cx_Freeze é `PuertoBravo.exe --probar-motor-voz`; do código, `python main.py --probar-motor-voz`. O resultado é salvo em `data/voces_generadas/motor_probado.json` com a versão do jogo e uma impressão digital dos arquivos do motor, e o teste é repetido se algum deles mudar. O teste é executado em segundo plano: enquanto dura, `disponible()` responde não e `cuando_se_sepa()` avisa quando termina. Além disso, toda vez que o jogo carrega o motor dentro de seu processo, ele o grava e apaga o registro assim que gera a primeira linha: se fechar pela metade duas vezes seguidas, ele para de tentar. `parar_prueba()` encerra o processo de teste quando o jogo fecha e antes da atualização.

### Registro da sessão

`juego/registro.py` cria em `data/logs` uma pasta por sessão, com no máximo cinco. Dentro estão `sistema.txt` (versão, Windows, leitor de tela, som, mods, opções), `sesion.log` (telas, teclas, tudo o que o jogo diz, um instantâneo do estado do jogo a cada quinze segundos, rede, atualizações, frames lentos e avisos), `errores.log` (cada erro com seu traceback, o estado do jogo e as últimas teclas e sons) e `fallo_grave.log` se o processo travar repentinamente. Ele também captura exceções não tratadas do thread principal e de outros threads.

Tudo passa por um filtro antes de ser escrito: são substituídos os caminhos dos usuários, os nomes dos usuários e dos computadores, os endereços IP e de internet, os e-mails, as chaves e os nomes dos players da rede. Nem o que é digitado nas caixas de texto nem as mensagens de bate-papo são registrados. Existe um teste que reproduz uma sessão com dados falsos e falha se algum deles aparecer na pasta. Ao adicionar qualquer coisa que lide com dados do jogador, use `registro.privado()` ou `registro.ocultar()`.

### Acessibilidade

A acessibilidade é o principal requisito do projeto. Tudo o que acontece no jogo tem som próprio, e todo o texto passa pelo leitor de tela. Todas as chaves estão na ajuda (`F1`) e no manual, que são geradas a partir do mesmo código. O editor segue diretrizes de acessibilidade para wxPython: rótulos associados a cada controle, teclas de acesso sem repetições, controles nativos e ajuda de contexto com `Control+H`.

---

## 3. Criando mods

Um mod adiciona ou altera conteúdo sem mexer nos dados originais: locais, missões com todas as suas etapas, armas, veículos, corridas, comida, itens, peixes, personagens jogáveis, capítulos, mapas inteiros e, para o modo adulto, pessoas, planos, presentes e substâncias. Os mods estão em `data\mods` e são carregados na inicialização. Uma missão ou etapa pode depender de várias decisões ao mesmo tempo com `si_cruce` (`"concejal:1, trono:3"`), `si_cruce_min` e `si_cruce_max`, e uma missão pode exigir uma de cada filial com `requiere_alguna` (`"fd2 fd3 fd4; vd2 vd3"`). Cada mapa indica onde a linha de trem passa com `tren_eje` e `tren_n`, e um local do tipo `aeropuerto` com `"aerodromo": true` é uma pista de pouso curta de uma cidade. Em qualquer texto, o que muda dependendo se o protagonista é homem ou mulher é escrito entre colchetes, com a forma masculina, uma barra e a forma feminina: `Bienvenid[o|a]`, `[el sobrino|la sobrina]`. É resolvido por `juego/genero.py` pouco antes de o texto ser falado.

### Com o editor

A forma usual é `EditorMods.exe` (ou `editor.bat` do código-fonte). É um aplicativo acessível com leitor de tela: cada coisa é criada preenchendo um formulário, `Control+H` explica o campo em que você está e `F1` abre seu manual (`data\docs\editor_mods_pt.html`). Antes de salvar, ele verifica se existe tudo o que o mod se refere e avisa sobre qualquer coisa que esteja faltando.

O editor sempre salva de forma protegida, como `.pbm`, que é o que o jogo construído carrega, e abre os arquivos `.pbm` e `.json`.

### À mão

Um mod também é um arquivo JSON. O formato é explicado, com exemplos, em `desarrollo/formato_de_los_mods.html`, e `desarrollo/ejemplo_mod.json` é um mod mínimo. A partir do código-fonte, o jogo carrega os arquivos `.json` diretamente em `data\mods`. O jogo construído não: ele avisa na inicialização e pede que o arquivo seja aberto com o editor e salvo, para que fique verificado e protegido.

### Mods integrados

Oito acompanham o jogo, já habilitados, e também servem de modelo. Eles são gerados com `herramientas/crear_mods_ejemplo.py`, onde você pode ler como cada um é feito:

- Bahía del Ocaso: uma grande cidade costeira, com seis bairros, três gangues e uma história de vinte e uma missões (`herramientas/mod_bahia_ocaso.py`).
- Costa Dorada: uma vila de pescadores com história própria e exemplo de tudo que um mod pode conter.
- Valdeolmos: uma cidade vitivinícola, com uma fraude de vinho e uma corrida de tratores.
- Peñas Altas: uma cidade mineira de montanha, com uma mina que alguém explora à noite.
- Isla de los Vientos: uma ilha que você chega por mar, com naufrágios e salinas.
- Noches de neón: Puerto Bravo à noite, sem novo mapa, com táxis noturnos e vida social.
- Oficios y recados: vida mais honesta em Puerto Bravo.
- Motor y asfalto: carros, motos, corridas e missões ao volante.

Para compartilhar um mod, passe seu arquivo `.pbm`. Quem recebe copia em seu `data\mods`.

As missões podem ter vozes gravadas (`juego/voces.py`): arquivos de som em `data\voces`, um por linha. As linhas que dependem do protagonista possuem diversas formas, com uma arroba após o nome: `m01_1_1@alex`, `m01_1_1@m`, `m01_1_2@alex_m`. O editor escreve o script com o nome de cada arquivo e seus formulários. Não são aceitos mods com material de outros jogos ou vozes clonadas de pessoas reais.

As vozes que acompanham o jogo são geradas com Phonon 40m, um modelo de voz da [Gradium](https://gradium.ai/phonon) sob uma licença Creative Commons Attribution-NonCommercial (CC BY-NC 4.0). O mesmo modelo acompanha o jogo, em `data\phonon`, para gerar no computador do jogador as falas que nomeiam um personagem que ele criou (`juego/vozgen.py`), com o pacote `ptts`, que é um software livre. O texto da licença está em `data\phonon\LICENCIA.txt`. O arquivo do modelo, `model.q8.gguf`, pesa 95 megabytes e não está neste repositório: `herramientas\preparar_phonon.py` o copia de uma pasta com o modelo baixado do Hugging Face (`gradium/phonon-40m-multilingual`), e `compilar.bat` o chama. Sem o modelo o jogo funciona da mesma forma; essas linhas são faladas pelo leitor de tela.

---

## 4. Pacotes de som e música

O guia completo, com a descrição e duração de cada um dos 279 sons, é `data\docs\cambiar_sonidos_pt.html` (em espanhol, `cambiar_sonidos_es.html`). Resumindo:

### Sons

- Todos os efeitos estão em `data\sonidos`, em subpastas. `por_defecto` contém os padrões, um arquivo por som; se você excluir um, o jogo o criará novamente. Cada uma das outras subpastas é um pacote.
- O pack é escolhido dentro do jogo, em Opções, Som e música, e você ouve na hora.
- Estão incluídos quatro packs completos: Realista e Alternativo, com gravações reais em domínio público; Retro, com som de console antigo; e Envolvente, para o motor de som surround. Todos os quatro mantêm o original para os sons de orientação (balizas, tons, semáforos, radar e sons de lugares), pois deles depende a locomoção no jogo.
- Para fazer o seu próprio, crie uma pasta em `data\sonidos` e copie suas gravações nela com o nome exato do som que elas substituem: `claxon.wav`, `paso_acera0.ogg`. Os sons do jogo são em FLAC, sem perdas; o seu pode ser WAV, OGG, FLAC ou MP3. Você não precisa trazer todos: o que falta reproduz o original. WAV, OGG, FLAC e MP3 são suportados.
- Um arquivo `pack.json` opcional fornece ao pacote seu nome, autor, licença e ajustes de volume por som.
- O volume é nivelado automaticamente: cada som alterado é levado ao nível do original, e o jogador pode aumentar ou diminuir qualquer um deles separadamente nas Opções.

### Música

- Rádio: cada emissora possui seu arquivo em `data\radio`. Uma estação pode ter diversas músicas (`bravo.mp3`, `bravo_1.mp3`, `bravo_2.mp3`...), que giram. Qualquer outro arquivo de áudio que você deixar lá será uma nova estação, e `data\radio\mi_musica` será a estação com sua própria música. Músicas com mais de cinco minutos são lidas e reproduzidas em blocos de um minuto (`juego/musica.py`), portanto, uma gravação com várias horas de duração não ocupa mais memória do que uma música curta.
- Ambiente: `data\musica` possui uma pasta por situação (`menu`, `exploracion`, `noche`, `mar` e `tension`). Todas as peças de cada uma são utilizadas, aleatoriamente, como quer que sejam chamadas.
- Toda a música é nivelada automaticamente quando é carregada, então nenhuma faixa soa mais alta que a outra.

### Sons de terceiros

Os pacotes Realista e Alternativo são reunidos com gravações de domínio público (licença CC0) de kenney.nl, opengameart.org, freesound.org e bigsoundbank.com. Cada pack possui um arquivo `CREDITOS.txt` com a origem de cada som.

Regras do pacote, com seus testes de watchdog em `pruebas/test_171_sonidos.py`:

- As cinco pastas em `data/sonidos` (`por_defecto`, `realista`, `alternativo`, `retro` e `envolvente`) possuem exatamente os mesmos sons, com os mesmos nomes e nenhum em dois formatos. Um novo som é adicionado ao `sintesis.generar()` (no final, batendo `VERSION_CACHE`), ao `catalogo_sonidos` (grupo e descrição) e aos packs com `herramientas/crear_packs.py anadir <nombres>`.
- `crear_packs.py anadir` também serve para alterar um som já instalado: coloca a gravação dada pela tabela do pack (`PACKS`, `EXTRA`, `CALLE`, `V171`, `PROPIAS`) ou, se não houver, o som padrão; o pacote Retro herda do Realista tudo o que não tem som de console, e o Envolvente copia do Realista tudo o que não é orientação ou ambiente próprio. Em seguida, ele reescreve `CREDITOS.txt` (uma linha por gravação, a lista daqueles que são o som padrão e a contagem no cabeçalho) e as contagens em `pack.json`, para que sempre correspondam aos arquivos.
- As gravações individuais trazem título, autor e página em `DETALLE`, e é assim que aparecem em `CREDITOS.txt`. Aqueles de 1.7.1 são de bigsoundbank.com, todos CC0 e de Joseph SARDIN, exceto onde indicado: megafone ("Megafone, larsen" 9 e 4), aparelho de rádio ("Walkie talkie: Iniciar" e "Tons do teclado"), campainha ("Campainha casa # 1"; "Campainha # 6", de Dorian CLAIR), geladeira ("Porta da geladeira"), cozinha ("Tábua de corte, abobrinha" 2 e 1, "Fritar panela" 3 e 2, "Água fervente", "Caldo pequeno em uma panela"), prato ("Prato grande, colocado na mesa", "Prato pequeno, colocado na mesa"), cesta ("Pacote de batatas fritas, manipulação #2"; "Lata #1", de DenisChardonnet) e vizinhanças ("Bass Tom, #1", repetido três vezes; "Church Bell"; "Drum roll 3 S" e "Drum Roll 1 L"). Os originais baixados são mantidos fora do repositório, em `adjuntos/fuentes/bigsoundbank_171`, com seu `LEEME.txt`.
- Opções de corte em `crear_packs.py`: além de `dur`, `golpe`, `bucle` e `desde`, aceita `entrada` e `fundido` (segundos de fade no início e no final, para ruídos contínuos que são cortados) e `veces` (o mesmo take repetido naqueles momentos).
- `chat_personaje`, `chat_fuera`, `chat_accion` e `espera_servidor` são o som padrão em cada pack: são um código de tons, não o ruído de uma coisa.
- Os sons de orientação nos pacotes são aqueles em `por_defecto`, byte por byte onde importa: o teste compara as amostras.
- Existe uma classificação única de sons, em `juego/catalogo_sonidos.py`: `GRUPOS` (título, dica para o guia e chave, na ordem em que são ensinados) e `SONIDOS` (para cada grupo, arquivo, nome falado e explicação do que significa ouvir). A partir daí vêm, com os mesmos grupos, nomes e ordem, Aprender os sons (`menus_juego.sonidos`), Opções, Ajustar o volume de cada som (`menus_juego.volumen_sonidos`), o guia de sons e a lista para packs (`generar_datos.py`); todos passam pelo `catalogo_sonidos.clasificar`, que ordena cada grupo em ordem alfabética pelo nome falado (`orden`: sem acentos e com ñ após n). São 20 grupos, pelo que é feito no jogo: orientação e GPS; sons de lugares; andar a pé e nadar; veículos e condução; avarias, oficinas, gás e roubo de veículos; barcos, helicópteros, trem, bonde e avião; armas, o tiro de cada uma; combate, pontaria e ferimentos; polícia e serviços de emergência; pessoas na rua e animais; casa, cozinha e comida; lojas, dinheiro e itens; menus, alertas de telefone e jogos; missões, trabalho, reputação e humor; territórios e gangues; jogo e roleplay online; pesca, cassino e jogos; ambiente e clima; relacionamentos, apenas com conteúdo adulto; substâncias e tráfico, apenas com conteúdo adulto. Nenhum pode cair em “Outros sons”, que só existe para um arquivo adicionado manualmente.
- `IMPORTANTES` é a ordem do grupo “O mais importante”, e dela deriva o glossário `ayuda.SONIDOS`. `es_orientacion` diz quais sons os packs guardam (não depende dos grupos). `buscar` é a busca utilizada por ambos os menus (`menus_juego.buscar_sonido`): todas as palavras, no nome, explicação, grupo ou nome do arquivo, ignorando acentos e maiúsculas.
- O volume por som é salvo em `vol_sonidos` pelo nome do arquivo, portanto a reclassificação não perde nada. `packs.factor`, `packs.cambiado` e `packs.restablecer` dão o ajuste que realmente foi aplicado, dizem se foi alterado e retornam ao valor padrão; o menu (`MenuVolumenes`) adiciona Excluir, a lista "Sons alterados" e redefinição de um grupo.

---

## Licença

Licença MIT: você pode usar, modificar e distribuir qualquer parte do jogo, com a única condição de manter o aviso de direitos autorais e a licença. Está no arquivo `LICENSE`.