"use client";
import { Activity, Archive, BrainCircuit, Clock, GitBranch, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { demoProject, request } from "../lib/api";

export default function Overview() {
  const [data,setData]=useState({active_memories:0,superseded_memories:0,events:0,sessions:0,memory_types:{} as Record<string,number>});
  const [error,setError]=useState("");
  useEffect(()=>{demoProject().then(p=>request<typeof data>(`/api/projects/${p.id}/dashboard`)).then(setData).catch(e=>setError(e.message))},[]);
  const metrics = [["Active memories", String(data.active_memories), BrainCircuit], ["Superseded", String(data.superseded_memories), GitBranch], ["Evidence events", String(data.events), Archive], ["Sessions", String(data.sessions), Clock]] as const;
  const types=Object.entries(data.memory_types);
  return <div className="page">
    <div className="topline"><div><h1>Engineering memory, at a glance</h1><p className="subtle">Acme Commerce API · durable knowledge health and recent activity</p>{error&&<p style={{color:"#f07878"}}>{error}</p>}</div><span className="badge active">● API connected</span></div>
    <div className="grid4">{metrics.map(([label,value,Icon])=><div className="card metric" key={label}><Icon size={18} color="#67d6b3"/><strong>{value}</strong><span>{label}</span></div>)}</div>
    <div className="section twoCol"><div className="card"><div className="sectionTitle"><h2>Memory composition</h2><span className="badge">{types.reduce((n,[,v])=>n+v,0)} total</span></div>{types.map(([n,c])=><div className="barRow" key={n}><span>{n.replaceAll("_"," ")}</span><div className="bar"><i style={{width:`${Math.min(100,c*20)}%`}}/></div><b>{c}</b></div>)}</div><div className="card"><div className="sectionTitle"><h2>Recent memory activity</h2><Activity size={17}/></div><div className="event"><span className="eventIcon"><ShieldCheck size={16}/></span><div><strong>Serializable token rotation recorded</strong><p>Successful fix · confidence 98%</p></div></div><div className="event"><span className="eventIcon"><GitBranch size={16}/></span><div><strong>Session storage superseded</strong><p>Historical record retained</p></div></div><div className="event"><span className="eventIcon"><Archive size={16}/></span><div><strong>Evidence archive adapter ready</strong><p>Local in mock mode · S3 in live mode</p></div></div></div></div>
    <div className="section card"><div className="sectionTitle"><h2>Memory health</h2><span className="badge active">Governed</span></div><p className="subtle">{data.active_memories} active memories are available for grounded answers. Superseded and disputed records remain visible for audit while status-aware retrieval reduces their influence.</p></div>
  </div>
}
