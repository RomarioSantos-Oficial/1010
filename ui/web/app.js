const messages=document.querySelector('#messages'),form=document.querySelector('#form'),input=document.querySelector('#input');
const mic=document.querySelector('#mic'),voiceEnabled=document.querySelector('#voice-enabled'),avatar=document.querySelector('#avatar');
const userId=localStorage.lunaUserId||(localStorage.lunaUserId=`local_${crypto.randomUUID().slice(0,8)}`);
let health={},recorder=null,recordChunks=[],recordTimer=null,currentEmotion='neutral',isSpeaking=false;
voiceEnabled.checked=localStorage.getItem('lunaVoiceEnabled')==='true';
voiceEnabled.addEventListener('change',()=>localStorage.setItem('lunaVoiceEnabled',String(voiceEnabled.checked)));

function bubble(text,kind){const el=document.createElement('article');el.className=kind;el.textContent=text;messages.append(el);messages.scrollTop=messages.scrollHeight;return el}
function visualForEmotion(emotion){return emotion==='happy'?'happy':'neutral'}
function setAvatar(state){avatar.dataset.state=state}
function restoreAvatar(){setAvatar(visualForEmotion(currentEmotion))}

async function loadHealth(){
  try{
    health=await fetch('/health').then(r=>r.json());
    document.querySelector('#status').textContent=health.model_ready?'Modelo local ativo':'Modo demonstração';
    document.querySelector('#provider').textContent=`Motor: ${health.llm_provider}`;
    document.querySelector('#stt-status').textContent=`STT · ${health.stt==='ok'?'ativo':'offline'}`;
    document.querySelector('#tts-status').textContent=`Voz feminina · ${health.tts==='ok'?'disponível':'offline'}`;
    document.querySelector('#avatar-status').textContent=`Avatar · ${health.avatar==='ok'?'ativo':'offline'}`;
    mic.disabled=health.stt!=='ok'||!navigator.mediaDevices?.getUserMedia;
    voiceEnabled.disabled=health.tts!=='ok';
    if(health.tts!=='ok')voiceEnabled.checked=false;
  }catch{
    document.querySelector('#status').textContent='Servidor indisponível';mic.disabled=true;voiceEnabled.disabled=true;
  }
}

async function speak(text){
  if(!voiceEnabled.checked||health.tts!=='ok')return;
  try{
    isSpeaking=true;mic.disabled=true;setAvatar('speaking');
    const response=await fetch('/speech/synthesize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});
    if(!response.ok)throw new Error('síntese indisponível');
    const url=URL.createObjectURL(await response.blob()),audio=new Audio(url);
    await new Promise((resolve,reject)=>{audio.onended=resolve;audio.onerror=reject;audio.play().catch(reject)});
    URL.revokeObjectURL(url);
  }catch(error){document.querySelector('#voice-hint').textContent=`Voz: ${error.message}. A resposta em texto continua disponível.`}
  finally{isSpeaking=false;mic.disabled=health.stt!=='ok';restoreAvatar()}
}

async function sendMessage(text){
  bubble(text,'user');input.value='';const wait=bubble('Pensando…','assistant thinking');input.disabled=true;mic.disabled=true;
  try{
    const response=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:userId,text})});
    const data=await response.json();if(!response.ok)throw new Error(data.detail||'Erro');
    wait.textContent=data.spoken_text;wait.classList.remove('thinking');currentEmotion=data.emotion||'neutral';restoreAvatar();
    await speak(data.spoken_text);
  }catch(error){wait.textContent=`Não consegui responder: ${error.message}`;wait.classList.remove('thinking');currentEmotion='neutral';restoreAvatar()}
  finally{input.disabled=false;if(!isSpeaking)mic.disabled=health.stt!=='ok';input.focus()}
}

form.addEventListener('submit',async event=>{event.preventDefault();const text=input.value.trim();if(text)await sendMessage(text)});
input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();form.requestSubmit()}});

async function stopRecording(){clearTimeout(recordTimer);if(recorder&&recorder.state!=='inactive')recorder.stop()}

mic.addEventListener('click',async()=>{
  if(isSpeaking)return;
  if(recorder&&recorder.state==='recording'){await stopRecording();return}
  try{
    const stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true}});
    recordChunks=[];recorder=new MediaRecorder(stream);
    recorder.ondataavailable=event=>{if(event.data.size)recordChunks.push(event.data)};
    recorder.onstop=async()=>{
      stream.getTracks().forEach(track=>track.stop());mic.classList.remove('recording');mic.textContent='🎙';mic.disabled=true;
      const waiting=bubble('Transcrevendo áudio local…','assistant thinking');
      try{
        const audio=new Blob(recordChunks,{type:recorder.mimeType||'audio/webm'}),body=new FormData();body.append('audio',audio,'fala.webm');
        const response=await fetch('/speech/transcribe',{method:'POST',body});const data=await response.json();
        if(!response.ok)throw new Error(data.detail||'Falha na transcrição');waiting.remove();
        if(!data.text)throw new Error('Não detectei fala. Tente novamente mais perto do microfone.');
        await sendMessage(data.text);
      }catch(error){waiting.textContent=error.message;waiting.classList.remove('thinking');mic.disabled=health.stt!=='ok'}
    };
    recorder.start();mic.classList.add('recording');mic.textContent='■';document.querySelector('#voice-hint').textContent='Gravando… clique novamente para enviar.';
    recordTimer=setTimeout(stopRecording,15000);
  }catch(error){bubble(`Microfone indisponível: ${error.message}`,'assistant')}
});

setInterval(()=>{if(!isSpeaking&&avatar.dataset.state!=='speaking'){const previous=avatar.dataset.state;setAvatar('blink');setTimeout(()=>setAvatar(previous),150)}},4200);
document.querySelector('#forget').addEventListener('click',async()=>{if(!confirm('Apagar todo o histórico e as preferências desta identidade local?'))return;await fetch(`/memory/${userId}`,{method:'DELETE'});messages.replaceChildren();bubble('Memória apagada. Podemos recomeçar.','assistant')});
document.querySelector('#adult-verify').addEventListener('click',async event=>{
  if(!confirm('Confirma que você tem 18 anos ou mais?'))return;
  const response=await fetch('/adult/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:userId,confirmed_adult:true})});
  if(response.ok){event.target.textContent='Acesso 18+ confirmado';event.target.disabled=true;bubble('Confirmação 18+ registrada somente nesta sessão local.','assistant')}
});
loadHealth();
