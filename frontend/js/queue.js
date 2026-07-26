async function loadQueue(){try{const q=await API.get('queue');paintQueue(q)}catch{document.querySelector('#queueAdvice').textContent='Live data is reconnecting. Please refresh in a moment.'}}
function paintQueue(q){
  crowd.textContent=q.crowd_density||'Not published';
  wait.textContent=q.wait_minutes==null?'—':`${Math.floor(q.wait_minutes/60)}h ${q.wait_minutes%60}m`;
  people.textContent=q.people_count==null?'—':q.people_count.toLocaleString();
  prediction.textContent=q.balance_tickets?`Official SSD tickets: ${q.balance_tickets.count.toLocaleString()} (${q.balance_tickets.date})`:'Official public status';
  queueAdvice.textContent=q.slot?`Official TTD update — Running Slot: ${q.slot}. Queue wait time is not publicly published. Source: tirumala.org.`:q.message||'Queue wait time is not publicly published by TTD.';
}
document.querySelector('#refresh').onclick=loadQueue;loadQueue();
