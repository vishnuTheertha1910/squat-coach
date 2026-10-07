import React, {useEffect,useRef,useState} from 'react';

import {createRoot} from 'react-dom/client';

import Activity from 'lucide-react/dist/esm/icons/activity.js';

import ArrowUpRight from 'lucide-react/dist/esm/icons/arrow-up-right.js';

import Check from 'lucide-react/dist/esm/icons/check.js';

import Download from 'lucide-react/dist/esm/icons/download.js';

import Film from 'lucide-react/dist/esm/icons/film.js';

import History from 'lucide-react/dist/esm/icons/history.js';

import Layers from 'lucide-react/dist/esm/icons/layers.js';

import LoaderCircle from 'lucide-react/dist/esm/icons/loader-circle.js';

import Pause from 'lucide-react/dist/esm/icons/pause.js';

import Play from 'lucide-react/dist/esm/icons/play.js';

import RotateCcw from 'lucide-react/dist/esm/icons/rotate-ccw.js';

import Upload from 'lucide-react/dist/esm/icons/upload.js';

import X from 'lucide-react/dist/esm/icons/x.js';

import Trash2 from 'lucide-react/dist/esm/icons/trash-2.js';

import Info from 'lucide-react/dist/esm/icons/info.js';

import Video from 'lucide-react/dist/esm/icons/video.js';

import {Area,AreaChart,CartesianGrid,ResponsiveContainer,Tooltip,XAxis,YAxis,ReferenceLine} from 'recharts';

import './style.css';

import Pose3D from './Pose3D';



type Landmark={x:number;y:number;visibility:number;world_x?:number;world_y?:number;world_z?:number};

type FeedbackDetail={code:string;label:string;explanation:string;suggestion:string;time_s:number;measured:number|null;threshold:number;affects_verdict:boolean};

type Sample={t:number;phase:string;thigh_angle:number|null;hip_angle:number|null;shin_angle:number|null;landmarks:Landmark[]|null;feedback_codes:string[];validity:string};

type Rep={index:number;start_s:number;bottom_s:number;end_s:number;duration_s:number;descent_s:number;ascent_s:number;min_thigh_angle:number;max_thigh_angle:number;verdict:string;fault_codes:string[];feedback_details?:FeedbackDetail[];review_summary?:string};

type Summary={total:number;correct:number;improper:number;rule_score:number|null;mean_tempo_s:number|null;max_thigh_angle:number|null};

type Session={id:string;status:string;mode:string;source:string;duration_s:number;summary:Summary;reps:Rep[];samples:Sample[];video_url:string|null;error:string|null;width:number;height:number;created_at?:string;metrics?:{valid_frames:number;frames:number;invalid_counts:Record<string,number>}};

const EMPTY:Summary={total:0,correct:0,improper:0,rule_score:null,mean_tempo_s:null,max_thigh_angle:null};

const LINKS=[[11,12],[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],[23,24],[23,25],[25,27],[27,29],[29,31],[24,26],[26,28],[28,30],[30,32]];

const time=(s:number)=>`${Math.floor(s/60).toString().padStart(2,'0')}:${Math.floor(s%60).toString().padStart(2,'0')}`;

const number=(v:number|null|undefined,suffix='')=>v==null?'—':`${Math.round(v*10)/10}${suffix}`;

const words=(v:string)=>v.replaceAll('_',' ').toLowerCase();

const feedback:Record<string,string>={bend_forward:'Lean forward slightly',bend_backward:'Keep your torso more upright',knee_over_toe:'Reduce forward shin inclination',too_deep:'Rise slightly: beyond the configured angle',lower_hips:'Lower your hips into the target range',shallow:'Target depth was not reached',missing_person:'No person detected',no_person:'No person detected',shin_over_toe:'Reduce forward shin inclination',time_gap:'Tracking interrupted',invalid_timestamp:'Timing unavailable',missing_landmarks:'Keep your whole body in frame',unsuitable_view:'Turn side-on to the camera',low_confidence:'Pose landmarks are unclear',gap:'Tracking interrupted'};

function message(code:string){return feedback[code]||words(code)}

async function request<T>(url:string,opts?:RequestInit):Promise<T>{const r=await fetch(url,opts);if(!r.ok){let detail=`Request failed (${r.status})`;try{const j=await r.json();detail=typeof j.detail==='string'?j.detail:detail}catch{}throw Error(detail)}return r.json()}

function sampleAt(samples:Sample[],t:number){let lo=0,hi=samples.length-1,pos=-1;while(lo<=hi){const m=(lo+hi)>>1;if(samples[m].t<=t){pos=m;lo=m+1}else hi=m-1}return pos>=0&&t-samples[pos].t<=.3?samples[pos]:null}

function App(){

 const [tab,setTab]=useState<'review'|'history'>('review'),[mode,setMode]=useState('beginner'),[session,setSession]=useState<Session|null>(null),[history,setHistory]=useState<Session[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState(''),[t,setT]=useState(0),[playing,setPlaying]=useState(false),[overlay,setOverlay]=useState(true),[show3D,setShow3D]=useState(false),[selected,setSelected]=useState<Rep|null>(null),[loop,setLoop]=useState(false),[drag,setDrag]=useState(false),[playbackError,setPlaybackError]=useState(false),[notice,setNotice]=useState(''),[deleteId,setDeleteId]=useState<string|null>(null);

 

 const file=useRef<HTMLInputElement>(null),video=useRef<HTMLVideoElement>(null),canvas=useRef<HTMLCanvasElement>(null),generation=useRef(0),dialog=useRef<HTMLElement>(null);

 const sample=sampleAt(session?.samples||[],t),summary=session?.summary||EMPTY;

 const active=busy||session?.status==='processing';

 useEffect(()=>{if(!deleteId)return;const previous=document.activeElement as HTMLElement|null;function keys(e:KeyboardEvent){if(e.key==='Escape'){setDeleteId(null);return}if(e.key==='Tab'){const nodes=Array.from(dialog.current?.querySelectorAll<HTMLButtonElement>('button')||[]);const first=nodes[0],last=nodes[nodes.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}}document.addEventListener('keydown',keys);return()=>{document.removeEventListener('keydown',keys);previous?.focus()}},[deleteId]);

 async function refresh(){try{setHistory(await request<Session[]>('/api/sessions'))}catch(e){setError((e as Error).message)}}

 useEffect(()=>{refresh()},[]);

 useEffect(()=>{if(!session||session.status!=='processing')return;const token=generation.current;const id=window.setInterval(async()=>{try{const result=await request<Session>(`/api/sessions/${session.id}`);if(generation.current!==token)return;setSession(result);if(result.status!=='processing'){setBusy(false);if(result.status==='failed')setError(result.error||'Analysis failed');else setNotice(`Analysis complete. ${result.summary.total} repetition${result.summary.total===1?'':'s'} recorded.`);refresh()}}catch(e){if(generation.current===token){setError((e as Error).message);setBusy(false)}}},1200);return()=>clearInterval(id)},[session?.id,session?.status]);

 useEffect(()=>{let frame=0;function draw(){const v=video.current,c=canvas.current;if(v&&c){const ctx=c.getContext('2d');if(ctx){const w=c.clientWidth,h=c.clientHeight;c.width=Math.round(w*devicePixelRatio);c.height=Math.round(h*devicePixelRatio);ctx.scale(devicePixelRatio,devicePixelRatio);ctx.clearRect(0,0,w,h);const sm=sampleAt(session?.samples||[],v.currentTime);if(overlay&&sm?.landmarks&&sm.validity==='valid'&&v.videoWidth){const k=Math.min(w/v.videoWidth,h/v.videoHeight),vw=v.videoWidth*k,vh=v.videoHeight*k,ox=(w-vw)/2,oy=(h-vh)/2;ctx.strokeStyle='#ffffff';ctx.lineWidth=2.5;ctx.shadowColor='#1a242d';ctx.shadowBlur=3;for(const [a,b]of LINKS){const p=sm.landmarks[a],q=sm.landmarks[b];if(p&&q&&p.visibility>=.5&&q.visibility>=.5){ctx.beginPath();ctx.moveTo(ox+p.x*vw,oy+p.y*vh);ctx.lineTo(ox+q.x*vw,oy+q.y*vh);ctx.stroke()}}ctx.fillStyle='#ffffff';for(const p of sm.landmarks){if(p.visibility>=.5){ctx.beginPath();ctx.arc(ox+p.x*vw,oy+p.y*vh,3,0,Math.PI*2);ctx.fill()}}}}}frame=requestAnimationFrame(draw)}draw();return()=>cancelAnimationFrame(frame)},[tab,overlay,session]);

 async function upload(f:File){generation.current++;setSession(null);setSelected(null);setPlaying(false);setT(0);setLoop(false);setPlaybackError(false);setError('');setNotice('');setBusy(true);setTab('review');const token=generation.current;const form=new FormData();form.append('file',f);form.append('mode',mode);try{const result=await request<{id:string;status:string}>('/api/sessions',{method:'POST',body:form});const s=await request<Session>(`/api/sessions/${result.id}`);if(token===generation.current){setSession(s);setBusy(s.status==='processing');if(s.status==='failed')setError(s.error||'Analysis failed')}}catch(e){if(token===generation.current){setError((e as Error).message);setBusy(false)}}finally{if(file.current)file.current.value=''}}

 async function open(s:Session){generation.current++;setError('');setPlaybackError(false);setSelected(null);setLoop(false);setT(0);try{const full=await request<Session>(`/api/sessions/${s.id}`);setSession(full);setBusy(full.status==='processing');if(full.status==='failed')setError(full.error||'Analysis failed');setTab('review')}catch(e){setError((e as Error).message)}}

 async function remove(id:string){try{await request(`/api/sessions/${id}`,{method:'DELETE'});if(session?.id===id){generation.current++;setSession(null);setBusy(false)}setDeleteId(null);setNotice('Session and its saved files deleted.');refresh()}catch(e){setError((e as Error).message)}}

 function seek(value:number,clearRep=true){if(clearRep){setSelected(null);setLoop(false)}if(video.current){video.current.currentTime=value;setT(value)}}

 function togglePlayback(){if(playing)video.current?.pause();else{if(selected&&video.current&&video.current.currentTime>=selected.end_s)seek(selected.start_s,false);video.current?.play().catch(()=>setPlaybackError(true))}}
 function replay(rep:Rep){setSelected(rep);seek(rep.start_s,false);video.current?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'});video.current?.play().catch(()=>setPlaybackError(true));setNotice(`Replaying repetition ${rep.index}`)}

 function navigate(next:'review'|'history'){setTab(next);setError('');if(next==='history')refresh()}

 const reviewRep=selected||session?.reps[0];

 const hasWorld=!!session?.samples.some(s=>s.landmarks?.some(p=>p.world_x!=null));

 const validSessions=history.filter(s=>s.status==='completed');

 return <div className="app-shell"><header className="topbar"><a className="brand" href="/" aria-label="FORM home"><span className="brand-icon"><Activity size={19}/></span>FORM<span className="brand-sub">MOVEMENT STUDIO</span></a><nav aria-label="Workspace"><button className={tab==='review'?'nav active':'nav'} onClick={()=>navigate('review')}><Film size={16}/>Review</button><button className={tab==='history'?'nav active':'nav'} onClick={()=>navigate('history')}><History size={16}/>Sessions</button></nav><span className="local-pill"><span/> Local workspace</span></header>

 <main><div className="heading"><div><div className="eyebrow">{tab==='history'?'YOUR MOVEMENT, OVER TIME':'OBSERVE · UNDERSTAND · IMPROVE'}</div><h1>{tab==='history'?'Every session, in perspective.':'A clearer view of your squat.'}</h1><p>{tab==='history'?'Return to your recordings and follow your rule-based results.':'Review your movement, one repetition at a time.'}</p></div>{tab!=='history'&&<div className="mode-control"><label htmlFor="mode">Rule profile</label><select id="mode" value={mode} disabled={!!active} onChange={e=>setMode(e.target.value)}><option value="beginner">Beginner</option><option value="pro">Pro</option></select></div>}</div>

 {error&&<div className="alert" role="alert"><Info size={18}/><span>{error}</span><button className="icon-button" aria-label="Dismiss error" onClick={()=>setError('')}><X size={16}/></button></div>}<div className="sr-only" role="status" aria-live="polite">{notice}</div>

 {tab==='history'?<><section className="progress-panel"><div className="section-heading"><div><span className="eyebrow">PROGRESS</span><h2>Your recent sessions</h2></div><span className="muted">{validSessions.length} completed</span></div>{validSessions.length?<div className="progress-chart"><ResponsiveContainer width="100%" height={180}><AreaChart data={[...validSessions].reverse().map((s,i)=>({name:i+1,score:s.summary?.rule_score}))}><CartesianGrid vertical={false} stroke="#e9ecee"/><XAxis dataKey="name" tickLine={false} axisLine={false}/><YAxis domain={[0,100]} tickLine={false} axisLine={false}/><Tooltip/><Area dataKey="score" name="Rule score" stroke="#596872" fill="#e1e7ea" connectNulls={false}/></AreaChart></ResponsiveContainer></div>:<p className="empty-copy">Your completed sessions will appear here after you analyze a recording.</p>}</section><section className="history-list">{history.map(s=><article className="session-card" key={s.id}><span className="session-icon"><Film size={22}/></span><div className="session-title"><h3>{s.source}</h3><p>{s.mode} · {s.status} · {s.duration_s?time(s.duration_s):'—'}</p></div><div className="session-numbers"><strong>{s.summary?.total??'—'}</strong><span>repetitions</span></div><button onClick={()=>open(s)}>Open <ArrowUpRight size={16}/></button><button className="icon-button" aria-label={`Delete ${s.source}`} onClick={()=>setDeleteId(s.id)}><Trash2 size={17}/></button></article>)}</section></>:<>

 <section className="workspace"><div className="workspace-heading"><div><span className="eyebrow">{'SESSION REVIEW'}</span><h2>{session?.source||'Make room for your movement.'}</h2></div><div className="workspace-actions"><button aria-pressed={show3D} className={show3D?'selected':''} onClick={()=>setShow3D(!show3D)}>3D pose</button><button className={'subtle '+(overlay?'selected':'')} aria-pressed={overlay} onClick={()=>setOverlay(!overlay)}><Layers size={16}/>Skeleton</button>{tab==='review'&&<button onClick={()=>file.current?.click()}><Upload size={16}/>{session?'New recording':'Choose video'}</button>}</div></div>

 <div className="workspace-grid"><div className="video-column"><div className={`video-stage ${drag?'dragging':''} ${session?.video_url?'has-video':''}`} onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={()=>setDrag(false)} onDrop={e=>{e.preventDefault();setDrag(false);if(tab==='review'&&e.dataTransfer.files[0])upload(e.dataTransfer.files[0])}}>

 {session?.video_url?<><video key={session.id} ref={video} src={session.video_url} playsInline preload="auto" onTimeUpdate={e=>{const v=e.currentTarget;if(selected&&v.currentTime>=selected.end_s){if(loop){v.currentTime=selected.start_s}else if(!v.paused){v.pause();v.currentTime=selected.end_s;setT(selected.end_s)}}else setT(v.currentTime)}} onPlay={()=>setPlaying(true)} onPause={()=>setPlaying(false)} onEnded={()=>setPlaying(false)} onError={()=>setPlaybackError(true)} onLoadedData={()=>setPlaybackError(false)}/><canvas ref={canvas} className="skeleton"/><span className="video-stamp">{session.mode} RULES · {time(t)}</span>{playbackError&&<div className="playback-error" role="alert"><Info/><h3>This browser cannot play the recording.</h3><p>Retry playback or download the saved video to open it locally.</p><button onClick={()=>{setPlaybackError(false);video.current?.load()}}><RotateCcw size={16}/>Retry</button><a className="button" href={session.video_url} download>Download video</a></div>}</>:<div className="stage-empty"><span className="stage-icon">{active?<LoaderCircle className="spin" size={32}/>:<Video size={34} strokeWidth={1.25}/>}</span><h3>{active?'Reading your movement…':'Your next session starts here.'}</h3><p>{active?'Pose tracking and repetition rules are running locally.':'Drop a squat recording here, or choose a video to begin.'}</p>{!active&&<button className="primary" onClick={()=>file.current?.click()}><Upload size={17}/>Choose video <ArrowUpRight size={16}/></button>}<span className="stage-note">{active?'Results appear when analysis completes.':'Side view · Full body visible · Good lighting'}</span></div>}

 </div><div className="playback-controls"><button className="play-button" aria-label={playing?'Pause video':'Play video'} disabled={!session?.video_url} onClick={togglePlayback}>{playing?<Pause size={18}/>:<Play size={18}/>}</button><span className="time-label">{time(t)}</span><input aria-label="Video timeline" type="range" min="0" max={session?.duration_s||1} step="0.01" value={t} disabled={!session?.video_url} onChange={e=>seek(+e.target.value)}/><span className="time-label">{time(session?.duration_s||0)}</span><button className={'icon-button '+(loop?'selected':'')} aria-label="Loop selected repetition" aria-pressed={loop} disabled={!selected} onClick={()=>setLoop(!loop)}><RotateCcw size={17}/></button></div><p className="video-caption"><span><Check size={13}/>Processed on your computer</span><span>LearnOpenCV · MediaPipe pose</span></p></div>

 <aside className="inspector"><span className="eyebrow">MOVEMENT INSPECTOR</span><div className="inspector-status"><span className="small-dot"/>{active?'Analyzing':sample?.validity==='valid'?'Tracking movement':sample?message(sample.validity):'Awaiting movement'}</div><div className="phase-display"><span>Current phase</span><strong>{sample?words(sample.phase):'Ready'}</strong><div className="phase-track">{['Standing','Transition','Bottom'].map((p,i)=><span key={p} className={sample?.phase?.toLowerCase().includes(p.toLowerCase())||sample?.phase===`s${i+1}`?'active':''}>{p}</span>)}</div></div><div className="depth-block"><div><span>Thigh inclination</span><strong>{number(sample?.thigh_angle,'°')}</strong></div><div className="depth-track"><span style={{width:`${Math.min(100,(sample?.thigh_angle||0)/95*100)}%`}}/></div><p>Upstream angle · a depth proxy</p></div><span className="eyebrow totals-label">SESSION TOTALS</span><div className="inspector-counts"><div><span className="count-icon"><Check size={16}/></span><strong>{summary.correct}</strong><span>Correct by rules</span></div><div><span className="count-icon"><Info size={16}/></span><strong>{summary.improper}</strong><span>Improper by rules</span></div></div><div className="feedback-box" aria-live="polite"><span className="eyebrow">FEEDBACK</span>{sample?.feedback_codes?.length?sample.feedback_codes.map(c=><p key={c}>{message(c)}</p>):<p>{sample?.validity==='valid'?'Follow a steady, controlled rhythm.':'Rule-triggered cues appear here as you move.'}</p>}</div><p className="inspector-foot">Rule-based feedback, not a medical or expert assessment.</p></aside></div></section>

 {tab==='review'&&session?.metrics&&session.metrics.valid_frames<session.metrics.frames&&<div className="quality-note"><Info size={15}/><span>Tracking available in {Math.round(100*session.metrics.valid_frames/session.metrics.frames)}% of frames. {Object.entries(session.metrics.invalid_counts).filter(([,n])=>n>0).map(([code])=>message(code)).join(' · ')}. Repetitions spanning interruptions are not joined.</span></div>}{show3D&&<Pose3D playing={playing} onTogglePlayback={togglePlayback} hasWorld={hasWorld} getPoints={()=>sampleAt(session?.samples||[],video.current?.currentTime??t)?.landmarks||null}/>}<section className="metrics" aria-label="Session summary"><div className="metric"><span className="eyebrow">REPETITIONS</span><div className="metric-value"><strong>{summary.total}</strong><svg viewBox="0 0 44 44" className="rep-ring" aria-hidden="true"><circle cx="22" cy="22" r="18"/><circle cx="22" cy="22" r="18" pathLength="100" strokeDasharray={`${summary.total?summary.correct/summary.total*100:0} 100`}/></svg></div><p>Completed standing to standing</p></div><div className="metric"><span className="eyebrow">RULE SCORE</span><div className="metric-value"><strong>{number(summary.rule_score)}<small>{summary.rule_score!=null?' / 100':''}</small></strong><svg viewBox="0 0 44 44" className="rep-ring" aria-hidden="true"><circle cx="22" cy="22" r="18"/><circle cx="22" cy="22" r="18" pathLength="100" strokeDasharray={`${summary.rule_score||0} 100`}/></svg></div><p>Correct ÷ completed repetitions</p></div><div className="metric"><span className="eyebrow">AVERAGE TEMPO</span><div className="metric-value"><strong>{number(summary.mean_tempo_s)}<small>{summary.mean_tempo_s!=null?' sec':''}</small></strong></div><p>Time per completed repetition</p></div><div className="metric"><span className="eyebrow">MAX INCLINATION</span><div className="metric-value"><strong>{number(summary.max_thigh_angle,'°')}</strong></div><p>Thigh to upward vertical</p></div></section>

 {tab==='review'&&session?.status==='completed'&&<div className="details-grid"><section className="chart-panel"><div className="section-heading"><div><span className="eyebrow">THE SHAPE OF YOUR SESSION</span><h2>Movement over time</h2></div><span className="chart-unit">THIGH INCLINATION / °</span></div><ResponsiveContainer width="100%" height={210}><AreaChart data={session.samples.filter((_,i)=>i%Math.max(1,Math.floor(session.samples.length/800))===0).map(s=>({t:s.t,angle:s.validity==='valid'?s.thigh_angle:null}))} onClick={(e:any)=>{if(e?.activeLabel!=null)seek(+e.activeLabel)}}><CartesianGrid stroke="#edf0f1" vertical={false}/><XAxis dataKey="t" type="number" domain={[0,session.duration_s]} tickFormatter={time} minTickGap={45} tickLine={false} axisLine={false}/><YAxis domain={[0,110]} width={32} tickLine={false} axisLine={false}/><Tooltip labelFormatter={v=>time(Number(v))} formatter={v=>[`${v}°`,'Thigh inclination']}/><ReferenceLine x={t} stroke="#8c9da8" strokeDasharray="3 3"/><Area type="linear" dataKey="angle" stroke="#62737e" strokeWidth={2} fill="#e6ebee" connectNulls={false}/></AreaChart></ResponsiveContainer><p className="chart-help">Select a point to seek the recording. Gaps indicate unavailable tracking.</p></section><section className="report-panel"><span className="eyebrow">TAKE YOUR SESSION WITH YOU</span><h2>A record of your movement.</h2><p>Keep repetition timings, rule verdicts, and measured angles in a portable report.</p><a className="button primary" href={`/api/sessions/${session.id}/report.pdf`} download><Download size={16}/>PDF report</a><a className="button" href={`/api/sessions/${session.id}/report.csv`} download><Download size={16}/>CSV data</a><span className="report-note">Reports contain the same saved session results.</span></section></div>}

 {tab==='review'&&session?.status==='completed'&&reviewRep&&<section className="rep-feedback-panel"><div className="section-heading"><div><span className="eyebrow">MEASUREMENTS INTO CONTEXT</span><h2>Repetition {reviewRep.index}: what the rules observed</h2></div><span className={'verdict '+(reviewRep.verdict==='correct'?'correct':'')}>{words(reviewRep.verdict)}</span></div><div className="rep-selector" aria-label="Select repetition for detailed feedback">{session.reps.map(r=><button key={r.index} aria-pressed={reviewRep.index===r.index} onClick={()=>{setSelected(r);seek(r.bottom_s,false);video.current?.pause()}}>Rep {r.index}</button>)}</div><p className="review-summary">{reviewRep.review_summary||(reviewRep.verdict==='correct'?'No failing upstream rule was triggered in this completed repetition.':'This repetition triggered the fault codes in its table row.')}</p><div className="feedback-measurements"><span>Depth proxy <strong>{number(reviewRep.max_thigh_angle,'°')}</strong></span><span>Down / up <strong>{number(reviewRep.descent_s,'s')} / {number(reviewRep.ascent_s,'s')}</strong></span><span>Target band <strong>{session.mode==='pro'?'80–95°':'70–95°'}</strong></span></div>{reviewRep.feedback_details?.length?reviewRep.feedback_details.map((detail,i)=><article className="feedback-detail" key={detail.code+i}><div><span className="eyebrow">{detail.affects_verdict?'FAILING RULE':'ADVISORY CUE'}</span><h3>{detail.label}</h3><p>{detail.explanation}</p><p className="suggestion">{detail.suggestion}</p></div><button onClick={()=>{seek(detail.time_s,false);video.current?.pause();video.current?.scrollIntoView({behavior:'smooth',block:'center'})}}>View moment · {time(detail.time_s)}</button></article>):<p className="feedback-empty">{reviewRep.verdict==='correct'?'The configured bottom range and return sequence were completed without a failing rule. This does not certify overall form.':reviewRep.fault_codes.map(message).join(' · ')}{!reviewRep.feedback_details?' Older sessions need a new upload for measured cue details.':''}</p>}<p className="chart-help">Feedback explains the saved rule evidence. It does not assess pain, injury risk, balance, or faults not measured by this side-view pipeline.</p></section>}

 {tab==='review'&&session?.status==='completed'&&<section className="rep-panel"><div className="section-heading"><div><span className="eyebrow">LOOK A LITTLE CLOSER</span><h2>Every repetition has a story.</h2></div><span className="muted">Select to replay</span></div>{!session.reps.length?<p className="empty-copy">No completed repetitions were counted. Check the side view, full-body visibility, and tracking cues.</p>:<div className="table-scroll" tabIndex={0} aria-label="Scrollable repetition details"><table><thead><tr><th>Rep</th><th>Rule verdict</th><th>Time</th><th>Down / up</th><th>Max angle</th><th>Rule faults</th><th><span className="sr-only">Replay</span></th></tr></thead><tbody>{session.reps.map(rep=><tr key={rep.index} className={selected?.index===rep.index?'selected-row':''}><td><span className="rep-number">{String(rep.index).padStart(2,'0')}</span></td><td><span className={'verdict '+(rep.verdict==='correct'?'correct':'')}><span/>{words(rep.verdict)}</span></td><td>{time(rep.start_s)} – {time(rep.end_s)}</td><td>{number(rep.descent_s,'s')} / {number(rep.ascent_s,'s')}</td><td>{number(rep.max_thigh_angle,'°')}</td><td className="fault-cell">{rep.fault_codes.length?rep.fault_codes.map(message).join(' · '):'No failing rule triggered'}</td><td><button className="icon-button" aria-label={`Replay repetition ${rep.index}`} onClick={()=>replay(rep)}><Play size={17}/></button></td></tr>)}</tbody></table></div>}</section>}

 </>}

 <footer><span>FORM <span className="footer-dot">/</span> Move with a little more awareness.</span><span>Explicit rules. Visible measurements. Local processing.</span></footer></main><input ref={file} type="file" accept="video/*,.avi,.mkv,.mov" className="sr-only" aria-label="Choose squat recording" onChange={e=>{if(e.target.files?.[0])upload(e.target.files[0])}}/>

 {deleteId&&<div className="modal-backdrop"><section ref={dialog} role="dialog" aria-modal="true" aria-labelledby="delete-title" className="modal"><h2 id="delete-title">Delete this session?</h2><p>This removes the saved analysis and app-owned recording files from this computer.</p><div><button autoFocus onClick={()=>setDeleteId(null)}>Keep session</button><button className="primary" onClick={()=>remove(deleteId)}>Delete session</button></div></section></div>}

 </div>

}

createRoot(document.getElementById('root')!).render(<App/>);

