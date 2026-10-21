# Validação 0.4 — 21/10/2026

- 25 testes automatizados passaram, incluindo base ortonormal da câmera,
  movimento relativo à visão, altura dos olhos, limites de pitch e retração por parede.
- Três shaders de produção compilados e executados em Intel UHD Graphics,
  OpenGL 4.6.0, driver 32.0.101.5972, através de contexto WGL oculto.
- Capturas reais: terceira pessoa, primeira pessoa, noite e interior.
- Animação alterou pixels; tempo congelado produziu quadros idênticos;
  índices do atlas permaneceram finitos e válidos; quatro mapas renderizados.
- Medições do harness estão em gpu-probe.json. Não são FPS da aplicação.
- Grade padrão aumentou para 427 × 144, 61.488 glifos, em 1280 × 720.

ModernGL, GLFW e psutil não puderam ser instalados no ambiente. Portanto não
foi validada a janela principal nem a integração dos eventos de mouse/teclado.
Não há garantia de 60 FPS. Linux também não foi executado.
A cidade é uma interpretação procedural de Tóquio, não uma reconstrução geográfica.
