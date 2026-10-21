# GlyphWorld 0.2 — The Forgotten City

Protótipo gráfico de um mundo industrial formado por um campo dinâmico de caracteres.
Python 3.11+, ModernGL, GLFW, NumPy e Pillow. Não há IA nesta versão.

![Captura real dos shaders em GPU Intel UHD](docs/preview.png)

**Estado:** implementação entregue; testes de lógica e renderização dos shaders na GPU
executados. A aplicação completa ModernGL/GLFW ainda precisa de validação integrada:
o ambiente de desenvolvimento bloqueou a instalação dessas dependências. A captura
acima foi produzida pelos shaders reais em um harness OpenGL, não por imagem gerada.
Veja [o relatório de validação](docs/VALIDATION.md) antes de interpretar desempenho.

## Executar no Windows

1. Instale Python **3.11 ou superior** (64 bits), com o launcher `py` ou Python no PATH.
2. Baixe este repositório em **Code → Download ZIP** e extraia, ou use Git.
3. Dê dois cliques em **`start_windows.bat`**. Na primeira vez é necessária internet
   para criar o ambiente virtual e instalar as dependências.
4. A janela inicia em 1280 × 720; o personagem caminha automaticamente.

Instalação manual no PowerShell, dentro da pasta do projeto:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m glyphworld
```

Não é necessário ativar o ambiente virtual. Uma fonte monoespaçada do sistema é
usada para gerar o atlas; nenhuma fonte ou recurso de Rain World é distribuído.
Se a fonte não for localizada, configure `render.font` em `config.toml` com uma fonte
TTF monoespaçada. Caminhos relativos são resolvidos a partir da pasta de execução.

Linux (arquitetura preparada, ainda não validado):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m glyphworld
```

É necessária uma sessão gráfica, driver com OpenGL 3.3+ e as bibliotecas de sistema
usadas pelo GLFW. O renderer principal não utiliza APIs exclusivas do Windows.

## Controles

| Tecla | Ação |
|---|---|
| Espaço | Pausar/continuar personagem, câmera e atmosfera |
| `[` / `]` | Mais/menos caracteres; recria buffers e limpa histórico |
| R | Ligar/desligar chuva |
| L | Alternar iluminação ambiental/local e sombra aproximada |
| F1 | Mostrar/ocultar diagnóstico no título da janela |
| F2 | Final → luminosidade → orientação → profundidade → material |
| `+` / `-`, ou roda do mouse | Zoom entre 0,65× e 1,8× |
| F12 | Salvar PNG da imagem atual em `captures/` |
| Esc | Sair |

Todos os mapas de diagnóstico também são mostrados por glifos. O diagnóstico fica
no título da janela para não sobrepor pixels convencionais à cena.

## O que existe na demonstração

- Quatro camadas de arquitetura procedural com parallax, janelas, tanques e antenas.
- Fachada próxima com tijolos, rachaduras, canos, trepadeiras e luz quente.
- Passarela com corrimão, suportes diagonais e cabo pendente.
- Solo úmido, reflexos estilizados, vegetação ao vento, neblina e três camadas de chuva.
- Pequeno viajante original com capuz, casaco, pernas animadas e cachecol.
- Câmera com suavização exponencial e configuração por seed.

O movimento é demonstrativo: não há colisão, navegação, física de água, persistência
nem comportamento autônomo. A composição é 2D em camadas, com profundidade simulada.

## Como o campo de glifos funciona

1. `scene.frag` calcula cor e metadados (material, profundidade e textura) em dois
   buffers intermediários, com duas amostras por eixo de cada célula.
2. `field.frag` calcula luminosidade e gradiente local. Densidade, orientação,
   contraste, material, distância e textura determinam o símbolo. Vegetação,
   metal e água têm preferências distintas. O histórico ping-pong aplica histerese
   com referência de luminosidade acumulada para reduzir cintilação.
3. `glyph.frag` amostra apenas o símbolo selecionado no atlas compartilhado,
   colorindo sua máscara. Fora da máscara, o resultado é preto. Não há composição
   da imagem intermediária atrás dos caracteres, sprites visíveis ou geometria
   convencional na imagem final.

São **três draw calls por quadro**, independentemente do número de glifos. O estado
por célula mora em texturas da GPU, sem objetos Python individuais. O atlas é
gerado uma vez. Na densidade padrão são 214 × 80 = **17.120 células**.

O brilho escolhe entre símbolos de densidade diferente; as bordas usam `- | / \\`.
A escolha não é apenas uma rampa de brilho. O conjunto ASCII foi escolhido para
compatibilidade entre fontes e sistemas. Glifos Unicode adicionais ficam para uma
iteração com verificação de cobertura da fonte.

## Configuração e desempenho

Edite `config.toml`: resolução inicial, célula, VSync, seed, chuva, luz, zoom,
exposição, limiar temporal e fonte. Reduzir densidade aumenta o tamanho das células
e diminui o trabalho dos dois passes intermediários.

O título mostra FPS, tempo médio, número de células, RSS do processo e uma estimativa
das texturas alocadas. A estimativa não inclui memória do driver, swapchain nem todas
as alocações internas; não é uma medição de VRAM total. FPS de execução comum inclui
apresentação/VSync e pode refletir fila da GPU. Para uma medição sincronizada:

```powershell
.\.venv\Scripts\python.exe -m glyphworld --frames 900 --no-vsync --benchmark benchmark.json --capture captures\final.png
```

O benchmark chama `ctx.finish()` após apresentação e registra média, p95, amostras,
GPU, driver, resolução e grade. Usa até os últimos 600 quadros. Não há garantia de
60 FPS; medir novamente no computador e configuração reais.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m glyphworld --hidden --frames 120 --capture captures\smoke.png --benchmark benchmark-smoke.json
```

O primeiro comando testa configuração, cobertura da grade, atlas, seed, câmera,
animação e pausa. O segundo é um teste integrado real e precisa de GPU e sessão
gráfica, mesmo com janela oculta. Não deve ser tratado como teste puramente headless.

## Estrutura

```text
glyphworld/
  __main__.py       janela, loop, eventos, benchmark e captura
  renderer.py       passes, texturas, redimensionamento e recursos
  atlas.py          atlas compartilhado e descoberta de fonte
  config.py         TOML validado e dimensionamento da grade
  scene.py          paleta procedural reproduzível
  character.py      movimento demonstrativo
  camera.py         acompanhamento suave e zoom
  lighting.py       estado e tempo da atmosfera
  metrics.py        tempos e memória RSS
  shaders/          cena, seleção temporal e composição por glifos
tests/              testes sem interface gráfica
tools/              harness Windows opcional de validação dos shaders
docs/               captura real e relatório de validação
```

## Limitações e próximos passos

Prioridade seguinte: validar instalação e interação na janela principal, registrar
benchmark de 900 quadros e ajustar a direção artística com o vídeo de referência.
O vídeo e a conversa compartilhada não puderam ser inspecionados neste ambiente;
a implementação segue a especificação textual fornecida.

Depois: reprojeção temporal por movimento (hoje o histórico é por célula de tela),
atlas com cobertura calibrada, silhueta mais expressiva, composição de cenários em
segmentos menos repetitivos, colisão simples e testes Linux. Só então adicionar
memória e tomada de decisões do personagem.

Documentação técnica consultada: [ModernGL Context](https://moderngl.readthedocs.io/en/stable/reference/context.html)
e [GLFW Window guide](https://www.glfw.org/docs/latest/window_guide.html).
