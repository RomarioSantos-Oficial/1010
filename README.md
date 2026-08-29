# Luna IA Local — V0.6

Projeto da Luna, uma influenciadora virtual adulta criada por IA para conversa
local, lives, apresentação de produtos, moda e conteúdo audiovisual. A base segue
o `GUIA_PERSONA_IA_LOCAL.md` e separa cérebro, memória, voz, comércio, segurança e
avatar para permitir evolução sem misturar responsabilidades.

## O que já funciona

- Qwen 3 4B local em GGUF por `llama-cpp-python`;
- memória persistente em SQLite e busca semântica no Qdrant local;
- personalidade, emoção, gesto e ações estruturadas;
- catálogo consultado por ferramentas determinísticas, com preço e estoque reais;
- categorias de moda, moda praia, lingerie, calçados, eletrônicos e bem-estar adulto;
- verificação de maioridade para produtos e narrativas adultas;
- voz feminina brasileira principal com Kokoro e transcrição local com faster-whisper;
- interface web com avatar 2D, microfone, reprodução da voz e estados emocionais;
- base 3D adulta completa em BLEND/GLB, rig com mãos, dedos, pés e âncoras de pegada;
- modo de live local com fila priorizada, deduplicação, moderação e integração OBS configurável;
- bloqueios anteriores ao LLM para menores, mortos, coerção, mutilação e instruções de homicídio.

## Início rápido no Windows

Requer Python 3.11.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-core.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe app.py
```

Abra <http://127.0.0.1:8000>. O servidor escuta somente em `127.0.0.1` por padrão.
Se ele já estiver aberto, uma segunda execução apenas mostrará o endereço existente,
sem tentar abrir novamente o mesmo armazenamento Qdrant.

Os caminhos locais esperados no ambiente validado são:

- LLM: `models/llm/model.gguf`;
- STT: `models/stt/faster-whisper-small`;
- TTS feminino principal: `models/tts/kokoro-82m` (`pf_dora`);
- TTS de fallback: `models/tts/pt_BR-faber-medium.onnx`;
- segmentação humana: `models/vision/rembg/models/u2net_human_seg/u2net_human_seg.onnx`.

Sem o LLM, o sistema pode iniciar com `LLM_PROVIDER=demo` para validar API e interface.

## Voz local

O botão do microfone grava no navegador e envia o áudio para o faster-whisper. A
resposta falada é opcional e começa desativada na interface. Quando o usuário a
ativa, a voz principal é a brasileira feminina `pf_dora`, do Kokoro; o Piper fica
disponível apenas como fallback configurável. O microfone fica bloqueado durante a
reprodução para reduzir realimentação e eco.

Teste real de ida e volta TTS → STT:

```powershell
.\.venv\Scripts\python.exe -m scripts.voice_smoke
```

O WAV de prova é gravado em `outputs/voice/smoke_pt_br.wav`.

## Avatar

- sprite 2D final: `assets/avatar/luna_sprite_v1_1.png`;
- turntable de identidade: `assets/identity/luna_turntable_v1.png`;
- base 3D editável: `assets/avatar/3d/luna_base_v0_1.blend`;
- base 3D portátil: `assets/avatar/3d/luna_base_v0_1.glb`;
- especificação: `assets/avatar/luna_3d_spec.json`.

A base 3D é um manequim técnico adulto realmente rigado. Ela ainda não deve ser
tratada como o modelo final da Luna: escultura de identidade, retopologia,
blendshapes faciais, ajuste de roupas e mapeamento VRM 1.0 continuam pendentes.

O script `scripts/build_luna_3d_base.py` reconstrói a base no Blender portátil com
as extensões oficiais MPFB e VRM instaladas dentro de `tools/blender`.

## Live local e OBS

O modo local de live recebe comentários, remove duplicados, modera bloqueios graves
e seleciona mensagens por prioridade. Ele pode funcionar como prévia sem OBS. Para
controle de cenas, configure `OBS_ENABLED=true`, `OBS_HOST`, `OBS_PORT` e uma senha
forte em `OBS_PASSWORD`; a senha fica somente no `.env`, que não é enviado ao Git.

Cenas autorizadas: `LUNA_CHAT`, `LUNA_PRODUCT`, `LUNA_BREAK` e
`LUNA_STUDIO_RESULT`. O OBS 32.0.1 foi detectado neste computador, mas a conexão real
depende de abrir o OBS e ativar/configurar o servidor WebSocket local.

## Conteúdo adulto e segurança

Narrativas eróticas fictícias e consensuais entre adultos e explicações de produtos
adultos são permitidas após verificação de maioridade. Orientações de produto vêm do
catálogo e das notas de higiene/segurança, sem inventar alegações médicas.

O sistema bloqueia conteúdo sexual ou visual com menores, pessoas mortas, coerção,
mutilação e instruções para matar. Imagens e provadores virtuais ficam limitados à
personagem adulta fictícia Luna; a verificação de idade não remove essas proteções.

## API principal

- `GET /health` — saúde de todos os módulos;
- `POST /chat` — conversa com a Luna;
- `GET /products` — catálogo e filtros;
- `POST /adult/verify` — confirmação de maioridade da sessão;
- `POST /speech/transcribe` — áudio para texto;
- `POST /speech/synthesize` — texto para WAV;
- `GET /speech/devices` — dispositivos de entrada;
- `GET /avatar/state` — estado atual do avatar 2D;
- `GET /avatar/manifest` — identidade e ativos;
- `GET /avatar/3d/manifest` — capacidade e estágio do avatar 3D;
- `GET /live/status` — estado da live, fila e conexão OBS;
- `POST /live/start` e `POST /live/stop` — controla a sessão local;
- `POST /live/comments` — recebe e prioriza comentários;
- `POST /live/process-next` — seleciona e responde a próxima mensagem;
- `GET /memory/{user_id}` e `DELETE /memory/{user_id}` — memória do usuário;
- `GET /docs` — documentação interativa.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.voice_smoke
```

## Próximas etapas do guia

O núcleo, memória, comércio, voz, avatar 2D e prévia local de live estão funcionais.
A conexão real ao OBS ainda precisa da senha/configuração local e das quatro cenas.
A próxima fase visual é transformar a base 3D no corpo/rosto definitivo da Luna,
criar roupas ajustáveis e blendshapes; depois vêm ComfyUI, provador virtual e vídeo.
