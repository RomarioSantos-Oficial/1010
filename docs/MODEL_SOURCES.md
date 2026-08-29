# Fontes e integridade dos modelos locais

Somente pesos baixados de páginas oficiais ou repositórios mantidos pelos autores
foram usados. Os arquivos ficam em `models/` e não são enviados ao Git.

## Voz feminina principal

- modelo: Kokoro 82M v1.0;
- origem: <https://huggingface.co/hexgrad/Kokoro-82M>;
- revisão fixada: `f3ff3571791e39611d31c381e3a41a3af07b4987`;
- idioma/voz: português brasileiro `p`, voz feminina `pf_dora`;
- licença dos pesos: Apache 2.0, compatível com uso comercial;
- `kokoro-v1_0.pth` SHA-256:
  `496dba118d1a58f5f3db2efc88dbdc216e0483fc89fe6e47ee1f2c53f18ad1e4`;
- `voices/pf_dora.pt` SHA-256:
  `07e4ff987c5d5a8c3995efd15cc4f0db7c4c15e881b198d8ab7f67ecf51f5eb7`.

O modelo `OpenVoiceOS/pipertts_pt-BR_dii` não foi usado: embora seja uma voz
feminina brasileira, sua licença CC BY-NC-ND 4.0 impede o uso comercial planejado.

## Voz Piper de fallback

- origem: <https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR/faber/medium>;
- arquivo ONNX SHA-256:
  `858555e3a064209c57088fe6bd70c4c3dc54d03eaa00c45d5ecaf43a33f95aa7`.

Essa voz não é a identidade vocal principal da Luna.

## Reconhecimento de fala

- modelo: faster-whisper small;
- origem: <https://huggingface.co/Systran/faster-whisper-small>;
- `model.bin` SHA-256:
  `3e305921506d8872816023e4c273e75d2419fb89b24da97b4fe7bce14170d671`.

## Segmentação humana

- motor e modelo: rembg / U2Net Human Segmentation;
- origem: <https://github.com/danielgatis/rembg>;
- o checksum interno publicado pelo próprio rembg foi verificado após o download.

## Ferramentas 3D

- Blender 5.2.1 LTS: <https://www.blender.org/download/lts/5-2/>;
- MPFB 2.0.17: <https://extensions.blender.org/add-ons/mpfb/>;
- VRM Add-on 4.5.0: <https://extensions.blender.org/add-ons/vrm/>.

O Blender portátil e as extensões ficam isolados em `tools/blender/`, também fora
do Git. Os hashes dos pacotes foram conferidos contra o índice oficial de extensões.
