(() => {
  'use strict';
  const CGE_CORE_TARGET_VERSION = '0.7.0';
  const $ = id => document.getElementById(id);

  const MODELS = {
    simple: {
      title: 'Simple CGE', subtitle: 'Hosoe closed economy',
      description: 'Two goods, primary factors and one representative household. No government, foreign trade or intermediate-input network.',
      facts: ['static', 'closed economy', 'factor markets'],
      useWhen: 'Learning general-equilibrium mechanics or studying an economy-wide factor-endowment shock in the smallest complete model.',
      avoidWhen: 'The question requires tariffs, trade, government, intermediate inputs or dynamic adjustment.',
      outputs: [['Z[i]','sector output'],['F[h,i]','factor allocation'],['pf[h]','factor prices'],['X[i]','household demand'],['objective','household utility']],
      editor: 'factor'
    },
    standard: {
      title: 'Standard CGE', subtitle: 'Hosoe open economy',
      description: 'Production with intermediates, households, government, taxes, Armington imports, CET exports, saving and investment.',
      facts: ['static', 'intermediate inputs', 'government', 'trade'],
      useWhen: 'Sectoral tariff/production-tax reform, world-price shocks, factor-endowment shocks and questions where trade and input-output linkages matter.',
      avoidWhen: 'The question requires demographic cohorts, detailed household distribution, debt dynamics or a financial sector.',
      outputs: [['Z[i]','gross sector output'],['M[i], E[i]','imports and exports'],['pq[i]','composite price'],['F[h,i]','factor demand'],['Tm[i], Tz[i]','tax revenue'],['Xp[i]','household consumption']],
      editor: 'standard'
    },
    camcge: {
      title: 'CAMCGE', subtitle: 'Cameroon 1987 replication',
      description: 'The published multisector Cameroon model retained as an independent historical replication and regression benchmark.',
      facts: ['11 sectors', '3 labor groups', 'published experiments'],
      useWhen: 'Re-running the published Cameroon benchmark or its documented experiments and checking independent replication behavior.',
      avoidWhen: 'You want a generic new-country template without intentionally adapting the published equations and closure.',
      outputs: [['xd[i]','sector output'],['pd[i], p[i]','domestic/composite prices'],['e[i], mq[i]','trade'],['wa[lc]','labor prices'],['dk[i]','investment']],
      editor: 'cam'
    },
    ifpri: {
      title: 'IFPRI Standard', subtitle: 'public synthetic lane',
      description: 'Richer activities, commodities, factors and institutions with explicit macro-closure scenarios. The public Control Room uses the redistributable synthetic economy.',
      facts: ['explicit macro closure', 'named scenarios', 'clean-room public data'],
      useWhen: 'The macro/fiscal/external closure is part of the policy question or you want the documented IFPRI scenario system.',
      avoidWhen: 'You need to claim official benchmark replication without separately supplied official source material.',
      outputs: [['QA, QX','activity/commodity production'],['QM, QE','imports and exports'],['CPI, DPI, EXR','price system'],['GSAV, FSAV','macro balances'],['institutional incomes','distribution across institutions']],
      editor: 'ifpri'
    }
  };

  let current = 'standard';
  const state = { shock:'tariff', good:'BRD', factor:'CAP', level:'0', change:'-0.5', cam:'500', ifpri:'TARCUT1' };

  function card(id, model){
    const b=document.createElement('button'); b.className='model-card'; b.dataset.model=id;
    b.innerHTML=`<b>${model.title}</b><span>${model.subtitle}</span>`;
    b.addEventListener('click',()=>{current=id; render();}); return b;
  }

  function renderCards(){
    const root=$('model-cards'); root.innerHTML='';
    Object.entries(MODELS).forEach(([id,m])=>{const el=card(id,m); if(id===current)el.classList.add('active'); root.appendChild(el);});
  }

  function renderInfo(){
    const m=MODELS[current]; $('model-title').textContent=m.title; $('model-description').textContent=m.description;
    $('use-when').textContent=m.useWhen; $('avoid-when').textContent=m.avoidWhen;
    $('facts').innerHTML=m.facts.map(x=>`<span class="chip">${x}</span>`).join('');
    $('outputs').innerHTML=m.outputs.map(([a,b])=>`<div class="output"><b>${a}</b><span>${b}</span></div>`).join('');
  }

  const field=(label,html)=>`<div class="field"><label>${label}</label>${html}</div>`;
  function renderEditor(){
    const m=MODELS[current]; let html='';
    if(m.editor==='standard'){
      html += field('Shock', `<select id="shock"><option value="tariff">Import tariff</option><option value="production_tax">Production tax</option><option value="endowment">Factor endowment</option></select>`);
      html += `<div id="standard-fields"></div><div class="quick"><button data-q="tariff0">Abolish BRD tariff</button><button data-q="tariff50">Cut BRD tariff 50%</button><button data-q="capital10">Capital +10%</button></div>`;
    } else if(m.editor==='factor') {
      html += field('Factor', `<select id="factor"><option>LAB</option><option selected>CAP</option></select>`);
      html += field('Proportional change', `<input id="factor-change" type="number" step="0.01" value="0.10">`);
    } else if(m.editor==='cam') {
      html += `<p class="muted">Experiment-style foreign-saving shock.</p>` + field('New fsav level', `<input id="cam-level" type="number" value="500">`);
    } else {
      html += field('Named scenario', `<select id="ifpri-scenario"><option>TARCUT1</option><option>TARCUT2</option><option>FSAVINCR</option><option>PWMINCR</option><option>DEVAL</option></select>`);
      html += `<p class="muted">The public path uses <code>IFPRICGE.synthetic()</code>. Official-source replication remains a separate evidence lane.</p>`;
    }
    $('scenario-editor').innerHTML=html;
    bindEditor();
  }

  function standardFields(){
    const shock=$('shock').value; state.shock=shock; let html='';
    if(shock==='endowment'){
      html += field('Factor', `<select id="factor"><option>LAB</option><option>CAP</option></select>`);
      html += field('Proportional change', `<input id="change" type="number" step="0.01" value="0.10">`);
    } else {
      html += field('Good / sector', `<select id="good"><option>BRD</option><option>MLK</option></select>`);
      html += field('Mode', `<select id="mode"><option value="level">Set new rate</option><option value="change">Proportional change</option></select>`);
      html += `<div id="mode-field"></div>`;
    }
    $('standard-fields').innerHTML=html; bindStandardSubfields();
  }
  function modeField(){
    if(!$('mode-field'))return; const mode=$('mode').value;
    $('mode-field').innerHTML = mode==='level' ? field('New rate (decimal)', `<input id="level" type="number" step="0.01" value="0">`) : field('Proportional change', `<input id="change" type="number" step="0.01" value="-0.50">`);
    $('mode-field').querySelectorAll('input').forEach(x=>x.addEventListener('input',renderCode));
  }
  function bindStandardSubfields(){
    if($('mode')){$('mode').addEventListener('change',()=>{modeField();renderCode();}); modeField();}
    ['good','factor','change','level'].forEach(id=>{const x=$(id); if(x)x.addEventListener('input',renderCode); if(x)x.addEventListener('change',renderCode);});
  }
  function bindEditor(){
    if($('shock')){$('shock').value=state.shock; $('shock').addEventListener('change',()=>{standardFields();renderCode();}); standardFields();}
    ['factor','factor-change','cam-level','ifpri-scenario'].forEach(id=>{const x=$(id); if(x){x.addEventListener('input',renderCode);x.addEventListener('change',renderCode);}});
    document.querySelectorAll('[data-q]').forEach(b=>b.addEventListener('click',()=>quick(b.dataset.q)));
  }
  function quick(q){
    if(q==='tariff0'){ $('shock').value='tariff'; standardFields(); $('good').value='BRD'; $('mode').value='level'; modeField(); $('level').value='0'; }
    if(q==='tariff50'){ $('shock').value='tariff'; standardFields(); $('good').value='BRD'; $('mode').value='change'; modeField(); $('change').value='-0.50'; }
    if(q==='capital10'){ $('shock').value='endowment'; standardFields(); $('factor').value='CAP'; $('change').value='0.10'; }
    renderCode();
  }

  function codeForCurrent(){
    if(current==='simple'){
      const f=$('factor')?.value||'CAP', ch=$('factor-change')?.value||'0.10';
      return `from cge_core import SimpleCGE\n\nbase = SimpleCGE.example().solve()\nscenario = base.scenario("Factor endowment shock")\nscenario.endowment("${f}", change=${ch})\nresult = scenario.solve()\nresult.compare(base)`;
    }
    if(current==='camcge'){
      const v=$('cam-level')?.value||'500';
      return `from cge_core import CamCGE\n\nbase = CamCGE.example().solve()\nscenario = base.scenario("Foreign saving shock")\nscenario.set("fsav", None, ${v})\nresult = scenario.solve()\nresult.compare(base)`;
    }
    if(current==='ifpri'){
      const s=$('ifpri-scenario')?.value||'TARCUT1';
      return `from cge_core import IFPRICGE\n\nbase = IFPRICGE.synthetic().solve()\nresult = base.scenario("${s}").solve()\nresult.compare(base)`;
    }
    const shock=$('shock')?.value||'tariff';
    if(shock==='endowment'){
      const f=$('factor')?.value||'CAP', ch=$('change')?.value||'0.10';
      return `from cge_core import StandardCGE\n\nbase = StandardCGE.example().solve()\nscenario = base.scenario("Factor endowment shock")\nscenario.endowment("${f}", change=${ch})\nresult = scenario.solve()\nresult.compare(base)`;
    }
    const g=$('good')?.value||'BRD', mode=$('mode')?.value||'level';
    const method=shock==='tariff'?'tariff':'production_tax';
    const title=shock==='tariff'?'Tariff reform':'Production-tax reform';
    const arg=mode==='level' ? ($('level')?.value||'0') : `change=${$('change')?.value||'-0.50'}`;
    return `from cge_core import StandardCGE\n\nbase = StandardCGE.example().solve()\nscenario = base.scenario("${title}")\nscenario.${method}("${g}", ${arg})\nresult = scenario.solve()\nresult.compare(base)`;
  }

  function renderCode(){ $('code').textContent=codeForCurrent(); }
  function render(){ renderCards(); renderInfo(); renderEditor(); renderCode(); }
  $('copy-code').addEventListener('click', async()=>{try{await navigator.clipboard.writeText($('code').textContent);$('copy-code').textContent='Copied';setTimeout(()=>$('copy-code').textContent='Copy',1000);}catch(e){}});
  render();
})();
