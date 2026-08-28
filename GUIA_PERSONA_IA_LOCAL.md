# Persona IA Local — Guia Completo de Implementação

> **Objetivo:** construir em um PC local com Windows e GPU NVIDIA uma personagem virtual persistente capaz de conversar por texto e voz, manter memória de interação, possuir personalidade, usar avatar/imagem consistente, trocar roupas virtualmente, produzir fotos e vídeos, atuar como vendedora virtual e participar de lives via OBS.
>
> **Hardware-alvo considerado:** Ryzen 5 5600G, 32 GB RAM, NVIDIA RTX 3060 8 GB, Windows 64 bits.
>
> **Data da pesquisa:** agosto de 2026.

---

## 1. Resultado final esperado

```text
                         ┌─────────────────────────┐
                         │     PERSONA DIGITAL     │
                         │ identidade + regras     │
                         └────────────┬────────────┘
                                      │
              ┌───────────────────────┼────────────────────────┐
              │                       │                        │
              ▼                       ▼                        ▼
        ┌───────────┐           ┌────────────┐          ┌─────────────┐
        │  CÉREBRO  │           │  MEMÓRIA   │          │  CATÁLOGO   │
        │    LLM    │           │ SQLite +   │          │ produtos /  │
        │  local    │           │ vetores    │          │ estoque     │
        └─────┬─────┘           └──────┬─────┘          └──────┬──────┘
              │                        │                       │
              └───────────────┬────────┴───────────────┬───────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────┐          ┌──────────────┐
                       │ ORQUESTRADOR│          │ APRENDIZADO  │
                       │   Python    │          │ LLM professora│
                       └──────┬──────┘          │ + LoRA       │
                              │                 └──────────────┘
             ┌────────────────┼─────────────────────┐
             │                │                     │
             ▼                ▼                     ▼
       ┌───────────┐    ┌─────────────┐      ┌──────────────┐
       │    VOZ    │    │   AVATAR    │      │   ESTÚDIO    │
       │ STT + TTS │    │ tempo real  │      │ imagem/vídeo │
       └─────┬─────┘    └──────┬──────┘      └──────┬───────┘
             │                 │                    │
             └──────────────┬──┴────────────────────┘
                            ▼
                      ┌─────────────┐
                      │ OBS / LIVE  │
                      │ redes sociais│
                      └─────────────┘
```

A personagem deve ter **dois modos principais**.

### Modo Live / Conversa

- LLM pequeno e quantizado.
- Reconhecimento de voz em tempo real.
- TTS rápido.
- Avatar 2D/3D leve.
- Consulta de memória.
- Consulta de catálogo.
- Resposta a comentários.
- Controle de cenas no OBS.

### Modo Studio

- Geração de imagens.
- Troca de roupas.
- Ensaios publicitários.
- Vídeos.
- Roteiros.
- Campanhas.
- Treinamento LoRA.
- Processos pesados.

Isso é essencial para uma RTX 3060 de 8 GB: não é realista manter LLM, geração de imagem, VTON e vídeo pesados simultaneamente na GPU.

---

# 2. Stack recomendada

| Função | Tecnologia principal |
|---|---|
| LLM | Qwen3-4B |
| Inferência local | llama.cpp / llama-cpp-python |
| STT | faster-whisper |
| TTS rápido | Piper |
| TTS/clonagem opcional | XTTS |
| SQL | SQLite |
| Memória vetorial | Qdrant |
| Embeddings | sentence-transformers |
| Backend | FastAPI |
| Configuração | Pydantic + YAML |
| Geração visual | ComfyUI |
| Virtual try-on | CatVTON |
| Retrato animado | LivePortrait |
| Vídeo/composição | FFmpeg |
| Live | OBS Studio + obs-websocket |
| Fine-tuning | Transformers + PEFT/LoRA |
| Testes | pytest |

---

# 3. LLM local

## Modelo base sugerido

Começar com **Qwen3-4B**.

Referência:

- https://huggingface.co/Qwen/Qwen3-4B

Motivos:

- 4B é uma faixa prática para um PC doméstico.
- Pode rodar quantizado.
- Bom suporte a vários idiomas.
- Integração direta com Transformers.
- Pode receber LoRA depois.

## Motor local

Recomendação principal: **llama.cpp / llama-cpp-python**.

Referências:

- https://github.com/ggerganov/llama.cpp
- https://github.com/abetlen/llama-cpp-python

Estruture a aplicação para poder trocar llama.cpp por Ollama ou Transformers sem reescrever o projeto.

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict]) -> str:
        raise NotImplementedError
```

Exemplo de provider:

```python
from llama_cpp import Llama

class LlamaCppProvider:
    def __init__(self, model_path: str):
        self.llm = Llama(
            model_path=model_path,
            n_ctx=8192,
            n_gpu_layers=-1,
            verbose=False,
        )

    def chat(self, messages):
        result = self.llm.create_chat_completion(
            messages=messages,
            temperature=0.75,
            top_p=0.9,
        )
        return result["choices"][0]["message"]["content"]
```

Para a RTX 3060 8 GB, começar com um GGUF Q4 ou Q5 e medir VRAM e velocidade.

---

# 4. Personalidade

Criar um arquivo separado:

```text
config/persona.yaml
```

Exemplo:

```yaml
name: Luna
language: pt-BR

identity:
  type: virtual_ai_character
  disclosure: true

style:
  warmth: 0.85
  humor: 0.55
  formality: 0.30
  detail: 0.55
  affection: 0.75

sales:
  enabled: true
  consult_catalog_before_price: true
  never_invent_stock: true
  never_invent_product_specs: true

memory:
  remember_interaction_preferences: true
  remember_product_interests: true
  remember_sensitive_personal_data: false

adult_commerce:
  enabled: true
  adults_only: true
```

A personagem pode falar de forma carinhosa e natural, mas deve ser apresentada como personagem/assistente de IA, especialmente em contexto comercial.

---

# 5. Memória

Não tente colocar toda a memória dentro dos pesos do LLM.

Use três níveis:

```text
Memória imediata
    ↓
últimas mensagens em RAM

Memória episódica
    ↓
SQLite
resumos das conversas

Memória semântica
    ↓
Qdrant
busca por significado
```

## SQLite

Guardar apenas informações úteis à interação.

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    display_name TEXT,
    tone_preference TEXT,
    detail_level TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    created_at TEXT NOT NULL
);
```

Exemplos de memória apropriada:

```json
{
  "user_id": "anon_8fc1",
  "preferences": {
    "tone": "carinhoso",
    "response_length": "medio",
    "shopping_style": "discreto"
  },
  "interests": ["moda", "lingerie"]
}
```

Evite inferir ou armazenar atributos pessoais sensíveis que não sejam necessários.

## Qdrant

Referência:

- https://qdrant.tech/documentation/quick-start/

Via Docker:

```powershell
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

Pipeline:

```text
mensagem
 ↓
resumo
 ↓
embedding
 ↓
Qdrant
```

Na próxima interação:

```text
pergunta
 ↓
embedding
 ↓
busca semântica
 ↓
memórias relevantes
 ↓
prompt do LLM
```

---

# 6. Reconhecimento de voz

Use **faster-whisper**.

Referência:

- https://github.com/SYSTRAN/faster-whisper

Instalação:

```powershell
pip install faster-whisper
```

Exemplo:

```python
from faster_whisper import WhisperModel

class SpeechRecognizer:
    def __init__(self):
        self.model = WhisperModel(
            "small",
            device="cuda",
            compute_type="int8_float16",
        )

    def transcribe(self, file_path: str) -> str:
        segments, info = self.model.transcribe(
            file_path,
            language="pt",
            vad_filter=True,
        )
        return " ".join(segment.text.strip() for segment in segments)
```

Se faltar VRAM:

```python
WhisperModel("small", device="cpu", compute_type="int8")
```

---

# 7. TTS

## Piper

Projeto atual mantido pela Open Home Foundation:

- https://github.com/OHF-Voice/piper1-gpl

Instalação:

```powershell
pip install piper-tts
```

Crie uma interface abstrata:

```python
class TTSProvider:
    def speak_to_file(self, text: str, output: str):
        raise NotImplementedError
```

Assim você poderá trocar Piper por XTTS ou outro TTS posteriormente.

## XTTS opcional

Referência:

- https://github.com/coqui-ai/TTS

Útil quando a personagem precisar de uma voz clonada/autoral mais específica.

Use apenas amostras de voz que você tenha direito de usar.

---

# 8. Estado emocional simulado

Estados não representam sentimentos reais. Eles servem para controlar linguagem, expressão e animação.

```python
from dataclasses import dataclass

@dataclass
class PersonaState:
    warmth: float = 0.8
    energy: float = 0.7
    humor: float = 0.5
    confidence: float = 0.7
    expression: str = "neutral"
```

A resposta interna pode ser estruturada:

```json
{
  "spoken_text": "Claro! Posso te mostrar algumas opções.",
  "emotion": "happy",
  "action": "show_product",
  "action_args": {
    "sku": "LING-001"
  },
  "memory_candidate": null
}
```

Depois:

```text
spoken_text -> TTS
emotion -> avatar
action -> ferramenta registrada
```

---

# 9. Catálogo comercial

Nunca faça o LLM inventar preço, estoque ou características técnicas.

Estrutura:

```text
commerce/
├── catalog.py
├── inventory.py
├── recommendation.py
├── order_tools.py
└── catalog.db
```

Exemplo:

```json
{
  "sku": "LING-001",
  "name": "Conjunto Aurora",
  "category": "lingerie",
  "price": 149.90,
  "stock": {
    "P": 3,
    "M": 8,
    "G": 4
  },
  "description": "Conjunto em renda...",
  "images": ["products/LING-001/front.png"]
}
```

Fluxo:

```text
"Tem tamanho G?"
 ↓
LLM identifica intenção
 ↓
get_product_stock("LING-001", "G")
 ↓
resultado real do banco
 ↓
LLM transforma em resposta natural
```

---

# 10. Modo comercial 18+

Criar um módulo separado:

```text
adult_commerce/
├── age_gate.py
├── product_policy.py
├── catalog.py
└── response_style.py
```

Ele pode atender produtos legais para adultos, lingerie, bem-estar sexual e produtos de sex shop.

Não tente contornar regras de APIs comerciais. Se um provedor não permitir determinado conteúdo, use um modelo/local ou serviço cuja licença e política sejam compatíveis com seu caso de uso.

Mesmo nesse modo, mantenha bloqueios mínimos contra conteúdo ilegal, exploração, coerção ou menores.

---

# 11. Identidade visual

As imagens existentes da personagem devem formar um conjunto mestre.

```text
assets/identity/
├── original/
│   ├── face_front.png
│   ├── face_34_left.png
│   ├── face_34_right.png
│   ├── profile_left.png
│   ├── body_front.png
│   └── body_side.png
├── curated/
├── masks/
├── captions/
└── metadata.json
```

O sistema deve escolher automaticamente a referência correta dependendo do trabalho.

```text
pedido
 ↓
"personagem usando vestido X"
 ↓
ReferenceSelector
 ↓
escolhe pose/corpo apropriados
 ↓
virtual try-on / geração
```

---

# 12. ComfyUI

Use **ComfyUI** como backend visual local.

Referências:

- https://github.com/Comfy-Org/ComfyUI
- https://www.comfy.org/

Ele será executado separadamente e chamado pelo Python por API.

Estrutura:

```text
visual/
├── comfy_client.py
├── workflows/
│   ├── portrait.json
│   ├── tryon.json
│   ├── campaign.json
│   └── animation.json
└── outputs/
```

Não coloque toda a lógica de geração visual dentro de `main.py`.

---

# 13. Troca de roupa — Virtual Try-On

Para uma peça real do catálogo, use Virtual Try-On.

Uma opção pesquisada:

- https://github.com/Zheng-Chong/CatVTON

O projeto relata inferência perto de 8 GB de VRAM em 1024×768 com bf16.

Na RTX 3060 8 GB, implemente um gerenciador de GPU.

```text
Modo conversa:
LLM na GPU

usuário pede foto
 ↓
GPU Manager
1. descarrega LLM da GPU
2. limpa recursos
3. executa CatVTON
4. salva resultado
5. descarrega CatVTON
6. recarrega LLM
```

Base:

```python
import gc
import torch


def free_gpu():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
```

Cada modelo deve ter também seu próprio método `unload()`.

---

# 14. GPU Manager

```python
import asyncio
import gc
import torch

class GPUManager:
    def __init__(self):
        self.active_model = None
        self.lock = asyncio.Lock()

    async def switch_to(self, service):
        async with self.lock:
            if self.active_model is not None:
                await self.active_model.unload()

            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            await service.load()
            self.active_model = service
```

O `asyncio.Lock()` impede que dois modelos pesados tentem usar a GPU simultaneamente.

---

# 15. Validação visual do produto

Para venda, não basta gerar uma imagem bonita. É preciso conferir fidelidade ao produto.

```text
produto original
      ↓
CatVTON
      ↓
imagem gerada
      ↓
Vision Validator
      ↓
score
```

Avaliar:

- cor;
- padrão;
- tipo de peça;
- logotipo;
- mangas;
- comprimento;
- decote;
- detalhes principais.

Se o resultado divergir demais, rejeite e regenere.

---

# 16. Avatar em tempo real

Não use diffusion de vídeo a cada frase da live.

## V1

Avatar 2D simples:

- PNG principal;
- olhos abertos/fechados;
- boca aberta/fechada;
- expressões;
- idle;
- listening;
- thinking;
- speaking.

## V2

Avaliar LivePortrait:

- https://github.com/KwaiVGI/LivePortrait

LivePortrait é útil para animação e retargeting de retratos.

## V3

Criar um avatar 3D persistente em Blender/Godot/Unity/Unreal.

Não gere o personagem 3D novamente a cada conversa.

---

# 17. Avatar 3D

Pipeline:

```text
fotos de identidade
     ↓
modelagem/reconstrução
     ↓
modelo 3D
     ↓
rig corporal
     ↓
blendshapes faciais
     ↓
lip sync
     ↓
render em tempo real
```

Prioridade correta:

1. chat;
2. memória;
3. voz;
4. avatar 2D;
5. OBS;
6. depois 3D.

---

# 18. OBS e live

OBS inclui `obs-websocket` nas versões modernas.

Referência:

- https://github.com/obsproject/obs-websocket

Estrutura:

```text
live/
├── obs_controller.py
├── chat_adapter.py
├── event_queue.py
├── live_agent.py
└── moderation.py
```

O Python pode controlar:

- cenas;
- produto exibido;
- banners;
- avatar;
- imagem gerada;
- áudio;
- overlays.

Exemplo:

```python
class OBSController:
    def show_product(self, sku: str):
        ...

    def set_scene(self, scene: str):
        ...

    def set_avatar_expression(self, expression: str):
        ...
```

Proteja o WebSocket do OBS com senha.

---

# 19. Pipeline de conversa completo

```text
Microfone
 ↓
VAD
 ↓
faster-whisper
 ↓
texto
 ↓
Intent Router
 ├── conversa
 ├── catálogo
 ├── memória
 ├── gerar imagem
 ├── gerar vídeo
 └── OBS
 ↓
Memory Retriever
 ↓
Persona Builder
 ↓
LLM
 ↓
Response Validator
 ↓
TTS
 ↓
Audio Player
 ↓
Lip Sync / Avatar
```

---

# 20. Orquestrador

```python
class Orchestrator:

    async def process(self, user_id: str, text: str):
        memories = await self.memory.retrieve(user_id, text)

        intent = await self.router.classify(text)

        tool_context = None
        if intent.requires_tool:
            tool_context = await self.tools.execute(intent)

        messages = self.prompt_builder.build(
            user_id=user_id,
            text=text,
            memories=memories,
            tool_context=tool_context,
        )

        answer = self.llm.chat(messages)
        validated = self.validator.validate(answer)

        await self.memory.observe(
            user_id=user_id,
            user_text=text,
            assistant_text=validated.spoken_text,
        )

        audio = await self.tts.synthesize(validated.spoken_text)

        await self.avatar.react(
            emotion=validated.emotion,
            audio=audio,
        )

        return validated
```

---

# 21. Ferramentas registradas

Nunca execute texto arbitrário do LLM como comando do sistema.

Errado:

```python
os.system(llm_response)
```

Correto:

```python
TOOLS = {
    "get_stock": get_stock,
    "show_product": show_product,
    "generate_campaign": generate_campaign,
}
```

O LLM só pode solicitar ferramentas previamente registradas e validadas.

---

# 22. Fila de mensagens na live

```text
comentários
 ↓
Priority Queue
 ├── pergunta sobre produto
 ├── pergunta direta
 ├── interação social
 └── spam
 ↓
selecionar
 ↓
responder
```

```python
from dataclasses import dataclass

@dataclass
class LiveMessage:
    user_id: str
    text: str
    priority: int
    timestamp: float
```

---

# 23. Geração de imagem

O LLM deve gerar uma solicitação estruturada para o motor visual.

```json
{
  "task": "product_campaign",
  "identity": "luna",
  "product_sku": "DRESS-004",
  "style": "elegant",
  "scene": "studio",
  "aspect_ratio": "9:16",
  "count": 4
}
```

O pipeline decide:

```text
roupa real?
    SIM -> VTON
    NÃO -> geração normal

precisa pose?
    SIM -> controle de pose

precisa preservar identidade?
    SIM -> referência/adapter/LoRA
```

---

# 24. LoRA visual da personagem

Depois de curar boas referências, treine um LoRA visual para reforçar consistência.

Não use LoRA sozinho como garantia de identidade.

Combine:

- LoRA;
- imagem de referência;
- controle de pose;
- controle facial;
- validador de identidade.

---

# 25. Vídeos

Não comece com um modelo pesado de vídeo generativo.

Primeira versão:

```text
produto
 ↓
roteiro LLM
 ↓
storyboard
 ↓
imagens da personagem
 ↓
animação
 ↓
TTS
 ↓
legendas
 ↓
FFmpeg
 ↓
MP4
```

FFmpeg será responsável por:

- unir áudio e vídeo;
- recortar para 9:16;
- adicionar legendas;
- ajustar FPS;
- exportar MP4.

---

# 26. Roteiros de campanha

Input:

```json
{
  "sku": "LING-001",
  "platform": "instagram_reels",
  "duration": 20,
  "tone": "elegante"
}
```

Output:

```json
{
  "hook": "...",
  "scenes": [
    {
      "seconds": "0-4",
      "speech": "...",
      "visual": "close_up"
    }
  ],
  "cta": "..."
}
```

---

# 27. Aprendizado com uma LLM professora

A personagem não deve modificar seus pesos depois de cada conversa.

Use este ciclo:

```text
interações
 ↓
interaction_logger
 ↓
anonimização
 ↓
LLM professora
 ↓
resposta candidata
 ↓
LLM crítica
 ↓
score
 ↓
dataset staging
 ↓
testes
 ↓
LoRA nova
```

A memória muda imediatamente. Os pesos mudam apenas em versões controladas.

---

# 28. Dataset

Formato JSONL:

```json
{"messages":[
  {"role":"system","content":"Você é Luna..."},
  {"role":"user","content":"Pode me ajudar a escolher?"},
  {"role":"assistant","content":"Claro. Você prefere algo mais discreto ou mais marcante?"}
]}
```

Para estoque:

```json
{"messages":[
  {"role":"user","content":"Tem no tamanho G?"},
  {"role":"assistant","content":"Vou consultar o estoque antes de te responder."}
]}
```

Treine o comportamento de consultar ferramentas, não preços específicos que mudam.

---

# 29. Registro de exemplos de treinamento

```json
{
  "interaction_id": "abc",
  "user_text": "...",
  "assistant_text": "...",
  "context": "...",
  "feedback": 1,
  "teacher_score": 0.91,
  "persona_score": 0.95,
  "sales_accuracy_score": 1.0,
  "eligible_for_training": true
}
```

Só exemplos aprovados entram no dataset final.

---

# 30. Fine-tuning com PEFT / LoRA

Referências:

- https://huggingface.co/docs/peft/
- https://huggingface.co/docs/peft/main/package_reference/lora

Ambiente separado:

```powershell
py -3.11 -m venv .venv-training
.\.venv-training\Scripts\Activate.ps1
pip install torch transformers datasets accelerate peft trl
```

Esqueleto:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model

MODEL = "Qwen/Qwen3-4B"

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    device_map="auto",
)

config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules="all-linear",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, config)
model.print_trainable_parameters()
```

Na RTX 3060 8 GB, usar treinamento eficiente, batches pequenos, gradient accumulation e quantização quando compatível.

---

# 31. “Token próprio”

Não crie um tokenizer novo sem necessidade.

Use:

```text
Qwen tokenizer
      +
Qwen base model
      +
LoRA da personagem
      +
memória externa
```

O que evolui é a personalidade e o comportamento, não o vocabulário básico do tokenizer.

---

# 32. Versionamento

```text
models/lora/
├── luna-v1/
├── luna-v2/
├── luna-v3/
└── registry.json
```

Exemplo:

```json
{
  "production": "luna-v2",
  "candidate": "luna-v3",
  "rollback": "luna-v1"
}
```

Nunca substituir automaticamente a versão estável sem testes.

---

# 33. Testes de regressão

Criar perguntas fixas:

```text
1. Quem é você?
2. Você é uma pessoa real?
3. Qual o preço deste produto inexistente?
4. Tem tamanho G sem consultar o catálogo?
5. Lembre minha preferência de resposta.
6. Responda em português.
7. Cliente reclama do preço.
8. Cliente quer alternativa.
```

Medir:

- consistência da personalidade;
- naturalidade;
- precisão;
- alucinação;
- uso correto de ferramentas;
- latência;
- tamanho da resposta.

---

# 34. Estrutura completa de diretórios

```text
persona_ai/
│
├── app.py
├── requirements-core.txt
├── pyproject.toml
├── .env
├── README.md
│
├── config/
│   ├── persona.yaml
│   ├── app.yaml
│   └── models.yaml
│
├── core/
│   ├── orchestrator.py
│   ├── event_bus.py
│   ├── gpu_manager.py
│   ├── model_registry.py
│   └── state.py
│
├── brain/
│   ├── llm_provider.py
│   ├── llama_cpp_provider.py
│   ├── ollama_provider.py
│   ├── prompt_builder.py
│   ├── tool_router.py
│   └── response_validator.py
│
├── persona/
│   ├── identity.py
│   ├── emotion.py
│   ├── relationship_state.py
│   └── style.py
│
├── memory/
│   ├── sqlite_store.py
│   ├── qdrant_store.py
│   ├── embeddings.py
│   ├── retrieval.py
│   ├── summarizer.py
│   └── schemas.py
│
├── speech/
│   ├── microphone.py
│   ├── vad.py
│   ├── stt_whisper.py
│   ├── tts.py
│   ├── piper_tts.py
│   ├── audio_player.py
│   └── lip_sync.py
│
├── avatar/
│   ├── controller.py
│   ├── expressions.py
│   ├── avatar_2d.py
│   └── liveportrait_adapter.py
│
├── vision/
│   ├── image_analyzer.py
│   ├── reference_selector.py
│   ├── product_validator.py
│   └── identity_validator.py
│
├── visual/
│   ├── comfy_client.py
│   ├── catvton_client.py
│   ├── image_pipeline.py
│   ├── video_pipeline.py
│   └── workflows/
│
├── commerce/
│   ├── catalog.py
│   ├── inventory.py
│   ├── recommendation.py
│   ├── order_tools.py
│   └── database.db
│
├── adult_commerce/
│   ├── age_gate.py
│   ├── policy.py
│   └── style.py
│
├── learning/
│   ├── interaction_logger.py
│   ├── dataset_builder.py
│   ├── teacher.py
│   ├── critic.py
│   ├── trainer.py
│   ├── evaluator.py
│   └── versions.py
│
├── live/
│   ├── obs_controller.py
│   ├── live_agent.py
│   ├── chat_queue.py
│   └── platform_adapters/
│
├── api/
│   ├── server.py
│   └── routes/
│
├── ui/
│   ├── desktop.py
│   └── web/
│
├── assets/
│   ├── identity/
│   ├── products/
│   ├── avatar/
│   └── voices/
│
├── data/
│   ├── app.db
│   ├── conversations/
│   ├── datasets/
│   └── generated/
│
├── models/
│   ├── llm/
│   ├── lora/
│   ├── tts/
│   └── visual/
│
└── tests/
    ├── test_memory.py
    ├── test_catalog.py
    ├── test_persona.py
    ├── test_tools.py
    ├── test_speech.py
    └── test_regression.py
```

---

# 35. Ambiente Python no Windows

Prefira Python 3.11 para maximizar compatibilidade.

```powershell
mkdir persona_ai
cd persona_ai

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
```

Se PowerShell bloquear a ativação:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

# 36. Dependências iniciais

Criar `requirements-core.txt`:

```txt
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
aiosqlite
httpx
websockets
pyyaml
numpy
sounddevice
soundfile
faster-whisper
qdrant-client
sentence-transformers
llama-cpp-python
pytest
pytest-asyncio
```

Instalar:

```powershell
pip install -r requirements-core.txt
pip install piper-tts
```

---

# 37. Ambientes separados

Recomendado:

```text
.venv-core       -> app, LLM, memória e voz
.venv-training   -> Transformers, PEFT e treinamento
ComfyUI/venv     -> geração visual
LivePortrait/env -> animação
```

Evita conflitos de PyTorch, CUDA, diffusers, numpy e onnxruntime.

---

# 38. Prompt Builder

Monte o prompt em camadas.

```text
SYSTEM
├── identidade
├── personalidade
├── regras comerciais
├── estado atual
├── horário
├── memórias relevantes
├── contexto do catálogo
└── instrução atual
```

Exemplo:

```python
def build_system_prompt(persona, memories, state):
    return f"""
Você é {persona.name}, uma personagem virtual de IA.

IDENTIDADE:
{persona.identity}

ESTILO:
{persona.style}

ESTADO SIMULADO:
{state}

MEMÓRIAS RELEVANTES:
{memories}

Regras:
- Não invente preço ou estoque.
- Consulte ferramentas comerciais quando necessário.
- Não diga ser humana.
- Converse naturalmente em português brasileiro.
"""
```

---

# 39. FastAPI

Endpoints iniciais:

```text
POST /chat
POST /speech/transcribe
POST /speech/synthesize
POST /image/generate
POST /image/tryon
POST /video/generate
GET  /products/{sku}
GET  /memory/{user_id}
POST /live/start
POST /live/stop
```

Executar:

```powershell
uvicorn api.server:app --host 127.0.0.1 --port 8000
```

Durante desenvolvimento, mantenha serviços apenas em localhost.

---

# 40. Arquivo .env

```env
APP_ENV=development
DATABASE_URL=sqlite:///data/app.db
QDRANT_URL=http://127.0.0.1:6333
OBS_HOST=127.0.0.1
OBS_PORT=4455
OBS_PASSWORD=troque_isto
COMFY_URL=http://127.0.0.1:8188
LLM_MODEL_PATH=models/llm/model.gguf
```

Adicione `.env` ao `.gitignore`.

---

# 41. Interface

Primeira versão pode ser PySide6 ou web.

Para crescer como produto, uma combinação boa é:

```text
React frontend
    ↓
FastAPI
    ↓
serviços locais
```

Tela sugerida:

```text
┌───────────────────────────────────────────────────────┐
│ Luna                                 ● LOCAL           │
├────────────────────┬──────────────────────────────────┤
│                    │ Chat                             │
│      AVATAR        │                                  │
│                    │ [mensagens]                      │
│                    │                                  │
├────────────────────┼──────────────────────────────────┤
│ Estado             │ [🎙] Digite uma mensagem...     │
│ LLM: ativo         │                                  │
│ Voz: ativa         │                                  │
│ Memória: ativa     │                                  │
└────────────────────┴──────────────────────────────────┘

[Studio] [Produtos] [Memórias] [Treinamento] [Live]
```

---

# 42. Privacidade

Configurações recomendadas:

```text
[x] memória de preferências
[x] histórico de produtos
[ ] salvar transcrição integral
[ ] usar interação para treinamento
```

Permitir:

- visualizar memória;
- apagar memória;
- desligar aprendizado;
- apagar histórico.

---

# 43. Logs

```text
logs/
├── app.log
├── errors.log
├── llm.log
├── generation.log
└── live.log
```

Nunca salve em log:

- senhas;
- tokens;
- dados de pagamento.

---

# 44. Roadmap funcional

## V0.1
- chat local;
- Qwen;
- llama.cpp.

## V0.2
- SQLite;
- memória simples.

## V0.3
- Qdrant;
- memória semântica.

## V0.4
- faster-whisper;
- Piper;
- conversa por voz.

## V0.5
- avatar 2D;
- expressões.

## V0.6
- catálogo;
- vendas.

## V0.7
- OBS;
- live local.

## V0.8
- identidade visual;
- ComfyUI.

## V0.9
- CatVTON;
- troca de roupa.

## V1.0
- integração completa.

## V1.1
- campanhas.

## V1.2
- vídeo.

## V1.3
- LLM professora.

## V1.4
- LoRA da personalidade.

## V2.0
- avatar 3D avançado.

---

# 45. Ordem de implementação

```text
PASSO 01  Criar repositório
PASSO 02  Criar Python 3.11 venv
PASSO 03  Criar estrutura de diretórios
PASSO 04  Implementar LLMProvider
PASSO 05  Rodar Qwen GGUF
PASSO 06  Criar persona.yaml
PASSO 07  Criar PromptBuilder
PASSO 08  Criar SQLite
PASSO 09  Criar MemoryService
PASSO 10  Adicionar Qdrant
PASSO 11  Adicionar embeddings
PASSO 12  Adicionar faster-whisper
PASSO 13  Adicionar Piper
PASSO 14  Criar VoiceLoop
PASSO 15  Criar PersonaState
PASSO 16  Criar avatar 2D
PASSO 17  Criar catálogo
PASSO 18  Criar ToolRouter
PASSO 19  Criar modo comercial
PASSO 20  Instalar OBS
PASSO 21  Criar OBSController
PASSO 22  Criar LiveAgent
PASSO 23  Instalar ComfyUI separadamente
PASSO 24  Criar ComfyClient
PASSO 25  Curar referências visuais
PASSO 26  Criar ReferenceSelector
PASSO 27  Integrar identidade visual
PASSO 28  Instalar/testar CatVTON
PASSO 29  Criar GPUManager
PASSO 30  Integrar Virtual Try-On
PASSO 31  Criar ProductValidator
PASSO 32  Criar pipeline de campanha
PASSO 33  Criar pipeline de vídeo simples
PASSO 34  Criar interaction_logger
PASSO 35  Criar dataset_builder
PASSO 36  Criar teacher/critic
PASSO 37  Treinar primeiro LoRA
PASSO 38  Criar testes de regressão
PASSO 39  Criar versionamento
PASSO 40  Promover primeira versão estável
```

---

# 46. Milestones detalhadas

## Milestone 1 — Chat local

Objetivo:

```text
Usuário -> LLM -> resposta
```

Critérios:

- modelo abre;
- responde em português;
- histórico funciona;
- latência aceitável.

## Milestone 2 — Memória

```text
Usuário:
"Gosto de respostas mais curtas."

mais tarde:
"Explique esse produto."

IA:
responde de forma curta
```

A memória deve sobreviver a reinicialização.

## Milestone 3 — Voz

```text
microfone
 ↓
STT
 ↓
LLM
 ↓
TTS
 ↓
alto-falante
```

Impedir que o microfone transcreva a própria voz da personagem.

## Milestone 4 — Avatar

Estados mínimos:

```text
idle
listening
thinking
speaking
happy
neutral
```

## Milestone 5 — Catálogo

Criar 10 produtos fictícios de teste e validar:

- estoque;
- tamanhos;
- preços;
- produto inexistente;
- recomendação alternativa.

## Milestone 6 — OBS

Cenas:

```text
LUNA_CHAT
LUNA_PRODUCT
LUNA_BREAK
LUNA_STUDIO_RESULT
```

## Milestone 7 — ComfyUI

Testes:

```text
texto -> imagem
referência -> identidade consistente
produto -> campanha
```

## Milestone 8 — Virtual Try-On

```text
foto personagem + foto roupa -> personagem usando roupa
```

## Milestone 9 — Vídeo

Começar com imagem + animação + voz + legenda.

## Milestone 10 — Aprendizado

```text
coletar -> anonimizar -> avaliar -> selecionar -> treinar -> testar -> versionar
```

---

# 47. Benchmark

Criar `benchmark.py` para medir:

```text
STT latency
LLM first-token latency
LLM tokens/s
TTS latency
time to first audio
avatar FPS
GPU VRAM
RAM
image generation time
try-on generation time
```

Salvar resultados em CSV.

---

# 48. Estratégia específica para RTX 3060 8 GB

## Conversa

```text
LLM 4B quantizado
Whisper small no CPU se necessário
Piper no CPU
avatar leve
```

## Try-on

```text
descarregar LLM da GPU
CatVTON -> GPU
finalizar
descarregar CatVTON
recarregar LLM
```

## Vídeo

Mesmo princípio.

Evite manter simultaneamente:

- LLM 4B inteiro na GPU;
- Whisper grande;
- diffusion;
- VTON;
- vídeo diffusion.

---

# 49. Arquitetura final

```text
                         ┌───────────────┐
                         │      UI       │
                         └───────┬───────┘
                                 │
                         ┌───────▼───────┐
                         │    FastAPI    │
                         └───────┬───────┘
                                 │
                    ┌────────────▼────────────┐
                    │      ORCHESTRATOR       │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼────────┐     ┌─────────▼────────┐      ┌────────▼────────┐
│ Brain Service  │     │ Memory Service   │      │ Commerce Service│
│ llama.cpp      │     │ SQLite + Qdrant  │      │ SQL / APIs      │
└───────┬────────┘     └──────────────────┘      └─────────────────┘
        │
┌───────▼─────────────────────────────────────────────────────────┐
│                         EVENT BUS                               │
└───────┬───────────────┬─────────────────────┬──────────────────┘
        │               │                     │
┌───────▼──────┐ ┌──────▼──────┐      ┌──────▼──────────┐
│ Speech       │ │ Avatar       │      │ Studio          │
│ Whisper/TTS  │ │ 2D/3D        │      │ Comfy/VTON      │
└───────┬──────┘ └──────┬──────┘      └──────┬──────────┘
        │               │                    │
        └───────────────┼────────────────────┘
                        ▼
                  ┌───────────┐
                  │    OBS    │
                  └───────────┘
```

---

# 50. Exemplo de interação final

```text
Pessoa:
"Oi, me mostra alguma coisa elegante."

Persona:
consulta memória:
- prefere recomendações discretas

consulta catálogo:
- encontra opções

Persona fala:
"Claro. Separei uma opção mais delicada que combina com o estilo que você costuma pedir."

OBS:
mostra produto

Pessoa:
"Como ficaria em você?"

Persona:
"Posso preparar uma simulação para você."

Studio Queue:
- escolhe referência
- carrega produto
- executa VTON
- valida resultado
- salva imagem

OBS:
mostra imagem gerada

Persona:
"Essa é uma simulação de como a peça pode ficar."
```

---

# 51. Fontes pesquisadas

## PEFT / LoRA

- https://huggingface.co/docs/peft/
- https://huggingface.co/docs/peft/main/package_reference/lora

## Qwen

- https://huggingface.co/Qwen/Qwen3-4B

## llama.cpp / Python

- https://github.com/ggerganov/llama.cpp
- https://github.com/abetlen/llama-cpp-python

## faster-whisper

- https://github.com/SYSTRAN/faster-whisper

## Piper

- https://github.com/OHF-Voice/piper1-gpl

## XTTS

- https://github.com/coqui-ai/TTS

## Qdrant

- https://qdrant.tech/documentation/quick-start/

## ComfyUI

- https://github.com/Comfy-Org/ComfyUI
- https://www.comfy.org/

## CatVTON

- https://github.com/Zheng-Chong/CatVTON

## LivePortrait

- https://github.com/KwaiVGI/LivePortrait

## OBS WebSocket

- https://github.com/obsproject/obs-websocket

---

# 52. Decisões técnicas importantes

1. **Não treinar um LLM do zero inicialmente.** Use modelo-base + LoRA.
2. **Não usar fine-tuning como memória pessoal.** Use SQLite/Qdrant.
3. **Não alterar pesos após toda conversa.** Crie versões controladas.
4. **Não executar comandos arbitrários do LLM.** Use ferramentas registradas.
5. **Não confiar no LLM para estoque/preço.** Consulte o banco/API.
6. **Não usar diffusion pesado durante a live.** Use avatar em tempo real.
7. **Não manter todos os modelos na GPU de 8 GB.** Use GPU Manager.
8. **Não criar tokenizer próprio sem necessidade.** Use o tokenizer do modelo-base.
9. **Não depender de uma única foto para identidade.** Use conjunto curado.
10. **Para roupa real, use VTON.** Prompt simples não garante fidelidade.

---

# 53. Próxima etapa de desenvolvimento

Depois deste guia, o primeiro código a ser construído deve ser uma V0.1 com:

```text
Qwen local
+
llama.cpp
+
persona.yaml
+
SQLite
+
FastAPI
+
testes
```

Quando ela estiver estável, avance para voz, avatar, catálogo, OBS e geração visual.

