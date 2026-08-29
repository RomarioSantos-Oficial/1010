# Conformidade com o guia e o relatório técnico — V0.5

Verificação realizada em 28 de agosto de 2026 contra:

- `GUIA_PERSONA_IA_LOCAL.md`;
- relatório técnico fornecido para o repositório `RomarioSantos-Oficial/1010`.

## Resultado por versão

| Fase | Estado | Evidência principal | Pendência real |
|---|---|---|---|
| V0.1 — chat local | Aprovada | Qwen GGUF, providers intercambiáveis, persona YAML, SQLite, FastAPI e testes | benchmark CUDA ainda não criado |
| V0.2 — memória | Aprovada | MemoryCandidate, embeddings, Qdrant local, deduplicação, atualização, isolamento, exclusão e contexto de 1.000 mensagens testado | sumarizador de conversas antigas ainda não existe |
| V0.3 — comércio | Aprovada | catálogo/estoque SQLite, Pydantic, ActionRouter/ToolRouter, recomendações e age gate | imagens reais de todos os produtos ainda não existem |
| V0.4 — voz | Operacional, parcial | faster-whisper + voz feminina Kokoro, API, microfone web, VAD, proteção contra eco e teste real TTS→STT | interrupção da fala da Luna e testes físicos de ruído/microfone precisam de validação humana |
| V0.5 — avatar | Operacional, parcial | sprite 2D com idle/piscar/falar/feliz e base 3D rigada | lip sync fonético e expressões visuais próprias para triste/surpresa ainda pendentes |
| V0.6+ — live/studio | Pendente | interfaces futuras aparecem no health como offline | OBS, fila de live, ComfyUI, VTON, vídeo e treinamento ainda não foram implementados |

## Pontos do relatório técnico já atendidos

- memória semântica com embeddings e Qdrant;
- recusa de CPF, credenciais e nome desnecessário;
- deduplicação e atualização de preferências antigas;
- campos de criação, atualização, último uso, importância, confiança e contagem;
- isolamento de histórico, memória, sessão e relacionamento por usuário;
- resposta estruturada validada por Pydantic;
- ActionRouter com lista fechada de ferramentas e recusa de ações arbitrárias;
- catálogo, estoque, preço, tamanhos, recomendação e produto inexistente testados;
- ContextManager com limites de histórico, memória e caracteres;
- módulos separados de voz e avatar;
- README refeito em UTF-8 sem bytes nulos;
- `.gitignore` protegendo segredos, bancos, modelos e saídas;
- Ruff, pytest e workflow de CI no GitHub;
- logs sem conteúdo de conversa, request ID em erros e health check expandido.

## Voz feminina opcional

A voz principal é `pf_dora`, brasileira e feminina, do Kokoro 82M. A saída falada
começa desativada na interface e a escolha é guardada localmente no navegador. O
backend também aceita `TTS_ENABLED=false`; nesse caso, o chat por texto continua
funcionando e o health informa TTS offline.

O modelo e a voz foram baixados da revisão oficial fixada, tiveram SHA-256 conferido
e usam licença Apache 2.0. O Piper permanece apenas como fallback.

## Avatar e produtos

O sprite 2D está integrado à conversa. A base 3D contém corpo inteiro, 19.158
vértices, 163 ossos, 38 ossos de dedos/metacarpos e duas âncoras de pegada. Isso
permite começar animação de mãos e posicionamento de produtos.

As orientações de uso de produtos adultos vêm exclusivamente do catálogo e exigem
confirmação 18+. A base 3D ainda não possui as roupas finais nem animações específicas
de demonstração; esses ativos devem ser produzidos e testados por produto.

## Segurança aplicada antes dos modelos

O sistema bloqueia conteúdo sexual ou visual com menores, pessoas mortas, coerção,
mutilação e instruções para homicídio. Narrativas adultas fictícias e consensuais e
orientações de produtos legais são permitidas depois do age gate. O provador visual
aceita somente a personagem adulta fictícia Luna.

## Pendências do guia, sem simulação

- GPU Manager e benchmark de VRAM/tokens por segundo;
- divisão do Prompt Builder em componentes menores e resumo de conversas antigas;
- ReferenceSelector para escolher automaticamente rosto, corpo e pose;
- ComfyUI e modelo visual consistente;
- CatVTON, roupas reais do catálogo e validador de fidelidade do produto;
- blendshapes, lip sync fonético, escultura final de identidade e exportação VRM 1.0;
- OBS, adaptadores de plataformas, moderação e fila de comentários;
- composição de vídeo/FFmpeg;
- professora, dataset, LoRA, avaliação, registro de modelos e rollback.

Essas pendências correspondem às fases V0.6 a V2.0 do guia. Nenhuma delas é marcada
como pronta apenas por existir uma especificação ou um arquivo de referência.
