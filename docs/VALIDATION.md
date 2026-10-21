# Validação — 21 de outubro de 2026

## Resultados efetivamente obtidos

- Python 3.12.14 no Windows.
- **10 testes unitários aprovados**, usando `unittest`, NumPy e Pillow.
- Compilação sintática dos módulos Python via `compileall` aprovada.
- **3 shaders compilados e vinculados pelo driver Intel UHD Graphics**,
  OpenGL 4.6.0, build 32.0.101.5972.
- Os três passes foram executados em buffers reais da GPU, em 1280 × 720,
  com uma grade de 214 × 80 células.
- Captura real em `preview.png`, produzida com o atlas gerado pela implementação.
- Comparação de quadros confirma animação; comparação com tempo congelado confirma
  estabilidade. Índices do campo foram lidos de volta e verificados quanto a
  valores finitos e intervalo do atlas.
- Quatro mapas de diagnóstico e a combinação chuva/luz desligadas renderizaram
  sem erros OpenGL no harness.

Resultados numéricos do ensaio estão em `gpu-probe.json`. O teste mede apenas
os shaders através de um pequeno harness ctypes/WGL, com janela **oculta**,
framebuffer fora da tela, sincronização `glFinish`, sem apresentação nem VSync.
São 90 quadros, descartando os primeiros 10. **Não é o FPS da aplicação**,
não valida GLFW/ModernGL, não constitui teste de longa duração e não demonstra
que a meta de 60 FPS na janela foi atingida.

## Bloqueios do ambiente

A instalação de ModernGL, GLFW e psutil falhou porque o ambiente não conseguiu
resolver `pypi.org`. A tentativa de iniciar a aplicação principal terminou com
a mensagem explícita de dependências ausentes. Portanto, a janela principal,
eventos de teclado, redimensionamento, uso de memória do processo e apresentação
continuam **pendentes de validação integrada**. Não foram inventados resultados
para esses itens. O acesso ao vídeo de referência e ao link de conversa também
não permitiu sua inspeção; a referência usada foi a especificação textual.

## Reproduzir a validação

Na raiz do projeto, com dependências instaladas:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q glyphworld tests
python -m glyphworld --hidden --frames 120 --capture captures/smoke.png --benchmark benchmark-smoke.json
python -m glyphworld --frames 900 --no-vsync --benchmark benchmark.json
```

O harness opcional de GPU usa somente Python, NumPy, Pillow e o OpenGL do Windows:

```powershell
python tools/render_probe_windows.py
```

Ele atualiza a captura e o JSON em `docs/`; capturas adicionais vão para `captures/`.
Não é um backend do jogo e não introduz dependência Windows no renderer principal.

## Checklist manual pendente

- Abrir janela visível com `start_windows.bat` em uma instalação nova.
- Pausar e verificar que câmera, personagem, chuva e vegetação param.
- Testar cada controle documentado; confirmar que F12 cria PNG válido.
- Redimensionar, minimizar/restaurar e trocar densidade repetidamente.
- Comparar RSS antes/depois das trocas para detectar crescimento continuado.
- Executar por pelo menos 15 minutos e examinar repetição procedural e cintilação.
- Validar Linux separadamente.

O protótipo não é declarado integralmente concluído enquanto a validação da
aplicação principal permanecer pendente.
