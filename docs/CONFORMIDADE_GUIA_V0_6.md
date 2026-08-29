# Conformidade com o guia e o relatório técnico — V0.6

Verificação incremental realizada em 28 de agosto de 2026. Este documento complementa
`CONFORMIDADE_GUIA_V0_5.md` e registra somente a evolução de conversa, áudio e live.

## Testes reais de conversa

- identidade: Luna se identifica como personagem virtual de IA;
- preferência: registra `azul` e `vestidos longos` separadamente;
- recuperação: responde corretamente à pergunta posterior sobre a preferência;
- saída estruturada: `action=none`, ações inventadas e candidatos de memória inválidos
  não substituem a fala nem vazam JSON bruto;
- segurança: menor sexualizado e instrução de homicídio continuam bloqueados antes do LLM;
- comércio adulto: instrução cadastrada somente após confirmação 18+.

## Teste real de áudio

- TTS: Kokoro, voz feminina `pf_dora`;
- WAV: RIFF válido, 217.244 bytes e 4,525 segundos;
- STT: faster-whisper, idioma `pt`;
- frase transcrita exatamente: “Olá, eu sou Luna. O teste de áudio da conversa está funcionando.”;
- dispositivos de entrada detectados: 6.

## Live local implementada

- fila limitada e segura para múltiplas plataformas;
- prioridades: pergunta direta, produto, compra e interação social;
- deduplicação por plataforma, usuário e texto;
- descarte controlado quando a fila está cheia;
- moderação de spam e dos bloqueios graves definidos para Luna;
- isolamento de usuário no formato `live.<plataforma>.<usuário>`;
- endpoints de iniciar, parar, receber comentário, consultar estado e processar a próxima mensagem;
- protocolo obs-websocket v5 com autenticação, senha somente por variável local e lista fechada de cenas;
- simulações de 1, 5 e 20 comentários/s e 100 comentários/min.

## Limite desta fase

O OBS Studio 32.0.1 está instalado, mas não estava aberto e a porta 4455 não estava
ativa durante a implementação. Assim, o handshake foi testado com transporte local
simulado e o modo de prévia foi testado pela API real. A conexão com OBS não deve ser
marcada como aprovada até o usuário configurar uma senha WebSocket e criar as cenas
`LUNA_CHAT`, `LUNA_PRODUCT`, `LUNA_BREAK` e `LUNA_STUDIO_RESULT`.
