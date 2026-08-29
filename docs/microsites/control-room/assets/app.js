(() => {
  'use strict';

  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[ch]));

  const CGE_CORE_TARGET_VERSION = '0.7.0';
  const INSTALL = 'pip install "cge-core @ https://github.com/miraflor/CGE-core/archive/refs/tags/v0.7.0.zip"';
  const MODEL_ORDER = ['simple','standard','ifpri','camcge'];

  const MODELS = {
    simple: {
      title:'Simple CGE',
      badge:'Hosoe teaching model',
      card:'Closed economy · household + firms + factors',
      description:'The smallest bundled CGE economy. A representative household owns primary factors, firms hire those factors to produce goods, and relative prices adjust until goods and factor markets clear. There is no government, foreign trade, or intermediate-input network.',
      useWhen:'Use it to learn general-equilibrium mechanics or isolate a factor-endowment shock.',
      avoidWhen:'Do not use it for tariffs, government, imports/exports, or input-output propagation.',
      facts:['Static equilibrium','Closed economy','No government','No trade'],
      labels:{goods:['BRD','MLK'],factors:['CAP','LAB']},
      dataChoices:[
        ['example','Bundled example','Use the packaged Hosoe teaching economy.'],
        ['directory','Prepared data directory','Use a CGE-Core-format Simple CGE data directory.']
      ],
      closure:{
        title:'Canonical Simple CGE closure',
        anchor:'The bundled model fixes its price anchor and removes the corresponding redundant equilibrium condition.',
        adjusts:'Relative goods prices, factor returns, production, factor allocation, consumption, and welfare adjust endogenously.',
        note:'v0.7 applies this canonical closure automatically. Ordinary users do not choose the numeraire or Walras equation.'
      },
      glossary:[
        ['Z[i]','Production','Gross output of good/sector i.'],
        ['X[i]','Consumption','Representative-household demand for good i.'],
        ['F[h,i]','Factor demand','Use of factor h by sector i.'],
        ['pf[h]','Factor price','Wage or return to the primary factor.'],
        ['px[i], pz[i]','Goods prices','Relative prices coordinating demand and production.'],
        ['FF[h]','Factor endowment','Exogenous economy-wide supply of a primary factor.']
      ],
      story:[
        'The benchmark says how much labor and capital the household owns and how firms use them.',
        'A factor-endowment shock changes the quantity of one primary factor available to the whole economy.',
        'Its factor price adjusts, firms reallocate factors, and sector outputs change.',
        'Household income and relative goods prices change, so consumption changes too.',
        'The new solution is the set of prices and quantities that clears all modeled markets together.'
      ],
      controls:[
        {id:'endowment',name:'Factor endowment',symbol:'FF[h]',target:'factor',kind:'semantic',
         method:'endowment',description:'Change the economy-wide supply of LAB or CAP.',
         meaning:'Ask how the equilibrium changes if more or less of a primary factor is available.',
         watch:'Factor returns, sectoral factor allocation, output, consumption, welfare.',
         caution:'This is an endowment/full-employment counterfactual, not a mechanical jobs-created calculation.'}
      ],
      quick:[
        {label:'+10% labor',control:'endowment',target:'LAB',op:'pct',amount:10},
        {label:'−10% labor',control:'endowment',target:'LAB',op:'pct',amount:-10},
        {label:'+10% capital',control:'endowment',target:'CAP',op:'pct',amount:10}
      ],
      outputs:[
        ['Consumption','X[i]: household demand after income and relative prices adjust.'],
        ['Production','Z[i]: which sectors expand or contract.'],
        ['Factor demand','F[h,i]: reallocation of labor/capital across sectors.'],
        ['Factor prices','pf[h]: wages/returns and incidence.'],
        ['Goods prices','px[i], pz[i]: relative price adjustment.'],
        ['Welfare','Objective/utility and benchmark comparison.']
      ]
    },

    standard: {
      title:'Standard CGE',
      badge:'Hosoe open-economy model',
      card:'Intermediates · government · trade · investment',
      description:'The generic open-economy teaching model. Sectors use primary factors and intermediate inputs; households consume and save; government taxes and purchases goods; saving finances investment; Armington aggregation combines domestic and imported supply; CET transformation allocates output between domestic and export markets.',
      useWhen:'Use it for tariff/tax reform, factor-supply shocks, world-price shocks, and sectoral general-equilibrium propagation.',
      avoidWhen:'It is static and representative-household. It is not a year-by-year debt, demographic-cohort, or financial-sector model.',
      facts:['Static equilibrium','Intermediate inputs','Government','Armington + CET'],
      labels:{goods:['BRD','MLK'],factors:['CAP','LAB']},
      dataChoices:[
        ['example','Bundled example','Use the packaged Hosoe Standard CGE economy.'],
        ['sam','SAM CSV','Build the Standard CGE from one balanced social accounting matrix.'],
        ['directory','Prepared data directory','Use an already prepared CGE-Core dataset.']
      ],
      closure:{
        title:'Canonical Standard CGE closure',
        anchor:'The bundled Standard CGE uses its model-owned price anchor and independent equilibrium conditions.',
        adjusts:'Domestic/import/export prices, the exchange rate, production, trade, factor allocation, household demand, government revenue, saving and investment adjust together.',
        note:'v0.7 applies the canonical closure automatically. Closure remains economically important; it is simply no longer routine user-interface plumbing.'
      },
      glossary:[
        ['Z[i], Y[i]','Output / value added','Sector gross output and value added.'],
        ['X[i,j]','Intermediate use','Input-output demand for commodity i by sector j.'],
        ['F[h,i]','Factor demand','Labor/capital allocation across sectors.'],
        ['Xp[i]','Household demand','Private consumption by good.'],
        ['Xg[i]','Government demand','Model-consistent public purchases by good.'],
        ['Xv[i]','Investment demand','Demand for investment goods financed by saving.'],
        ['M[i], E[i]','Imports / exports','External trade quantities.'],
        ['D[i], Q[i]','Domestic / composite supply','Domestic sales and Armington composite supply.'],
        ['pq, pm, pe, pd, pz','Price system','Composite, import, export, domestic and output prices.'],
        ['epsilon','Exchange rate','Domestic-currency price of foreign exchange.'],
        ['taum[i], tauz[i]','Policy rates','Import tariff and production/indirect tax rates.'],
        ['Sf','Foreign saving','External financing term under this closure.']
      ],
      story:[
        'The SAM and calibration establish a benchmark in which production, institutions, trade, and all markets are mutually consistent.',
        'A policy shock first changes one exogenous rate, price, or endowment.',
        'Firms and users respond to changed relative prices through production, intermediate demand, Armington substitution, and CET transformation.',
        'Factor returns, household income, government revenue, saving, investment, imports, exports, and the exchange rate move together.',
        'The counterfactual is complete only when the entire system again satisfies its equilibrium conditions.'
      ],
      controls:[
        {id:'tariff',name:'Import tariff',symbol:'taum[i]',target:'good',kind:'semantic',method:'tariff',
         description:'Set or proportionally change the import tariff on one good.',
         meaning:'Changes the border tax entering the tariff-inclusive import price.',
         watch:'Imports M, domestic supply D, composite price pq, output Z, tariff revenue, welfare.',
         caution:'A 50% cut to a 10% tariff gives 5%; it does not subtract 50 percentage points.'},
        {id:'production_tax',name:'Production tax',symbol:'tauz[i]',target:'good',kind:'semantic',method:'production_tax',
         description:'Set or proportionally change the production/indirect tax rate on one sector.',
         meaning:'Changes the tax on sector gross output; it is not a household income tax.',
         watch:'Producer price, output, intermediate demand, factor use, government revenue.',
         caution:'Rates are decimals in model code: 0.05 means 5%.'},
        {id:'endowment',name:'Factor endowment',symbol:'FF[h]',target:'factor',kind:'semantic',method:'endowment',
         description:'Change the economy-wide supply of a primary factor.',
         meaning:'Asks what equilibrium absorbs a larger or smaller factor endowment.',
         watch:'Factor price, sectoral factor demand, output, household income, trade, welfare.',
         caution:'Full-employment closure means the factor price and allocation adjust to absorb the endowment.'},
        {id:'foreign_saving',name:'Foreign saving',symbol:'Sf',target:'scalar',kind:'component',component:'Sf',
         description:'Change the exogenous foreign-saving/resource-balance term.',
         meaning:'Changes external financing available to the economy under the savings-driven investment closure.',
         watch:'Investment, exchange rate, imports, exports, absorption, output.',
         caution:'Do not automatically label this FDI; it is an aggregate external-balance term.'},
        {id:'world_import_price',name:'World import price',symbol:'pWm[i]',target:'good',kind:'component',component:'pWm',
         description:'Change the exogenous foreign-currency import price of one good.',
         meaning:'Represents an external price shock under the small-country assumption.',
         watch:'pm, M, D, pq, sector costs, household demand, exchange rate.',
         caution:'This is a world price, not a domestic tax.'},
        {id:'world_export_price',name:'World export price',symbol:'pWe[i]',target:'good',kind:'component',component:'pWe',
         description:'Change the exogenous foreign-currency export price received for one good.',
         meaning:'Changes the export opportunity and induces CET reallocation between exports and domestic sales.',
         watch:'E, D, Z, domestic prices, factor demand, household income.',
         caution:'This is an exogenous price under the small-country assumption.'}
      ],
      quick:[
        {label:'Abolish BRD tariff',control:'tariff',target:'BRD',op:'zero'},
        {label:'Cut BRD tariff 50%',control:'tariff',target:'BRD',op:'pct',amount:-50},
        {label:'MLK production tax → 5%',control:'production_tax',target:'MLK',op:'level',amount:0.05},
        {label:'World BRD import price +10%',control:'world_import_price',target:'BRD',op:'pct',amount:10},
        {label:'Foreign saving +10%',control:'foreign_saving',op:'pct',amount:10},
        {label:'Labor endowment +10%',control:'endowment',target:'LAB',op:'pct',amount:10}
      ],
      outputs:[
        ['Production','Z[i], Y[i]: sector output and value added.'],
        ['Intermediate network','X[i,j]: input-output propagation.'],
        ['Factors','F[h,i], pf[h]: allocation and returns.'],
        ['Households','Xp[i]: consumption after income/prices adjust.'],
        ['Government','Xg[i] and tax revenues Td, Tz, Tm.'],
        ['Investment','Xv[i] and saving-financed absorption.'],
        ['Trade','M[i], E[i], D[i], Q[i].'],
        ['Prices','pz, pq, pe, pm, pd, py, pf, epsilon.'],
        ['Welfare','Utility and optional money-metric measures.'],
        ['Comparison','Benchmark, counterfactual, difference and percent change.']
      ]
    },

    ifpri: {
      title:'IFPRI Standard',
      badge:'Richer institutional model',
      card:'Named macro closures · public synthetic economy',
      description:'A separate IFPRI Standard CGE implementation with activities, commodities, factors, households and government, plus explicit macro-closure rules. The public package uses an independently authored synthetic economy; official-source replication remains a separate evidence lane.',
      useWhen:'Use the validated named scenarios when fiscal or external closure is part of the policy question.',
      avoidWhen:'Do not treat the public synthetic economy as the official IFPRI benchmark or assume the Hosoe shock helpers apply to IFPRI closure machinery.',
      facts:['Named scenarios','Explicit macro closure','Synthetic public data','Separate official evidence lane'],
      labels:null,
      dataChoices:[
        ['synthetic','Public synthetic economy','Redistributable data used by CI, tutorials and notebooks.'],
        ['official','Official-source data','Use only when you possess the external IFPRI source material.']
      ],
      closure:{
        title:'IFPRI model-owned macro closure',
        anchor:'Each validated named scenario carries the macro-closure changes appropriate to that experiment.',
        adjusts:'Activities, commodities, institutions, prices, factors, government saving/direct taxes, foreign saving/exchange rate, and other endogenous variables adjust according to the scenario closure.',
        note:'The public façade deliberately exposes named scenarios rather than hiding closure changes behind a generic shock editor.'
      },
      glossary:[
        ['QA, QH','Activities / output','Production and domestic-output quantities.'],
        ['QM, QE','Imports / exports','External trade quantities.'],
        ['CPI, DPI','Price indices','Consumer and domestic price indices used in closure.'],
        ['EXR','Exchange rate','External price adjustment variable in relevant closures.'],
        ['FSAV','Foreign saving','External-balance closure variable.'],
        ['GSAV','Government saving','Fiscal closure variable.'],
        ['DTINS','Direct tax adjustment','Institutional direct-tax-rate adjustment in the compensating fiscal closure.']
      ],
      story:[
        'The IFPRI benchmark calibrates a richer activity–commodity–institution accounting structure.',
        'A named policy scenario changes both the policy instrument and, where required, the macro closure.',
        'Activities, trade, factor returns, institutional incomes, taxes, saving, demand, and price indices adjust jointly.',
        'The same tariff cut can therefore have different incidence depending on whether government saving moves or direct taxes compensate.',
        'Public tutorials use synthetic data; official-source replication remains a separate provenance and validation exercise.'
      ],
      scenarios:[
        {id:'TARCUT1',title:'TARCUT1 · Tariff cut, flexible government saving',accent:'blue',
         description:'Cut benchmark import tariffs by 50%; let the fiscal loss appear through flexible government saving.'},
        {id:'TARCUT2',title:'TARCUT2 · Tariff cut, direct-tax adjustment',accent:'green',
         description:'Cut tariffs by 50%, hold government saving fixed, and let direct-tax rates adjust.'},
        {id:'FSAVINCR',title:'FSAVINCR · Foreign saving +10%',accent:'violet',
         description:'Increase benchmark foreign saving by 10%.'},
        {id:'PWMINCR',title:'PWMINCR · World import prices +10%',accent:'gold',
         description:'Increase benchmark world import prices by 10%.'},
        {id:'DEVAL',title:'DEVAL · 10% devaluation',accent:'rose',
         description:'Apply the validated devaluation closure with the exchange rate 10% above benchmark.'}
      ],
      outputs:[
        ['Activities / commodities','Production and supply quantities.'],
        ['Trade','QM imports and QE exports.'],
        ['Price system','CPI, DPI, exchange rate and commodity/activity prices.'],
        ['Factors','Factor demand and returns.'],
        ['Institutions','Household and government income, taxes, saving and demand.'],
        ['Macro closure','GSAV / DTINS and FSAV / EXR according to scenario.'],
        ['Diagnostics','Termination condition and maximum equation residual.'],
        ['Comparison','Scenario − BASE and percent change.']
      ]
    },

    camcge: {
      title:'CAMCGE',
      badge:'Cameroon 1987 replication',
      card:'11 sectors · 3 labor groups · 3 published experiments',
      description:'The Cameroon replication is a first-class installed model in v0.7 while retaining its own equations, data and closure. Its central role is independent historical validation against the published benchmark and policy experiments.',
      useWhen:'Use it to reproduce and inspect the published Cameroon benchmark and three policy experiments.',
      avoidWhen:'Do not treat it as a generic country template unless you intentionally adapt its economics, data and closure.',
      facts:['11 sectors','3 labor groups','3 experiments','Published replication'],
      labels:null,
      dataChoices:[
        ['example','Bundled Cameroon data','Use the packaged replication dataset.'],
        ['directory','Prepared CAMCGE data directory','Use an intentionally adapted CAMCGE-format dataset.']
      ],
      closure:{
        title:'CAMCGE-specific canonical closure',
        anchor:'The historical model retains its own savings, external-account, price-anchor, and market-clearing closure.',
        adjusts:'Sector output, domestic/composite prices, trade, labor returns, investment and other modeled quantities respond according to CAMCGE.',
        note:'v0.7 makes CAMCGE easier to call; it does not rewrite the model into the Hosoe Standard CGE.'
      },
      glossary:[
        ['xd[i]','Domestic output','Sector output used in the published experiment tables.'],
        ['pd[i], p[i]','Prices','Domestic and composite prices.'],
        ['e[i], mq[i]','Exports / imports','Trade quantities for traded sectors.'],
        ['wa[l]','Labor return','Nominal wage/return for each labor category.'],
        ['fsav','Foreign saving','External financing term used in Experiment 1.'],
        ['tm[i]','Import tariff','Sectoral tariff rate used in Experiments 2 and 3.']
      ],
      story:[
        'The bundled benchmark reproduces the historical Cameroon model before policy changes.',
        'Experiment 1 raises foreign saving to reproduce the oil-windfall/resource-inflow experiment.',
        'Experiment 2 doubles the tariff on food-crop imports.',
        'Experiment 3 doubles tariffs on intermediate goods and construction materials.',
        'The validation suite compares model outcomes with the published experiment targets.'
      ],
      scenarios:[
        {id:'EXP1',title:'Experiment 1 · Oil windfall / FSAV = 500',accent:'blue',
         description:'Set fsav to 500.'},
        {id:'EXP2',title:'Experiment 2 · Double food-crop tariff',accent:'gold',
         description:'Set tm["ag-subsist"] to 0.4410.'},
        {id:'EXP3',title:'Experiment 3 · Double two intermediate tariffs',accent:'rose',
         description:'Set tm["biens-int"] to 0.3536 and tm["cim-int"] to 0.5266.'}
      ],
      outputs:[
        ['Output','xd[i]: published sector-output responses.'],
        ['Prices','pd[i], p[i]: domestic and composite price responses.'],
        ['Trade','e[i], mq[i]: exports and imports.'],
        ['Labor','wa[l]: nominal and real wage interpretation.'],
        ['Investment','Real investment response.'],
        ['Tariff revenue','Fiscal effect of tariff experiments.'],
        ['Published validation','Model vs DRD290 target changes.']
      ]
    }
  };

  const state = {
    model:'standard',
    labels:{goods:['BRD','MLK'],factors:['CAP','LAB']},
    dataChoice:'example',
    dataPath:'sam.csv',
    directoryPath:'path/to/data',
    scenarioName:'Policy experiment',
    stack:[]
  };

  const CANONICAL_STDCGE_TARIFF = `from cge_core import StandardCGE

base = StandardCGE.example().solve()

scenario = base.scenario("Tariff abolition")
scenario.tariff("BRD", 0)

result = scenario.solve()

print(result.summary())
print(result.compare(base))`;

  function model(){ return MODELS[state.model]; }

  function setText(id, text){ const el=$(id); if(el) el.textContent=text; }

  function picture(kind){
    const common = `font-family="Inter,Segoe UI,sans-serif" font-size="12"`;
    const box = (x,y,w,h,label,fill='var(--panel)') =>
      `<g><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="12" fill="${fill}" stroke="var(--line)"/>
       <text x="${x+w/2}" y="${y+h/2+4}" text-anchor="middle" fill="var(--text)" ${common} font-weight="700">${esc(label)}</text></g>`;
    const arrow = (x1,y1,x2,y2,label='') =>
      `<g><path d="M${x1},${y1} L${x2},${y2}" stroke="var(--muted)" stroke-width="2" marker-end="url(#a)"/>
       ${label?`<text x="${(x1+x2)/2}" y="${(y1+y2)/2-5}" text-anchor="middle" fill="var(--muted)" ${common}>${esc(label)}</text>`:''}</g>`;
    let body='';
    if(kind==='simple'){
      body += box(28,40,120,54,'Household','var(--blue-soft)');
      body += box(292,40,120,54,'Firms','var(--green-soft)');
      body += box(28,210,120,54,'Factor markets');
      body += box(292,210,120,54,'Goods markets');
      body += arrow(148,65,292,65,'consumption');
      body += arrow(292,82,148,225,'factor income');
      body += arrow(148,235,292,82,'labor / capital');
      body += arrow(412,215,412,95,'output');
    } else if(kind==='standard'){
      body += box(18,28,105,50,'Household','var(--blue-soft)');
      body += box(168,28,105,50,'Government','var(--gold-soft)');
      body += box(318,28,105,50,'Investment','var(--violet-soft)');
      body += box(168,130,105,50,'Sectors','var(--green-soft)');
      body += box(18,225,105,50,'Factors');
      body += box(318,225,105,50,'Rest of world','var(--rose-soft)');
      body += arrow(70,78,190,130,'demand');
      body += arrow(220,78,220,130,'demand / tax');
      body += arrow(370,78,255,130,'investment');
      body += arrow(168,155,123,245,'factor demand');
      body += arrow(273,155,318,245,'trade');
      body += arrow(123,235,170,175,'income');
    } else if(kind==='ifpri'){
      body += box(18,28,110,48,'Activities','var(--green-soft)');
      body += box(165,28,110,48,'Commodities','var(--blue-soft)');
      body += box(312,28,110,48,'Rest of world','var(--rose-soft)');
      body += box(18,215,110,48,'Factors');
      body += box(165,215,110,48,'Households');
      body += box(312,215,110,48,'Government','var(--gold-soft)');
      body += box(165,120,110,48,'Macro closure','var(--violet-soft)');
      body += arrow(128,52,165,52);
      body += arrow(312,52,275,52,'trade');
      body += arrow(72,215,72,76,'factor use');
      body += arrow(128,239,165,239,'income');
      body += arrow(275,239,312,239,'tax');
      body += arrow(220,215,220,168);
      body += arrow(367,215,260,168);
    } else {
      body += box(18,28,110,48,'11 sectors','var(--green-soft)');
      body += box(165,28,110,48,'Domestic market','var(--blue-soft)');
      body += box(312,28,110,48,'Trade','var(--rose-soft)');
      body += box(18,215,110,48,'3 labor groups');
      body += box(165,215,110,48,'Investment','var(--violet-soft)');
      body += box(312,215,110,48,'External balance','var(--gold-soft)');
      body += box(165,120,110,48,'CAMCGE closure');
      body += arrow(128,52,165,52); body += arrow(275,52,312,52);
      body += arrow(72,215,72,76); body += arrow(220,215,220,168);
      body += arrow(367,215,260,168);
    }
    return `<svg viewBox="0 0 440 300" role="img" aria-label="${esc(kind)} economy diagram">
      <defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L0,6 L7,3 z" fill="var(--muted)"/></marker></defs>${body}</svg>`;
  }

  function renderModelCards(){
    $('modelCards').innerHTML = MODEL_ORDER.map((key,i)=>{
      const m=MODELS[key];
      return `<button class="model-card ${key===state.model?'active':''}" data-model="${key}">
        <span class="model-number">0${i+1}</span><strong>${esc(m.title)}</strong><p>${esc(m.card)}</p>
      </button>`;
    }).join('');
    document.querySelectorAll('[data-model]').forEach(btn=>{
      btn.addEventListener('click',()=>selectModel(btn.dataset.model));
    });
  }

  function renderOverview(){
    const m=model();
    setText('modelBadge',m.badge); setText('modelTitle',m.title); setText('modelDescription',m.description);
    $('modelPolicyUse').innerHTML =
      `<div class="policy-box good"><strong>Use it when</strong>${esc(m.useWhen)}</div>
       <div class="policy-box caution"><strong>Do not use it when</strong>${esc(m.avoidWhen)}</div>`;
    $('modelFacts').innerHTML=m.facts.map(x=>`<span class="fact">${esc(x)}</span>`).join('');
    $('economyPicture').innerHTML=picture(state.model);
  }

  function renderWalkthrough(){
    const m=model();
    setText('walkthroughIntro',`Understand ${m.title} as an economic system before selecting a shock.`);
    $('storyNav').innerHTML=[
      ['Notation','notationPanel'],['Variables','glossaryPanel'],['Adjustment story','storyPanel']
    ].map(([label,id])=>`<button data-scroll="${id}">${label}</button>`).join('');
    document.querySelectorAll('[data-scroll]').forEach(b=>b.addEventListener('click',()=>{
      document.getElementById(b.dataset.scroll).scrollIntoView({behavior:'smooth',block:'start'});
    }));
    const notation=[
      ['i, j','goods / sectors','Indices identify commodities or producing sectors.'],
      ['h, l','factors / labor groups','Indices identify primary factors or labor categories.'],
      ['P / p','price','Prices are endogenous unless the model closure fixes them.'],
      ['Q / X / Z','quantity','Different models use different quantity symbols; read the model glossary.'],
      ['τ / t','tax rate','Ad valorem rates are decimals in model code.'],
      ['Δ / %','counterfactual change','Compare the solved scenario with the solved benchmark.']
    ];
    $('notationPrimer').innerHTML=notation.map(([s,t,d])=>
      `<div class="notation-card"><strong><span class="symbol">${esc(s)}</span> · ${esc(t)}</strong><span>${esc(d)}</span></div>`
    ).join('');
    setText('variableGlossaryTitle',`${m.title}: key symbols`);
    setText('variableGlossaryIntro','Names differ across model families. The Control Room uses the symbols of the selected implementation rather than forcing one universal notation.');
    $('variableGlossary').innerHTML=m.glossary.map(([s,n,d])=>
      `<div class="glossary-item"><strong><span class="symbol">${esc(s)}</span> · ${esc(n)}</strong><p>${esc(d)}</p></div>`
    ).join('');
    setText('flowStoryTitle',`${m.title}: how a counterfactual propagates`);
    $('flowStory').innerHTML=m.story.map((x,i)=>
      `<div class="story-step"><div class="n">${i+1}</div><p>${esc(x)}</p></div>`
    ).join('');
  }

  function resetLabels(){
    const m=model();
    if(m.labels) state.labels={goods:[...m.labels.goods],factors:[...m.labels.factors]};
    renderData();
    renderScenario();
    renderScript();
  }

  function renderLabels(){
    const m=model();
    if(!m.labels){
      $('labelManagers').innerHTML=`<div class="label-group"><strong>Model-owned structure</strong>
        <p class="help">${m.title} uses its validated bundled structure. Scenario targets below are model-specific rather than free-form labels.</p></div>`;
      $('resetLabelsBtn').classList.add('hidden');
      setText('labelsNote','The Control Room does not pretend that arbitrary relabelling preserves a validated model specification.');
      return;
    }
    $('resetLabelsBtn').classList.remove('hidden');
    $('labelManagers').innerHTML=['goods','factors'].map(group=>{
      const title=group==='goods'?'Goods / sectors':'Primary factors';
      const chips=state.labels[group].map((x,i)=>`<span class="label-chip">${esc(x)}
        <button class="icon-button" data-remove="${group}:${i}" title="Remove ${esc(x)}">×</button></span>`).join('');
      return `<div class="label-group"><div class="label-group-head"><strong>${title}</strong><span class="help">${state.labels[group].length} active</span></div>
        <div class="label-list">${chips}</div>
        <div class="add-row"><input id="add-${group}" class="text-input" placeholder="Add label">
        <button class="button small ghost" data-add="${group}">Add</button></div></div>`;
    }).join('');
    document.querySelectorAll('[data-remove]').forEach(b=>b.addEventListener('click',()=>{
      const [group,idx]=b.dataset.remove.split(':'); state.labels[group].splice(Number(idx),1);
      renderData();renderScenario();renderScript();
    }));
    document.querySelectorAll('[data-add]').forEach(b=>b.addEventListener('click',()=>{
      const group=b.dataset.add, input=$(`add-${group}`), value=input.value.trim();
      if(value && !state.labels[group].includes(value)){state.labels[group].push(value.toUpperCase());}
      renderData();renderScenario();renderScript();
    }));
    setText('labelsNote','These labels control which example targets appear in the scenario editor. For empirical work, they must correspond to actual model/data indices.');
  }

  function renderDataSource(){
    const m=model();
    $('dataSourcePanel').innerHTML =
      `<div class="data-choice">${m.dataChoices.map(([id,title,desc])=>
        `<button class="choice-card ${state.dataChoice===id?'active':''}" data-data="${id}">
          <strong>${esc(title)}</strong><span>${esc(desc)}</span></button>`).join('')}</div>
       <div id="dataDetail"></div>`;
    document.querySelectorAll('[data-data]').forEach(b=>b.addEventListener('click',()=>{
      state.dataChoice=b.dataset.data; renderDataSource(); renderClosure(); renderScenario(); renderScript();
    }));
    let detail='';
    if(state.dataChoice==='sam'){
      detail=`<div class="form-grid"><div class="form-field"><label>SAM file</label>
        <input id="dataPathInput" class="text-input" value="${esc(state.dataPath)}"></div>
        <div class="form-field"><label>Assumption</label><div class="command">balanced square SAM</div></div></div>
        <p class="help">Canonical Hosoe account roles are defaults. Country-specific roles should be stated explicitly in the generated code after export.</p>`;
    } else if(state.dataChoice==='directory'){
      detail=`<div class="form-grid"><div class="form-field"><label>Prepared data directory</label>
        <input id="directoryPathInput" class="text-input" value="${esc(state.directoryPath)}"></div></div>`;
    } else if(state.dataChoice==='official'){
      detail=`<div class="form-grid"><div class="form-field"><label>Official-source path</label>
        <input id="directoryPathInput" class="text-input" value="${esc(state.directoryPath)}"></div></div>
        <p class="help">The official IFPRI source material is not redistributed by CGE-Core.</p>`;
    } else {
      detail=`<p class="help">No file path is required. The installed package supplies the example/synthetic benchmark.</p>`;
    }
    $('dataDetail').innerHTML=detail;
    const dp=$('dataPathInput'); if(dp) dp.addEventListener('input',()=>{state.dataPath=dp.value;renderScript();});
    const dir=$('directoryPathInput'); if(dir) dir.addEventListener('input',()=>{state.directoryPath=dir.value;renderScript();});
  }

  function renderData(){
    const m=model();
    setText('economyIntro', m.labels ?
      'The example labels below determine which sector/factor targets the editor offers. Choose the benchmark source separately.' :
      `${m.title} keeps its validated structural labels; choose the appropriate data provenance.`);
    renderLabels(); renderDataSource();
    $('economyStatus').className='status-pill ok'; setText('economyStatus','Data path selected');
  }

  function renderClosure(){
    const c=model().closure;
    setText('closureIntro','Closure determines which variables are exogenous and which variables adjust to clear the model. v0.7 hides routine closure plumbing without hiding its economic meaning.');
    setText('closureStatus','Model-owned');
    $('closurePanel').innerHTML =
      `<div class="mini-label">${esc(c.title)}</div>
       <div class="closure-map">
         <div class="closure-box"><strong>Fixed / exogenous side</strong><p class="help">${esc(c.anchor)}</p></div>
         <div class="closure-arrow">→</div>
         <div class="closure-box"><strong>Endogenous adjustment</strong><p class="help">${esc(c.adjusts)}</p></div>
       </div>
       <div class="closure-summary">${esc(c.note)}</div>`;
    $('preflightPanel').innerHTML =
      `<div class="mini-label">Preflight</div><h3>Before you solve</h3>
       <div class="check-list">
         <div class="check"><b>✓</b><span>Model family: ${esc(model().title)}</span></div>
         <div class="check"><b>✓</b><span>Data source: ${esc(state.dataChoice)}</span></div>
         <div class="check"><b>✓</b><span>Canonical/model-specific closure will be applied by CGE-Core.</span></div>
         <div class="check"><b>✓</b><span>Each scenario will be an independent counterfactual.</span></div>
       </div>`;
  }

  function targetOptions(control){
    if(control.target==='good') return state.labels.goods;
    if(control.target==='factor') return state.labels.factors;
    return [];
  }

  function renderControlEditor(control){
    const options=targetOptions(control);
    $('controlEditor').classList.remove('hidden');
    $('controlEditor').innerHTML =
      `<div class="editor-head"><div><div class="mini-label">${esc(control.symbol)}</div><h3>${esc(control.name)}</h3></div>
       <button class="button small ghost" id="closeEditor">Close</button></div>
       <p class="help">${esc(control.description)}</p>
       <div class="form-grid">
         ${control.target!=='scalar'?`<div class="form-field"><label>Target</label><select id="editorTarget" class="select">
           ${options.map(x=>`<option>${esc(x)}</option>`).join('')}</select></div>`:''}
         <div class="form-field"><label>Scenario name</label><input id="scenarioNameInput" class="text-input" value="${esc(state.scenarioName)}"></div>
       </div>
       <div class="operation-grid">
         <button class="choice-card" data-op="zero"><strong>Set to zero</strong><span>Useful for abolition.</span></button>
         <button class="choice-card" data-op="level"><strong>Set level</strong><span>Enter a new level/rate.</span></button>
         <button class="choice-card" data-op="pct"><strong>Percent change</strong><span>Scale the benchmark value.</span></button>
       </div>
       <div id="operationDetail"></div>
       <div class="policy-use">
         <div class="policy-box good"><strong>Economic meaning</strong>${esc(control.meaning)}</div>
         <div class="policy-box caution"><strong>Interpret carefully</strong>${esc(control.caution)}</div>
       </div>
       <p class="help"><strong>Watch:</strong> ${esc(control.watch)}</p>`;
    $('closeEditor').addEventListener('click',()=>$('controlEditor').classList.add('hidden'));
    $('scenarioNameInput').addEventListener('input',e=>{state.scenarioName=e.target.value || 'Policy experiment';renderScript();});
    document.querySelectorAll('[data-op]').forEach(b=>b.addEventListener('click',()=>renderOperation(control,b.dataset.op)));
  }

  function renderOperation(control,op){
    let prompt=op==='pct'?'Percent change':op==='level'?'New level / rate':'Set to zero';
    let defaultValue=op==='pct'?'10':control.id.includes('tax')||control.id==='tariff'?'0.05':'1.0';
    $('operationDetail').innerHTML =
      `<div class="form-grid">
        ${op!=='zero'?`<div class="form-field"><label>${prompt}</label><input id="operationValue" class="text-input" type="number" step="any" value="${defaultValue}"></div>`:''}
        <div class="form-field"><label>Action</label><button id="addShockBtn" class="button primary">Add to scenario</button></div>
       </div>`;
    $('addShockBtn').addEventListener('click',()=>{
      const targetEl=$('editorTarget');
      const target=targetEl?targetEl.value:null;
      const val=op==='zero'?0:Number($('operationValue').value);
      state.stack.push({type:'shock',control:control.id,target,op,amount:val});
      renderScenario();renderScript();
    });
  }

  function addQuick(q){
    state.stack.push({type:'shock',control:q.control,target:q.target||null,op:q.op,amount:q.amount ?? 0});
    renderScenario();renderScript();
  }

  function selectNamedScenario(id){
    state.stack=[{type:'named',id}];
    state.scenarioName=id;
    renderScenario();renderScript();
  }

  function renderScenario(){
    const m=model();
    setText('scenarioIntro', state.model==='ifpri' ?
      'Choose one validated IFPRI named scenario; its policy and macro closure belong together.' :
      state.model==='camcge' ?
      'Choose one published Cameroon experiment; the Control Room reproduces its documented shock values.' :
      'Choose an economic control, target, and level or proportional change. Multiple shocks can be stacked into one counterfactual.');
    $('quickActions').innerHTML='';
    $('controlCards').innerHTML='';
    $('controlEditor').classList.add('hidden');

    if(m.scenarios){
      setText('controlHeading',state.model==='ifpri'?'Validated named scenarios':'Published experiments');
      $('controlCards').innerHTML=m.scenarios.map(s=>
        `<button class="control-card scenario-option" data-accent="${esc(s.accent)}" data-named="${esc(s.id)}">
          <div class="control-top"><span class="control-symbol">${esc(s.id)}</span></div>
          <strong>${esc(s.title)}</strong><p>${esc(s.description)}</p></button>`).join('');
      document.querySelectorAll('[data-named]').forEach(b=>b.addEventListener('click',()=>selectNamedScenario(b.dataset.named)));
    } else {
      setText('controlHeading','What do you want to change?');
      $('quickActions').innerHTML=m.quick.map((q,i)=>`<button class="quick-button" data-quick="${i}">${esc(q.label)}</button>`).join('');
      document.querySelectorAll('[data-quick]').forEach(b=>b.addEventListener('click',()=>addQuick(m.quick[Number(b.dataset.quick)])));
      $('controlCards').innerHTML=m.controls.map(c=>
        `<button class="control-card" data-control="${esc(c.id)}">
          <div class="control-top"><span class="control-symbol">${esc(c.symbol)}</span></div>
          <strong>${esc(c.name)}</strong><p>${esc(c.description)}</p></button>`).join('');
      document.querySelectorAll('[data-control]').forEach(b=>b.addEventListener('click',()=>{
        renderControlEditor(m.controls.find(c=>c.id===b.dataset.control));
      }));
    }
    renderStack();
  }

  function stackLabel(item){
    if(item.type==='named'){
      const s=model().scenarios.find(x=>x.id===item.id);
      return s?s.title:item.id;
    }
    const c=model().controls.find(x=>x.id===item.control);
    const target=item.target?` ${item.target}`:'';
    if(item.op==='zero') return `${c.name}${target} → 0`;
    if(item.op==='pct') return `${c.name}${target} ${item.amount>=0?'+':''}${item.amount}%`;
    return `${c.name}${target} → ${item.amount}`;
  }

  function renderStack(){
    if(!state.stack.length){
      $('scenarioStack').innerHTML='<div class="empty-stack">No changes yet. Choose a quick action, a control, or a named experiment.</div>';
      setText('stackSummary','The benchmark will still be solved, but there is no counterfactual yet.');
      $('scenarioStatus').className='status-pill warn';setText('scenarioStatus','Add a scenario');
      return;
    }
    $('scenarioStack').innerHTML=state.stack.map((item,i)=>
      `<div class="stack-item"><div class="stack-item-head"><strong>${esc(stackLabel(item))}</strong>
       <div class="stack-controls"><button data-delete="${i}" title="Remove">×</button></div></div></div>`).join('');
    document.querySelectorAll('[data-delete]').forEach(b=>b.addEventListener('click',()=>{
      state.stack.splice(Number(b.dataset.delete),1);renderScenario();renderScript();
    }));
    setText('stackSummary',`${state.stack.length} planned change${state.stack.length===1?'':'s'} in one independent counterfactual.`);
    $('scenarioStatus').className='status-pill ok';setText('scenarioStatus','Scenario defined');
  }

  function modelConstructor(){
    if(state.model==='simple'){
      return state.dataChoice==='directory' ?
        `model = SimpleCGE(${JSON.stringify(state.directoryPath)})` :
        'model = SimpleCGE.example()';
    }
    if(state.model==='standard'){
      if(state.dataChoice==='sam') return `model = StandardCGE.from_sam(${JSON.stringify(state.dataPath)})`;
      if(state.dataChoice==='directory') return `model = StandardCGE(${JSON.stringify(state.directoryPath)})`;
      return 'model = StandardCGE.example()';
    }
    if(state.model==='ifpri'){
      return state.dataChoice==='official' ?
        `model = IFPRICGE.from_official_source(${JSON.stringify(state.directoryPath)})` :
        'model = IFPRICGE.synthetic()';
    }
    return state.dataChoice==='directory' ?
      `model = CamCGE.from_data(${JSON.stringify(state.directoryPath)})` :
      'model = CamCGE.example()';
  }

  function shockLine(item){
    const c=model().controls.find(x=>x.id===item.control);
    const target=item.target===null?'None':JSON.stringify(item.target);
    if(c.kind==='semantic'){
      if(item.op==='pct') return `scenario.${c.method}(${target}, change=${(item.amount/100).toFixed(6).replace(/0+$/,'').replace(/\.$/,'')})`;
      return `scenario.${c.method}(${target}, ${item.amount})`;
    }
    if(item.op==='pct'){
      const idx=item.target===null?'':`, ${JSON.stringify(item.target)}`;
      return `scenario.set(${JSON.stringify(c.component)}, ${target}, base.value(${JSON.stringify(c.component)}${idx}) * ${(1+item.amount/100).toFixed(6).replace(/0+$/,'').replace(/\.$/,'')})`;
    }
    return `scenario.set(${JSON.stringify(c.component)}, ${target}, ${item.amount})`;
  }

  function camLines(id){
    if(id==='EXP1') return ['scenario.set("fsav", None, 500)'];
    if(id==='EXP2') return ['scenario.set("tm", "ag-subsist", 0.4410)'];
    return ['scenario.set("tm", "biens-int", 0.3536)','scenario.set("tm", "cim-int", 0.5266)'];
  }

  function generateCode(){
    const cls={simple:'SimpleCGE',standard:'StandardCGE',ifpri:'IFPRICGE',camcge:'CamCGE'}[state.model];
    const lines=[`from cge_core import ${cls}`,'',modelConstructor(),'base = model.solve()'];

    if(!state.stack.length){
      lines.push('','print(base.summary())');
      return lines.join('\n');
    }

    if(state.model==='ifpri'){
      const id=state.stack[0].id;
      lines.push('',`result = base.scenario(${JSON.stringify(id)}).solve()`,'','print(result.summary())','print(result.compare(base))');
      return lines.join('\n');
    }

    lines.push('',`scenario = base.scenario(${JSON.stringify(state.scenarioName || 'Policy experiment')})`);
    if(state.model==='camcge' && state.stack[0].type==='named'){
      lines.push(...camLines(state.stack[0].id));
    } else {
      state.stack.forEach(item=>lines.push(shockLine(item)));
    }
    lines.push('','result = scenario.solve()','','print(result.summary())','print(result.compare(base))');
    return lines.join('\n');
  }

  function renderRunInstructions(){
    $('runInstructions').innerHTML =
      `<div class="run-steps">
        <div class="run-step"><div><strong>Install v0.7.0</strong><div class="command">${esc(INSTALL)}</div></div></div>
        <div class="run-step"><div><strong>Run your script</strong><div class="command">python scenario.py</div></div></div>
        <div class="run-step"><div><strong>Or use Colab</strong><p class="help">The canonical notebook performs the package installation in one cell, then goes directly to modelling.</p></div></div>
       </div>`;
    $('resultFiles').innerHTML=[
      'base.summary() — benchmark solve metadata',
      'result.summary() — counterfactual solve metadata',
      'result.compare(base) — variable-by-variable benchmark comparison',
      'result.value(...) — targeted numerical reads'
    ].map(x=>`<div class="result-file">${esc(x)}</div>`).join('');
  }

  function renderOutputs(){
    $('outputsGrid').innerHTML=model().outputs.map(([n,d])=>
      `<div class="output-card"><strong>${esc(n)}</strong><p>${esc(d)}</p></div>`).join('');
  }

  function renderScript(){
    const code=generateCode();
    $('codePreview').querySelector('code').textContent=code;
    setText('scriptCaption',`${model().title} · ${state.stack.length?state.scenarioName:'benchmark only'}`);
    $('readyStatus').className=`status-pill ${state.stack.length?'ok':'warn'}`;
    setText('readyStatus',state.stack.length?'Ready to run':'Benchmark only');
    renderRunInstructions();renderOutputs();
  }

  function download(filename,text,type='text/plain'){
    const blob=new Blob([text],{type});
    const url=URL.createObjectURL(blob), a=document.createElement('a');
    a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();
    URL.revokeObjectURL(url);
  }

  function exportJSON(){
    return JSON.stringify({
      cge_core_version:CGE_CORE_TARGET_VERSION,
      model:state.model,
      data_choice:state.dataChoice,
      data_path:state.dataChoice==='sam'?state.dataPath:state.directoryPath,
      scenario_name:state.scenarioName,
      changes:state.stack
    },null,2);
  }

  function selectModel(key){
    state.model=key;
    const m=model();
    state.labels=m.labels?{goods:[...m.labels.goods],factors:[...m.labels.factors]}:{goods:[],factors:[]};
    state.dataChoice=m.dataChoices[0][0];
    state.scenarioName=key==='ifpri'?'TARCUT1':key==='camcge'?'Published experiment':'Policy experiment';
    state.stack=[];
    renderAll();
  }

  function renderAll(){
    renderModelCards();renderOverview();renderWalkthrough();renderData();renderClosure();renderScenario();renderScript();
  }

  $('themeSelect').value=document.documentElement.dataset.theme || 'light';
  $('themeSelect').addEventListener('change',e=>{
    document.documentElement.dataset.theme=e.target.value;
    try{localStorage.setItem('cge-control-room-theme',e.target.value);}catch(_){}
  });
  $('resetLabelsBtn').addEventListener('click',resetLabels);
  $('clearStackBtn').addEventListener('click',()=>{state.stack=[];renderScenario();renderScript();});
  $('copyCodeBtn').addEventListener('click',async()=>{
    const code=generateCode();
    try{await navigator.clipboard.writeText(code);setText('copyCodeBtn','Copied');setTimeout(()=>setText('copyCodeBtn','Copy'),1200);}
    catch(_){download('scenario.py',code);}
  });
  $('downloadPyBtn').addEventListener('click',()=>download('scenario.py',generateCode(),'text/x-python'));
  $('downloadJsonBtn').addEventListener('click',()=>download('cge-scenario.json',exportJSON(),'application/json'));

  // Public API examples retained as static regression sentinels:
  // scenario.tariff("BRD", 0)
  // scenario.endowment("LAB", change=0.10)
  // scenario.production_tax("MLK", 0.05)
  // This literal is deliberately retained as a regression fixture target.
  // It represents the smallest complete Standard-CGE tariff experiment.
  void CANONICAL_STDCGE_TARIFF;

  renderAll();
})();
