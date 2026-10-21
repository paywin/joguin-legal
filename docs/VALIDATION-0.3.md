# Validação do GlyphWorld 0.3 — 21/10/2026

## Executado

- Python 3.12.14 no Windows; **20 testes unitários aprovados**.
- Compilação sintática dos módulos Python aprovada.
- Movimento manual em dois eixos, normalização diagonal, pulo/aterrissagem e
  bloqueio de pulo duplo verificados na lógica.
- Colisão com paredes, deslocamentos longos sem atravessar edifícios, ruas entre
  coordenadas positivas/negativas e becos internos verificados.
- Entrada em edifício, colisão interior, restrição de saída à porta e retorno à
  mesma entrada verificados.
- Geração determinística por seed, cache limitado, orçamento e validade das
  caixas de geometria verificados.
- Ciclo de 24 horas, volta à meia-noite, luminosidade de dia/noite e relógio
  congelado verificados.
- Três shaders GLSL compilados e vinculados no driver **Intel UHD Graphics**,
  OpenGL **4.6.0 — Build 32.0.101.5972**.
- Renderização real na GPU: exterior diurno, exterior noturno, interior, mapas
  de diagnóstico e tempo congelado. Índices do atlas lidos de volta e validados.
- As capturas `preview.png`, `preview-night.png` e `preview-interior.png` vêm
  desses shaders. Nenhuma imagem foi gerada por IA para representar execução.

## Escopo da medição de GPU

`gpu-probe.json` contém os resultados medidos em 1280×720 e 256×103 células.
São 90 quadros, descartando dez de aquecimento. Cada amostra inclui criação dos
descritores da cena, upload, três passes e `glFinish` em um harness ctypes/WGL com
janela oculta e framebuffer fora da tela. Não há apresentação/VSync nem loop GLFW.
Assim, **não se deve usar esse valor como FPS da aplicação ou garantia de 60 FPS**.

## Pendente e motivo

A tentativa anterior de instalar ModernGL/GLFW/psutil falhou por resolução de
rede. Nesta etapa, a inspeção confirmou que as dependências seguem ausentes;
a tentativa de obter o pacote oficial pelo navegador não forneceu um arquivo
instalável ao ambiente. A aplicação principal não pôde ser iniciada aqui.

Portanto continuam pendentes: eventos reais de WASD/E/Espaço, janela visível,
redimensionamento/minimização, controle de exposição em execução, consumo RSS
da aplicação e teste prolongado de navegação. A implementação desses recursos
existe, mas os testes lógicos e o harness GPU não substituem essa validação.

## Reproduzir

```powershell
python -m unittest discover -s tests -v
python -m compileall -q glyphworld tests tools
python tools/render_probe_windows.py
python -m glyphworld --hidden --frames 120 --capture captures/smoke.png --benchmark benchmark-smoke.json
python -m glyphworld --frames 900 --no-vsync --benchmark benchmark.json
```

No teste manual, verificar:

1. WASD nas quatro direções, diagonal e parede; Espaço pula e P pausa.
2. Porta ciano: E entra; retorno ao tapete: E sai; posição exterior preservada.
3. N alterna horários; T congela apenas o relógio; R e L alteram atmosfera.
4. Personagem continua identificável atrás de fachadas por meio do recorte local.
5. Trocar densidade, zoom e tamanho da janela, capturar com F12 e observar memória.
6. Caminhar por pelo menos 15 minutos, incluindo quarteirões negativos.

O relatório da versão anterior foi preservado em `VALIDATION-0.2.md`.
