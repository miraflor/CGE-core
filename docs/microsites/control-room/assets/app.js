
(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const esc = (value) => String(value).replace(/[&<>"']/g, ch => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[ch]));

  const MODEL_ORDER = ['simple','standard','ifpri','camcge'];

  const MODELS = {
    simple: {
      title:'Simple CGE',
      badge:'Hosoe teaching model',
      card:'Closed economy · households + firms + factor markets',
      description:'The smallest CGE-Core model. A representative household owns the primary factors, firms hire those factors to produce goods, and relative prices adjust until both goods and factor markets clear. There is no government, foreign trade, or intermediate-input network.',
      useWhen:'Use this model to understand general-equilibrium mechanics or to study a clean factor-supply/endowment shock without trade or fiscal complications.',
      avoidWhen:'Do not use it for tariffs, taxes, government spending, imports/exports, input-output propagation, or dynamic adjustment over time.',
      facts:['Static equilibrium','Closed economy','No government','No trade'],
      picture:'simple',
      editableLabels:true,
      labelGroups:{
        goods:{title:'Goods / sectors', defaults:['BRD','MLK']},
        factors:{title:'Primary factors', defaults:['CAP','LAB']}
      },
      data:{type:'engine', example:'splcge', custom:true},
      closure:{kind:'engine', numeraireOptions:['pf','px','pz'], walrasOptions:['eqpf','eqpx'], defaultNumeraire:'pf', defaultWalras:'eqpf'},
      controls:[
        {id:'ff',name:'Factor endowment',symbol:'FF[h]',component:'FF',target:'factor',
          description:'Change the exogenous quantity of a primary factor available to the economy.',
          meaning:'This asks: what would the equilibrium look like if the economy had more or less of this factor, with preferences and production technology otherwise unchanged?',
          watch:'Watch the factor price first. A larger labor endowment, for example, does not mechanically mean employment rises by exactly the same percentage; the wage and the allocation of labor across sectors adjust endogenously.',
          caution:'Interpret FF as an exogenous factor-supply/endowment scenario, not automatically as a jobs-created policy target.',
          unit:'quantity',domain:'positive',allowZero:false}
      ],
      quick:[
        {label:'+10% labor',control:'ff',target:'LAB',op:'pct',amount:10},
        {label:'−10% labor',control:'ff',target:'LAB',op:'pct',amount:-10},
        {label:'+10% capital',control:'ff',target:'CAP',op:'pct',amount:10}
      ],
      outputs:[
        ['Consumption','X[i]: how household demand for each good changes after income and relative prices adjust.'],
        ['Production','Z[i]: sector output in the new equilibrium; compare which sectors expand and contract.'],
        ['Factor demand','F[h,i]: how labor/capital are reallocated across sectors.'],
        ['Goods prices','px[i], pz[i]: relative consumer/producer price signals that coordinate the new equilibrium.'],
        ['Factor prices','pf[h]: wages/returns to modeled primary factors; central for incidence.'],
        ['Welfare','Utility objective: a compact measure of whether the representative household is better or worse off.'],
        ['Comparison','SIM − BASE and percent change']
      ]
    },

    standard: {
      title:'Standard CGE',
      badge:'Hosoe open-economy model',
      card:'Sectors + intermediates + government + trade + investment',
      description:'CGE-Core’s generic open-economy model. Sectors use primary factors and intermediate inputs; households consume and save; government collects taxes and purchases goods; saving finances investment; and domestic goods compete with imports while producers divide output between domestic and export markets.',
      useWhen:'Use this for sectoral tax and tariff reform, world-price shocks, factor-supply shocks, and questions where input-output linkages and trade reallocation matter.',
      avoidWhen:'It is a static representative-household model. It is not designed for year-by-year debt dynamics, demographic cohorts, detailed household distribution, or a financial sector.',
      facts:['Static equilibrium','Intermediate inputs','Government','Armington + CET trade'],
      picture:'standard',
      editableLabels:true,
      labelGroups:{
        goods:{title:'Goods / sectors', defaults:['BRD','MLK']},
        factors:{title:'Primary factors', defaults:['CAP','LAB']}
      },
      institutions:{
        hoh:['Household','HOH'], gov:['Government','GOV'], inv:['Saving / investment','INV'],
        ext:['Rest of world','EXT'], idt:['Indirect tax','IDT'], trf:['Tariff','TRF']
      },
      data:{type:'engine', example:'stdcge', custom:true},
      closure:{kind:'engine', numeraireOptions:['pf','py','pz','pq','pe','pm','pd','epsilon'], walrasOptions:['eqpf','eqpqd'], defaultNumeraire:'pf', defaultWalras:'eqpf'},
      controls:[
        {id:'tauz',name:'Production tax',symbol:'tauz[i]',component:'tauz',target:'good',
          description:'Change the ad valorem production/indirect tax rate on one sector’s gross output.',
          meaning:'This is a tax on production in the selected sector. It is not a consumer VAT and not a tax on labor or capital income.',
          watch:'Watch the selected sector’s producer price and output, then follow intermediate-input demand, factor use, household demand, tax revenue, and spillovers to other sectors.',
          caution:'Rates are model decimals: 0.10 means 10%. A 50% cut to a 10% tax gives 5%, not minus 40 percentage points.',
          unit:'rate',domain:'nonnegative',allowZero:true},
        {id:'taum',name:'Import tariff',symbol:'taum[i]',component:'taum',target:'good',
          description:'Change the ad valorem import tariff on one good in the model’s goods set.',
          meaning:'This changes the border tax paid on imports of the selected good. The first-round effect is on the tariff-inclusive import price; households and firms then substitute between imported and domestic supply through the Armington structure.',
          watch:'Watch imports M, domestic supply D, the composite price pq, domestic production Z, tariff revenue Tm, and welfare.',
          caution:'This is a tariff on imports, not a tax on the domestic sector’s gross output. Rates are decimals: 0.10 means 10%.',
          unit:'rate',domain:'nonnegative',allowZero:true},
        {id:'ff',name:'Factor endowment',symbol:'FF[h]',component:'FF',target:'factor',
          description:'Change the exogenous economy-wide supply/endowment of a primary factor.',
          meaning:'This asks what happens if more or less labor, capital, land, or another modeled factor is available to the whole economy.',
          watch:'Watch the factor price pf[h], sectoral factor demand F[h,i], sector output, household factor income, trade, and welfare.',
          caution:'A +10% labor endowment is not a mechanical +10% employment result. The model is full-employment: wages and sector allocation adjust so the larger supply is absorbed.',
          unit:'quantity',domain:'positive',allowZero:false},
        {id:'sf',name:'Foreign saving',symbol:'Sf',component:'Sf',target:'scalar',
          description:'Change the exogenous foreign-saving term in the savings-driven investment closure.',
          meaning:'Economically, Sf is the external financing/resource-balance term that helps finance domestic investment. Increasing it allows the economy to absorb more resources from abroad under this closure.',
          watch:'Watch investment demand, the exchange rate, imports and exports, domestic absorption, sector output, and welfare.',
          caution:'Do not label this automatically as “FDI.” It is an aggregate foreign-saving/current-account financing variable in this model, not a detailed capital-flow instrument.',
          unit:'quantity',domain:'free',allowZero:true},
        {id:'pwm',name:'World import price',symbol:'pWm[i]',component:'pWm',target:'good',
          description:'Change the exogenous world import price of one good under the small-country assumption.',
          meaning:'This represents a foreign price shock before the domestic exchange-rate and tariff effects are added—for example, a rise in the world price of an imported fuel or material.',
          watch:'Watch the domestic import price pm, imports M, domestic substitution D, composite price pq, sector costs, household demand, and the exchange rate.',
          caution:'The benchmark world price is normalized to 1 in the Hosoe implementation, so a +10% shock normally moves 1.00 to 1.10.',
          unit:'price',domain:'positive',allowZero:false},
        {id:'pwe',name:'World export price',symbol:'pWe[i]',component:'pWe',target:'good',
          description:'Change the exogenous world export price received for one good under the small-country assumption.',
          meaning:'This is a terms-of-trade/export-demand-price opportunity: the foreign-currency price received for exports changes, and producers respond by reallocating output between exports and domestic sales through the CET structure.',
          watch:'Watch exports E, domestic sales D, sector output Z, domestic prices, factor demand and household income.',
          caution:'This is an exogenous world price, not an export-demand curve shift with market power.',
          unit:'price',domain:'positive',allowZero:false}
      ],
      quick:[
        {label:'Abolish tariff',control:'taum',op:'zero'},
        {label:'Cut tariff 50%',control:'taum',op:'pct',amount:-50},
        {label:'Abolish production tax',control:'tauz',op:'zero'},
        {label:'World import price +10%',control:'pwm',op:'pct',amount:10},
        {label:'Foreign saving +10%',control:'sf',op:'pct',amount:10},
        {label:'Labor supply +10%',control:'ff',target:'LAB',op:'pct',amount:10}
      ],
      outputs:[
        ['Sector production','Z[i] gross output and Y[i] value added: identify sector winners, losers, and where the supply response originates.'],
        ['Intermediate use','X[i,j]: how the shock propagates through the input-output network as sectors buy inputs from one another.'],
        ['Factor demand','F[h,i] by factor × sector'],
        ['Household demand','Xp[i]: consumption response after prices, factor income, taxes and saving adjust.'],
        ['Government demand','Xg[i]: model-consistent public purchases by good; not currently a free-form runtime spending knob in StdModelDef.'],
        ['Investment demand','Xv[i]: how total saving is translated into demand for investment goods.'],
        ['Trade','E[i] exports and M[i] imports: external adjustment after relative prices, tariffs and the exchange rate move.'],
        ['Composite supply','Q[i] Armington composite; D[i] domestic sales'],
        ['Prices','pz, pq, pe, pm, pd, py, pf'],
        ['Exchange rate','epsilon: the relative domestic-currency price of foreign exchange that helps clear the external account.'],
        ['Tax revenue','Td, Tz[i], Tm[i]: direct, production-tax and tariff revenue; useful for identifying fiscal feedback from the reform.'],
        ['Saving','Private and government saving are endogenous; Sf is the exogenous foreign-saving term under this closure.'],
        ['Welfare','Utility plus optional equivalent variation (EV), giving a money-metric welfare interpretation at base prices.'],
        ['Comparison','BASE, SIM, difference, % change']
      ]
    },

    ifpri: {
      title:'IFPRI Standard',
      badge:'Validated IFPRI test economy',
      card:'Richer institutions · explicit macro closures · 5 scenarios',
      description:'The IFPRI subsystem is a richer, separate CGE implementation with activities, commodities, factors and institutions, plus explicit macro closure rules. In the current repository, five named policy scenarios are validated against the external IFPRI reference economy.',
      useWhen:'Use this when the fiscal or external closure is itself part of the policy question—for example, whether a tariff cut is absorbed by government saving or by a compensating direct-tax adjustment.',
      avoidWhen:'The Control Room deliberately exposes the five currently validated scenarios rather than pretending the subsystem already has a generic free-form policy editor for every parameter.',
      facts:['5 validated scenarios','Explicit macro closure','Richer institutions','External test.dat'],
      picture:'ifpri',
      editableLabels:false,
      data:{type:'ifpri'},
      closure:{kind:'ifpri'},
      scenarios:[
        {id:'TARCUT1',name:'TARCUT1',title:'Tariff cut — flexible government saving',description:'Cut all benchmark import tariffs by 50%. The fiscal revenue loss is allowed to show up through flexible government saving.',policy:'Policy question: what does trade liberalization do when the government does not replace the lost tariff revenue with a compensating direct-tax increase?',accent:'blue'},
        {id:'TARCUT2',name:'TARCUT2',title:'Tariff cut — direct-tax adjustment',description:'Cut all benchmark import tariffs by 50%, hold government saving fixed, and let a uniform direct-tax-rate adjustment restore the government closure.',policy:'Policy question: what does the same tariff reform do when the government insists on preserving its saving position and replaces the fiscal loss through direct taxation?',accent:'green'},
        {id:'FSAVINCR',name:'FSAVINCR',title:'Foreign saving +10%',description:'Increase the benchmark foreign-saving inflow by 10%.',policy:'Policy question: how does additional external financing change investment, absorption, trade and production under the IFPRI closure?',accent:'violet'},
        {id:'PWMINCR',name:'PWMINCR',title:'World import prices +10%',description:'Increase benchmark world import prices by 10%.',policy:'Policy question: how does a broad adverse import-price shock transmit through domestic prices, substitution, production, institutions and trade?',accent:'gold'},
        {id:'DEVAL',name:'DEVAL',title:'10% devaluation',description:'Fix the exchange rate 10% above benchmark, use DPI as the numeraire, and free CPI and foreign saving.',policy:'Policy question: what new equilibrium is consistent with a 10% weaker domestic currency when the price anchor and external-balance closure are changed accordingly?',accent:'rose'}
      ],
      outputs:[
        ['Activities / commodities','QA, QH and other production/supply quantities'],
        ['Trade','QM imports and QE exports'],
        ['Price system','CPI, DPI, exchange rate and commodity/activity prices'],
        ['Factors','Factor demand and returns'],
        ['Institutions','Household and government incomes, taxes, saving and demand'],
        ['Government closure','GSAV / DTINS depending on scenario'],
        ['External account','FSAV / EXR depending on closure'],
        ['Diagnostics','Termination condition and equation residual'],
        ['Reporting','Scenario − BASE and percent change']
      ]
    },

    camcge: {
      title:'CAMCGE',
      badge:'Cameroon 1987 replication',
      card:'11 sectors · 3 labor groups · 3 published experiments',
      description:'The repository-level CAMCGE implementation reproduces the published Cameroon benchmark and its three policy experiments. Its main role inside CGE-Core is validation: it tests whether the engine can reproduce a historically published multisector CGE model and its counterfactuals.',
      useWhen:'Use this to inspect or rerun the published Cameroon experiments and to validate CGE-Core against an independent historical benchmark.',
      avoidWhen:'Do not treat CAMCGE as the generic interface for a new country policy study unless you intentionally adapt its data, equations, and closure.',
      facts:['11 sectors','3 labor groups','3 experiments','Replication benchmark'],
      picture:'camcge',
      editableLabels:false,
      fixedStructure:{
        sectors:['ag-subsist','ag-exp+ind','sylvicult','ind-alim','biens-cons','biens-int','cim-int','biens-cap','construct','services','publiques'],
        labor:['rural','urban-unsk','urban-skil']
      },
      data:{type:'camcge'},
      closure:{kind:'camcge'},
      scenarios:[
        {id:'exp1',name:'Experiment 1',title:'Oil windfall / foreign saving = 500',description:'Set fsav to 500 and reproduce the published oil-windfall experiment.',policy:'This is a historical replication exercise: a large external resource inflow raises available foreign saving and the model traces the effects on investment, prices, trade, output and real wages.',accent:'violet'},
        {id:'exp2',name:'Experiment 2',title:'Double tariff on food crops',description:'Double tm on ag-subsist.',policy:'This tests whether stronger protection of subsistence-food imports materially changes imports, domestic output and tariff revenue in the published Cameroon structure.',accent:'green'},
        {id:'exp3',name:'Experiment 3',title:'Double tariffs on intermediate goods',description:'Double tariffs on biens-int and cim-int.',policy:'This raises the import cost of intermediate and construction-material goods, so the main mechanism runs through production costs, investment, sector reallocation and real wages.',accent:'gold'}
      ],
      outputs:[
        ['Sector output','xd, xxd and related sector quantities'],
        ['Domestic / composite prices','pd and p by sector'],
        ['Trade','exports e and imports mq'],
        ['Labor prices','wa for rural, urban-unskilled, urban-skilled'],
        ['Investment','dk by sector and aggregate real investment'],
        ['Tax revenue','Tariff revenue and other fiscal quantities'],
        ['Income / saving','y and savings'],
        ['Welfare','omega objective'],
        ['Validation','Published-vs-model regression checks']
      ]
    }
  };


  const WALKTHROUGH = {
    simple:{
      intro:'Start with the smallest possible CGE story. A household owns labor and capital, firms use those factors to produce goods, and prices adjust until what households want to buy equals what firms produce and all factor endowments are employed.',
      notation:[
        ['i','good / sector','An index such as BRD or MLK. In this teaching model, the good and the producing sector use the same label.'],
        ['h','primary factor','An index such as LAB or CAP.'],
        ['0','benchmark suffix','A name ending in 0, such as X0 or F0, is a base-year quantity read from or calibrated to the SAM. It is not a policy shock.'],
        ['p...','price prefix','px, pz and pf are prices. The model determines relative prices; one price is chosen as the numeraire.'],
        ['FF[h]','factor endowment','The exogenous amount of factor h owned by the household and available to the economy.'],
        ['α, β, b','calibrated parameters','Preference share α, factor cost share β, and production scale/TFP b are calibrated from the benchmark.']
      ],
      groups:[
        ['Quantities',[
          ['X[i]','Household consumption','How much of good i the household buys.','Think: final household demand.'],
          ['Z[i]','Sector output','How much good i firms produce.','In equilibrium, goods-market clearing requires household demand and production to be consistent.'],
          ['F[h,i]','Factor input','How much factor h sector i employs.','Examples: labor used by the bread sector, capital used by the milk sector.'],
          ['FF[h]','Factor endowment','Total exogenous supply of factor h.','The economy reallocates this fixed supply across sectors.']
        ]],
        ['Prices',[
          ['px[i]','Demand price','Price paid on the household-demand side for good i.','This is the price entering household demand.'],
          ['pz[i]','Supply price','Price received on the production side for good i.','This is the price entering firms’ factor-demand decisions.'],
          ['pf[h]','Factor price','Price of primary factor h.','For labor, this is the model wage; for capital, the rental/return price.']
        ]],
        ['Calibration parameters',[
          ['alpha[i]','Preference share','Cobb-Douglas household expenditure share for good i.','Higher alpha means the benchmark household places a larger budget share on that good.'],
          ['beta[h,i]','Factor share','Cobb-Douglas cost share of factor h in sector i.','It governs how strongly the sector uses each primary factor.'],
          ['b[i]','Production scale / TFP','Scale parameter of sector i’s production function.','Calibrated so the model reproduces benchmark production.']
        ]]
      ],
      beats:[
        ['Household owns factors','The household begins with FF[h]: its labor, capital, or other primary-factor endowments.'],
        ['Firms hire factors','Each sector chooses F[h,i]. Factor prices pf[h] move until total demand for each factor matches the available FF[h].'],
        ['Firms produce goods','Using those factors, sector i produces Z[i].'],
        ['Household buys goods','Factor income finances household consumption X[i]. The demand price px[i] helps determine how spending is divided.'],
        ['Markets clear','Goods and factor markets must clear simultaneously. The model solves the full set of prices and quantities together.']
      ]
    },

    standard:{
      intro:'The Standard model adds the pieces most policy users expect: intermediate inputs, government, saving and investment, imports, exports, and an exchange rate. The easiest way to read it is to separate quantities, prices, fiscal variables, saving, and exogenous world conditions.',
      notation:[
        ['i','good / sector','The same set indexes producing sectors and goods in this Hosoe model. BRD and MLK are the bundled example labels, not fixed limits.'],
        ['j','using sector','In X[i,j], i is the input good being supplied and j is the sector using it.'],
        ['h','primary factor','Labor, capital, or another factor supplied to production.'],
        ['0','benchmark suffix','Z0, Xp0, M0, etc. are benchmark quantities used for calibration. CGE-Core protects these from in-place SIM edits.'],
        ['p...','price prefix','pf, py, pz, pq, pe, pm and pd are endogenous prices. pWe and pWm are exogenous world prices.'],
        ['tau...','tax-rate prefix','tauz is the production-tax rate; taum is the import-tariff rate; taud is the calibrated direct-tax rate.']
      ],
      groups:[
        ['Production and use',[
          ['Y[i]','Value added / composite factor','Primary factors combined into sector i’s value-added bundle.','Think: the labor-and-capital contribution before intermediate inputs are added.'],
          ['F[h,i]','Primary-factor input','Amount of factor h used by sector i.','Examples: labor in agriculture or capital in manufacturing.'],
          ['X[i,j]','Intermediate input','Amount of good i used as an input by sector j.','This is the model’s input-output propagation channel.'],
          ['Z[i]','Gross sector output','Total output produced by sector i.','It combines value added and required intermediate inputs.'],
          ['Xp[i]','Household consumption','Household purchases of composite good i.','Final private consumption.'],
          ['Xg[i]','Government consumption','Government purchases of composite good i.','A benchmark/endogenous model quantity, not currently a free-form spending shock in StdModelDef.'],
          ['Xv[i]','Investment demand','Purchases of good i for investment.','Total saving is translated into demand for investment goods using calibrated shares.']
        ]],
        ['Trade quantities',[
          ['E[i]','Exports','Quantity of good i sold abroad.','Producers choose between E and D through the CET transformation structure.'],
          ['M[i]','Imports','Quantity of good i purchased from abroad.','Users choose between M and D through the Armington structure.'],
          ['D[i]','Domestic sales','Domestically produced quantity of good i sold in the home market.','The home-market counterpart to exports.'],
          ['Q[i]','Armington composite good','Composite of imports M[i] and domestic supply D[i].','This is the good households, government, investment, and intermediate users actually demand.']
        ]],
        ['Prices',[
          ['pf[h]','Factor price','Price of factor h.','For labor this is the model wage; for capital it is the rental/return price.'],
          ['py[i]','Value-added price','Price of sector i’s composite primary-factor bundle Y[i].','It is the unit value/cost of the value-added component of production.'],
          ['pz[i]','Gross-output / supply price','Supply price associated with gross output Z[i].','This price links production, taxes, exports, and domestic sales.'],
          ['pq[i]','Composite-good price','Price of Armington composite Q[i].','This is the domestic user price of the import-plus-domestic composite before specific final-demand allocation.'],
          ['pe[i]','Export price in local currency','Domestic-currency price received for exports E[i].','It equals the exogenous world export price translated through the exchange rate.'],
          ['pm[i]','Import price in local currency','Domestic-currency price of imported good i.','It reflects the world import price, exchange rate, and tariff wedge.'],
          ['pd[i]','Domestic-good price','Price of domestically produced good i sold at home.','It is the price on the D[i] branch of both CET supply and Armington demand.'],
          ['epsilon','Exchange rate','Domestic-currency price of foreign exchange in the model.','It connects world prices and the domestic price system and helps clear the external account.']
        ]],
        ['Saving and external balance',[
          ['Sp','Private saving','Household saving generated from factor income.','Part of total resources available for investment.'],
          ['Sg','Government saving','Government saving generated from tax revenue.','A fiscal surplus/saving channel feeding investment.'],
          ['Sf','Foreign saving','Exogenous foreign-resource inflow used in the savings-driven investment closure.','Think current-account financing, not automatically FDI.']
        ]],
        ['Taxes and tax revenue',[
          ['tauz[i]','Production-tax rate','Ad valorem tax rate on sector i’s gross output.','This is the policy rate you can shock.'],
          ['taum[i]','Import-tariff rate','Ad valorem tariff rate on imports of good i.','This is the policy rate you can shock.'],
          ['taud','Direct-tax rate','Flat direct tax rate on household factor income.','Calibrated from the SAM and not exposed as a mutable SIM policy control in current StdModelDef.'],
          ['Tz[i]','Production-tax revenue','Revenue raised from tauz[i].','Endogenous fiscal result after output changes.'],
          ['Tm[i]','Tariff revenue','Revenue raised from taum[i].','Endogenous fiscal result after imports change.'],
          ['Td','Direct-tax revenue','Revenue from the calibrated direct tax.','Changes endogenously with household factor income.']
        ]],
        ['World conditions and technology',[
          ['pWe[i]','World export price','Exogenous foreign-currency export price, normalized to 1 in the benchmark.','Small-country assumption: the country takes this price as given.'],
          ['pWm[i]','World import price','Exogenous foreign-currency import price, normalized to 1 in the benchmark.','A natural place to impose an external commodity-price shock.'],
          ['sigma[i]','Armington elasticity','Ease of substitution between imports and domestic goods.','Currently fixed at 2 in StdModelDef.'],
          ['psi[i]','CET elasticity','Ease of transforming output between exports and domestic sales.','Currently fixed at 2 in StdModelDef.'],
          ['ax[i,j]','Intermediate input coefficient','Units of input good i required per unit of output in sector j.','Calibrated Leontief input-output coefficient.'],
          ['ay[i]','Value-added coefficient','Units of value added required per unit of gross output in sector i.','Calibrated production requirement.']
        ]]
      ],
      beats:[
        ['Firms assemble gross output','Sector i combines primary-factor value added Y[i] with intermediate inputs X[·,i] to produce Z[i].'],
        ['Producers choose where output goes','Gross output is transformed between exports E[i] and domestic sales D[i]. Relative prices pe and pd influence this allocation.'],
        ['Domestic users choose where supply comes from','Imports M[i] and domestic sales D[i] are combined into the Armington composite Q[i]. Relative prices pm and pd determine the mix.'],
        ['The composite good is absorbed','Q[i] is demanded by households Xp[i], government Xg[i], investment Xv[i], and other sectors as intermediate input X[i,j].'],
        ['Factor markets transmit incidence','Changes in sector production alter F[h,i]. Factor prices pf[h] adjust so aggregate factor demand matches exogenous endowments FF[h].'],
        ['Fiscal accounts feed saving and demand','Production taxes, tariffs, and direct taxes produce Tz, Tm, and Td. Government demand and saving respond according to the calibrated model structure.'],
        ['The external account closes','World prices pWm/pWe, the exchange rate epsilon, trade quantities, and exogenous foreign saving Sf must jointly satisfy the balance-of-payments condition.'],
        ['Everything clears together','A tariff or price shock is not solved sector-by-sector. The model finds one set of prices and quantities satisfying all equations simultaneously.']
      ]
    },

    ifpri:{
      intro:'The IFPRI model is larger and uses a richer accounting language than the Hosoe examples. Rather than memorizing every symbol, first learn the main blocks: activities produce commodities, factors earn income, institutions receive and spend income, government collects taxes, and the macro closure decides which aggregates are fixed or allowed to adjust.',
      notation:[
        ['A','activities','Producing activities. Unlike the Hosoe Standard model, activities and commodities are separate concepts.'],
        ['C','commodities','Goods and services that can be produced, consumed, traded, or used as inputs.'],
        ['F','factors','Labor, capital, or other primary factors.'],
        ['INS','institutions','Households, enterprises, government, and related institutional accounts.'],
        ['Q...','quantity prefix','Many IFPRI quantity variables begin with Q: QA, QE, QM, QH, QG, QINV, etc.'],
        ['P...','price prefix','Many price variables begin with P: PA, PE, PM, PQ, CPI, DPI, and others.']
      ],
      groups:[
        ['Core quantities',[
          ['QA[a]','Activity level','Scale of production activity a.','The activity side of production.'],
          ['QX[c]','Commodity output','Supply of commodity c.','Activities can map into commodities rather than being identical to them.'],
          ['QM[c]','Imports','Imported quantity of commodity c.','Trade response on the import side.'],
          ['QE[c]','Exports','Exported quantity of commodity c.','Trade response on the export side.'],
          ['QH[c,h]','Household consumption','Commodity c consumed by household h.','Distributional demand can be more explicit than in the Hosoe representative-household model.'],
          ['QG[c]','Government demand','Government consumption of commodity c.','Part of the government account and macro closure.'],
          ['QINV[c]','Investment demand','Commodity demand for investment.','Links saving and the investment account.']
        ]],
        ['Prices and macro variables',[
          ['PA[a]','Activity price','Price/value associated with activity output.','Production-side price signal.'],
          ['PQ[c]','Composite commodity price','Domestic user price of composite commodity c.','A key price for household, government, investment, and intermediate demand.'],
          ['PM[c]','Import price','Domestic-currency price of imports.','Reflects world prices and exchange-rate conditions.'],
          ['PE[c]','Export price','Domestic-currency export price.','Connects foreign prices and domestic production decisions.'],
          ['CPI','Consumer price index','Consumer-side nominal price anchor in the BASE closure.','BASE fixes CPI as numeraire.'],
          ['DPI','Domestic producer price index','Alternative aggregate price index.','DEVAL uses DPI as numeraire instead of CPI.'],
          ['EXR','Exchange rate','Domestic-currency price of foreign exchange.','DEVAL fixes EXR 10% above benchmark.'],
          ['FSAV','Foreign saving','External financing/resource-balance term.','Fixed in BASE; freed in the DEVAL closure.']
        ]],
        ['Closure variables',[
          ['GSAV','Government saving','Government fiscal saving balance.','Flexible in some scenarios and fixed in TARCUT2.'],
          ['DTINS','Direct-tax adjustment','Uniform direct-tax-rate adjustment variable.','Becomes endogenous in TARCUT2 to preserve government saving.'],
          ['IADJ','Investment scaling','Macro adjustment factor for investment demand.','Fixed in the validated BASE closure.'],
          ['GADJ','Government-demand scaling','Macro adjustment factor for government demand.','Fixed in the validated BASE closure.'],
          ['WALRAS','Walras residual','Residual associated with the model’s Walras condition.','The official NLP minimizes its square rather than fixing WALRAS directly.']
        ]]
      ],
      beats:[
        ['Activities produce commodities','The model separates production activities from commodities, allowing a more flexible SAM structure.'],
        ['Factors generate incomes','Activities demand factors; factor returns feed institutional incomes.'],
        ['Institutions spend and save','Households, government, and other institutions allocate income to consumption, taxes, transfers, and saving.'],
        ['Trade connects domestic and world markets','Imports, exports, world prices, and EXR determine how external shocks enter domestic prices and quantities.'],
        ['Macro closure answers “who adjusts?”','CPI, DPI, FSAV, GSAV, DTINS, IADJ, and GADJ determine which aggregate balance is held fixed and which variable bears the adjustment.'],
        ['Policy simulations are closure-specific','TARCUT1 and TARCUT2 can impose the same tariff cut but produce different incidence because the fiscal adjustment mechanism differs.']
      ]
    },

    camcge:{
      intro:'CAMCGE uses the notation of the published Cameroon model. The Control Room keeps this model primarily as a replication benchmark, so the most useful reading strategy is to identify sector output, domestic/composite prices, trade, labor prices, investment, and the external-balance closure.',
      notation:[
        ['i','sector','One of 11 published Cameroon sectors.'],
        ['it','tradable sector','Subset of sectors with trade variables.'],
        ['lc','labor category','Rural, urban unskilled, or urban skilled labor.'],
        ['x / xd / xxd','output-family variables','Published model distinguishes related production/output concepts; the replication reports these separately.'],
        ['p...','price prefix','Variables such as p, pd, pva, pwm and pwe are different price concepts in the published model.'],
        ['fsav','foreign saving','External saving/resource inflow used in the published closure and experiments.']
      ],
      groups:[
        ['Production and prices',[
          ['x[i]','Sector production variable','Published sector production quantity.','One of the main reported base-equilibrium quantities.'],
          ['xd[i]','Domestic sector output','Domestic output measure used heavily in experiment comparisons.','The regression scripts report percentage changes in xd.'],
          ['xxd[i]','Related domestic production quantity','Additional production quantity in the published formulation.','Retained to reproduce the original model exactly.'],
          ['p[i]','Composite / market price','Sector price measure in the published model.','Reported alongside pd in the experiments.'],
          ['pd[i]','Domestic price','Domestic-sector price.','A key incidence variable in tariff experiments.'],
          ['pva[i]','Value-added price','Price of sector value added.','Connects production and factor returns.']
        ]],
        ['Trade and external balance',[
          ['e[i]','Exports','Exports for tradable sectors.','Respond to relative domestic and world prices.'],
          ['mq[i]','Imports','Imports for tradable sectors.','Experiment 2 focuses especially on food-crop imports.'],
          ['pwm[i]','World import price','Exogenous import-price term.','Foreign-price component of import valuation.'],
          ['pwe[i]','World export price','Exogenous export-price term.','Foreign-price component of export valuation.'],
          ['fsav','Foreign saving','External resource/saving term.','Experiment 1 sets fsav to 500.']
        ]],
        ['Labor and investment',[
          ['wa[lc]','Labor price / wage','Wage for each published labor category.','The replication reports real-wage effects by rural, urban-unskilled, and urban-skilled labor.'],
          ['dk[i]','Investment by sector','Sectoral investment allocation.','Important in the intermediate-tariff experiment.'],
          ['inv_real','Real investment','Aggregate real investment measure.','Reported as an experiment outcome.']
        ]]
      ],
      beats:[
        ['Start from the published base equilibrium','CGE-Core first reproduces the paper’s reported levels, prices, wages, and accounting balances.'],
        ['Keep the published closure','The replication fixes mps and drops caeq exactly as required by the benchmark implementation.'],
        ['Apply one published experiment','Foreign saving or tariffs are changed exactly as in the paper.'],
        ['Resolve the whole economy','Sector output, prices, trade, labor returns, investment, and tax revenue adjust simultaneously.'],
        ['Compare against published targets','The regression scripts test whether CGE-Core reproduces the reported percentage changes within tolerance.']
      ]
    }
  };

  const state = {
    model:'simple',
    labels:{},
    dataSource:{mode:'example', customPath:'my_data_dir', ifpriPath:'', solver:'auto'},
    closure:{},
    stack:[]
  };

  MODEL_ORDER.forEach(modelId => {
    const model = MODELS[modelId];
    if(model.editableLabels){
      state.labels[modelId] = {};
      Object.entries(model.labelGroups).forEach(([key,group]) => {
        state.labels[modelId][key] = group.defaults.map(label => ({label,active:true}));
      });
    }
  });

  function saveLocal(){
    try{
      localStorage.setItem('cge-control-room-state', JSON.stringify({
        model:state.model, labels:state.labels, dataSource:state.dataSource, closure:state.closure,
        accounts:state.accounts||null, simpleAccount:state.simpleAccount||null
      }));
    }catch(e){}
  }
  function loadLocal(){
    try{
      const saved=JSON.parse(localStorage.getItem('cge-control-room-state')||'null');
      if(!saved) return;
      if(MODELS[saved.model]) state.model=saved.model;
      if(saved.labels) state.labels={...state.labels,...saved.labels};
      if(saved.dataSource) state.dataSource={...state.dataSource,...saved.dataSource};
      if(saved.closure) state.closure=saved.closure;
      if(saved.accounts) state.accounts=saved.accounts;
      if(saved.simpleAccount) state.simpleAccount=saved.simpleAccount;
    }catch(e){}
  }

  function model(){ return MODELS[state.model]; }
  function activeLabels(group){
    return ((state.labels[state.model]||{})[group]||[]).filter(x=>x.active).map(x=>x.label);
  }
  function firstLabel(group, fallback=''){
    return activeLabels(group)[0] || fallback;
  }

  function renderModelCards(){
    $('modelCards').innerHTML = MODEL_ORDER.map((id,i)=>{
      const m=MODELS[id];
      return `<button type="button" class="model-card ${id===state.model?'active':''}" data-model="${id}">
        <div class="model-number">0${i+1}</div>
        <strong>${esc(m.title)}</strong>
        <p>${esc(m.card)}</p>
      </button>`;
    }).join('');
    document.querySelectorAll('[data-model]').forEach(btn=>{
      btn.addEventListener('click',()=>{
        if(state.model===btn.dataset.model) return;
        state.model=btn.dataset.model;
        state.stack=[];
        ensureClosureDefaults();
        saveLocal();
        renderAll();
      });
    });
  }

  function renderOverview(){
    const m=model();
    $('modelBadge').textContent=m.badge;
    $('modelTitle').textContent=m.title;
    $('modelDescription').textContent=m.description;
    $('modelPolicyUse').innerHTML=`<div class="policy-use-box"><strong>Good for</strong><p>${esc(m.useWhen)}</p></div><div class="policy-use-box"><strong>Not designed for</strong><p>${esc(m.avoidWhen)}</p></div>`;
    $('modelFacts').innerHTML=m.facts.map(x=>`<span class="fact">${esc(x)}</span>`).join('')+`<span class="audit-badge">✓ logic checked</span>`;
    $('economyPicture').innerHTML=diagramFor(state.model);
  }

  function diagramFor(id){
    const base = `viewBox="0 0 720 270" role="img" aria-label="${esc(MODELS[id].title)} economy diagram"`;
    const arrow = `<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="var(--muted)"/></marker></defs>`;
    const node=(x,y,w,h,title,sub,fill='var(--blue-soft)',stroke='var(--blue)')=>`
      <g><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="14" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>
      <text x="${x+w/2}" y="${y+25}" text-anchor="middle" fill="var(--text)" font-size="14" font-weight="800">${title}</text>
      <text x="${x+w/2}" y="${y+43}" text-anchor="middle" fill="var(--muted)" font-size="11">${sub}</text></g>`;
    const line=(x1,y1,x2,y2)=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="var(--muted)" stroke-width="1.6" marker-end="url(#a)"/>`;

    if(id==='simple'){
      return `<svg ${base}>${arrow}
        ${node(55,95,150,70,'Household','consumes goods','var(--green-soft)','var(--green)')}
        ${node(515,95,150,70,'Firms','produce BRD / MLK','var(--blue-soft)','var(--blue)')}
        ${node(285,25,150,62,'Goods market','X = Z','var(--gold-soft)','var(--gold)')}
        ${node(285,183,150,62,'Factor market','CAP + LAB','var(--violet-soft)','var(--violet)')}
        ${line(205,112,285,70)} ${line(435,70,515,112)}
        ${line(515,150,435,212)} ${line(285,212,205,150)}
        <text x="360" y="137" text-anchor="middle" fill="var(--muted)" font-size="12">relative prices clear both markets</text>
      </svg>`;
    }
    if(id==='standard'){
      return `<svg ${base}>${arrow}
        ${node(275,94,170,76,'Firms & sectors','factors + intermediates','var(--blue-soft)','var(--blue)')}
        ${node(30,28,145,62,'Household','consumption + saving','var(--green-soft)','var(--green)')}
        ${node(30,180,145,62,'Government','taxes + demand','var(--gold-soft)','var(--gold)')}
        ${node(545,28,145,62,'Rest of world','imports + exports','var(--violet-soft)','var(--violet)')}
        ${node(545,180,145,62,'Investment','saving → demand','var(--rose-soft)','var(--rose)')}
        ${line(175,58,275,108)} ${line(175,211,275,146)}
        ${line(445,108,545,58)} ${line(445,146,545,211)}
        ${line(360,94,360,58)} ${line(360,170,360,210)}
        <text x="360" y="36" text-anchor="middle" fill="var(--muted)" font-size="11">factor & goods markets</text>
        <text x="360" y="235" text-anchor="middle" fill="var(--muted)" font-size="11">saving / investment balance</text>
      </svg>`;
    }
    if(id==='ifpri'){
      return `<svg ${base}>${arrow}
        ${node(270,93,180,76,'Activities','production','var(--blue-soft)','var(--blue)')}
        ${node(55,92,150,76,'Institutions','households + govt','var(--green-soft)','var(--green)')}
        ${node(515,92,150,76,'Commodities','domestic + trade','var(--violet-soft)','var(--violet)')}
        ${node(270,18,180,52,'Factors','labor / capital','var(--gold-soft)','var(--gold)')}
        ${node(270,197,180,52,'Macro closure','CPI · FSAV · GSAV · EXR','var(--rose-soft)','var(--rose)')}
        ${line(205,130,270,130)} ${line(450,130,515,130)} ${line(360,70,360,93)} ${line(360,169,360,197)}
        <text x="360" y="263" text-anchor="middle" fill="var(--muted)" font-size="11">named policy scenarios alter shocks + closures together</text>
      </svg>`;
    }
    return `<svg ${base}>${arrow}
      ${node(270,92,180,76,'CAMCGE','Cameroon benchmark','var(--blue-soft)','var(--blue)')}
      ${node(25,28,155,62,'11 sectors','agriculture → services','var(--green-soft)','var(--green)')}
      ${node(25,180,155,62,'3 labor groups','rural · unsk · skilled','var(--gold-soft)','var(--gold)')}
      ${node(540,28,155,62,'Trade','9 tradable sectors','var(--violet-soft)','var(--violet)')}
      ${node(540,180,155,62,'3 experiments','published regressions','var(--rose-soft)','var(--rose)')}
      ${line(180,58,270,108)} ${line(180,211,270,146)} ${line(450,108,540,58)} ${line(450,146,540,211)}
      <text x="360" y="250" text-anchor="middle" fill="var(--muted)" font-size="11">replication benchmark: preserve the published closure</text>
    </svg>`;
  }


  function renderWalkthrough(){
    const w=WALKTHROUGH[state.model];
    $('walkthroughIntro').textContent=w.intro;
    $('variableGlossaryTitle').textContent=`${model().title}: variable reference`;
    $('variableGlossaryIntro').textContent='These are the symbols you will see in equations, generated scripts, and result tables. Read the plain-language line first; the symbol is there so you can connect the interface back to the model code.';

    $('notationPrimer').innerHTML=w.notation.map(x=>`
      <div class="notation-card"><div class="notation-symbol">${esc(x[0])}</div>
      <strong>${esc(x[1])}</strong><p>${esc(x[2])}</p></div>`).join('');

    $('variableGlossary').innerHTML=w.groups.map((g,gi)=>`
      <section class="variable-group" id="variable-group-${gi}">
        <h4>${esc(g[0])}</h4>
        <div class="variable-grid">${g[1].map(v=>`
          <article class="variable-card">
            <div class="variable-head"><span class="variable-symbol">${esc(v[0])}</span><span class="variable-name">${esc(v[1])}</span></div>
            <p>${esc(v[2])}</p><div class="plain">${esc(v[3])}</div>
          </article>`).join('')}</div>
      </section>`).join('');

    $('flowStoryTitle').textContent=`How the ${model().title} economy moves`;
    $('flowStory').innerHTML=w.beats.map((b,i)=>`
      <div class="story-beat"><div class="story-beat-num">${i+1}</div>
      <div><strong>${esc(b[0])}</strong><p>${esc(b[1])}</p></div></div>`).join('');

    const navItems=[
      ['notationPrimer','Notation'],
      ['variableGlossary','Variables'],
      ['flowStory','Economic flow']
    ];
    $('storyNav').innerHTML=navItems.map((x,i)=>`<button type="button" data-story-target="${x[0]}" class="${i===0?'active':''}">${esc(x[1])}</button>`).join('');
    document.querySelectorAll('[data-story-target]').forEach(btn=>btn.addEventListener('click',()=>{
      document.querySelectorAll('[data-story-target]').forEach(x=>x.classList.toggle('active',x===btn));
      $(btn.dataset.storyTarget).scrollIntoView({behavior:'smooth',block:'center'});
    }));
  }

  function renderEconomy(){
    const m=model();
    $('economyIntro').textContent = m.editableLabels
      ? 'Manage the labels used by the scenario selectors. Check or uncheck labels, remove them, or add new ones.'
      : state.model==='ifpri'
        ? 'The IFPRI economy structure is loaded from the external test.dat at runtime, so this interface does not invent sector labels.'
        : 'CAMCGE uses its fixed published Cameroon benchmark structure.';
    $('labelsTitle').textContent = m.editableLabels ? 'Scenario target labels' : 'Benchmark structure';
    $('resetLabelsBtn').classList.toggle('hidden', !m.editableLabels);

    if(m.editableLabels){
      $('labelManagers').innerHTML = Object.entries(m.labelGroups).map(([key,g]) => labelManagerHtml(key,g.title)).join('');
      bindLabelManagers();
      $('labelsNote').textContent='These lists drive the dropdowns and generated code. They do not rewrite your SAM; a custom dataset must contain the same active labels.';
      $('economyStatus').textContent = hasRequiredLabels() ? 'Labels ready' : 'Add an active label';
      $('economyStatus').className='status-pill '+(hasRequiredLabels()?'ok':'warn');
    }else if(state.model==='ifpri'){
      $('labelManagers').innerHTML = `
        <div class="label-group">
          <div class="label-group-head"><strong>Loaded from test.dat</strong><span class="fact">runtime dataset</span></div>
          <div class="label-list">
            <span class="label-chip">Activities</span><span class="label-chip">Commodities</span>
            <span class="label-chip">Factors</span><span class="label-chip">Institutions</span>
          </div>
        </div>`;
      $('labelsNote').textContent='CGE-Core validates the dataset sets, SAM membership and balance, elasticities, factor quantities and tax mappings before solving.';
      $('economyStatus').textContent='Dataset-defined';
      $('economyStatus').className='status-pill ok';
    }else{
      const s=m.fixedStructure;
      $('labelManagers').innerHTML = `
        <div class="label-group">
          <div class="label-group-head"><strong>11 published sectors</strong><span class="fact">fixed benchmark</span></div>
          <div class="label-list">${s.sectors.map(x=>`<span class="label-chip">${esc(x)}</span>`).join('')}</div>
        </div>
        <div class="label-group">
          <div class="label-group-head"><strong>Labor categories</strong><span class="fact">fixed benchmark</span></div>
          <div class="label-list">${s.labor.map(x=>`<span class="label-chip">${esc(x)}</span>`).join('')}</div>
        </div>`;
      $('labelsNote').textContent='These labels are part of the published CAMCGE replication and are not editable in the control room.';
      $('economyStatus').textContent='Benchmark fixed';
      $('economyStatus').className='status-pill ok';
    }

    renderDataSource();
  }

  function labelManagerHtml(key,title){
    const items=(state.labels[state.model]||{})[key]||[];
    return `<div class="label-group" data-label-group="${key}">
      <div class="label-group-head"><strong>${esc(title)}</strong><span class="count">${items.filter(x=>x.active).length} active</span></div>
      <div class="label-list">
        ${items.map((item,i)=>`<span class="label-chip ${item.active?'':'inactive'}">
          <input type="checkbox" data-label-toggle="${key}:${i}" ${item.active?'checked':''} aria-label="Use ${esc(item.label)}">
          <span>${esc(item.label)}</span>
          <button type="button" class="icon-button" data-label-remove="${key}:${i}" aria-label="Remove ${esc(item.label)}">×</button>
        </span>`).join('')}
      </div>
      <div class="add-row">
        <input class="text-input" data-label-input="${key}" placeholder="Add ${esc(title.toLowerCase())} label">
        <button type="button" class="button small ghost" data-label-add="${key}">Add</button>
      </div>
    </div>`;
  }

  function bindLabelManagers(){
    document.querySelectorAll('[data-label-toggle]').forEach(el=>{
      el.addEventListener('change',()=>{
        const [group,index]=el.dataset.labelToggle.split(':');
        state.labels[state.model][group][Number(index)].active=el.checked;
        saveLocal(); renderEconomy(); renderClosure(); renderScenario();
      });
    });
    document.querySelectorAll('[data-label-remove]').forEach(el=>{
      el.addEventListener('click',()=>{
        const [group,index]=el.dataset.labelRemove.split(':');
        state.labels[state.model][group].splice(Number(index),1);
        saveLocal(); renderEconomy(); renderClosure(); renderScenario();
      });
    });
    document.querySelectorAll('[data-label-add]').forEach(el=>{
      el.addEventListener('click',()=>{
        const group=el.dataset.labelAdd;
        const input=document.querySelector(`[data-label-input="${group}"]`);
        const value=input.value.trim();
        if(!value) return;
        if(!state.labels[state.model][group].some(x=>x.label===value)){
          state.labels[state.model][group].push({label:value,active:true});
        }
        input.value=''; saveLocal(); renderEconomy(); renderClosure(); renderScenario();
      });
    });
  }

  function hasRequiredLabels(){
    const m=model();
    if(!m.editableLabels) return true;
    return Object.keys(m.labelGroups).every(k => activeLabels(k).length>0);
  }

  function resetLabels(){
    const m=model();
    if(!m.editableLabels) return;
    state.labels[state.model]={};
    Object.entries(m.labelGroups).forEach(([key,g])=>{
      state.labels[state.model][key]=g.defaults.map(label=>({label,active:true}));
    });
    saveLocal(); renderEconomy(); ensureClosureDefaults(); renderClosure(); renderScenario();
  }

  function renderDataSource(){
    const m=model();
    const panel=$('dataSourcePanel');
    if(m.data.type==='engine'){
      panel.innerHTML=`
        <div class="data-choice">
          <button type="button" class="choice-card ${state.dataSource.mode==='example'?'active':''}" data-data-mode="example">
            <strong>Bundled ${esc(m.data.example)} example</strong><span>Uses cge_core.example_data()</span>
          </button>
          <button type="button" class="choice-card ${state.dataSource.mode==='custom'?'active':''}" data-data-mode="custom">
            <strong>Custom dataset directory</strong><span>Use your SAM-derived CSV directory</span>
          </button>
        </div>
        <div class="form-grid">
          <div class="form-field ${state.dataSource.mode==='custom'?'':'hidden'}">
            <label for="customDataPath">Data directory</label>
            <input id="customDataPath" class="text-input" value="${esc(state.dataSource.customPath)}" placeholder="my_data_dir">
          </div>
          <div class="form-field">
            <label for="solverSelect">Solver</label>
            ${solverSelectHtml()}
          </div>
        </div>
        ${state.model==='standard'?institutionMappingHtml():simpleInstitutionHtml()}
      `;
      document.querySelectorAll('[data-data-mode]').forEach(btn=>btn.addEventListener('click',()=>{
        state.dataSource.mode=btn.dataset.dataMode;saveLocal();renderDataSource();generateAndRenderCode();
      }));
      const path=$('customDataPath'); if(path) path.addEventListener('input',()=>{state.dataSource.customPath=path.value;saveLocal();generateAndRenderCode()});
      bindSolver();
      bindAccountMapping();
    }else if(m.data.type==='ifpri'){
      panel.innerHTML=`
        <div class="notice-like">
          The official IFPRI <code>test.dat</code> remains external to CGE-Core. Point the generated script to the folder that contains it.
        </div>
        <div class="form-grid">
          <div class="form-field">
            <label for="ifpriPath">IFPRI_SOURCE_DIR</label>
            <input id="ifpriPath" class="text-input" value="${esc(state.dataSource.ifpriPath)}" placeholder="C:\\path\\to\\ifpri-test-folder">
          </div>
          <div class="form-field">
            <label for="solverSelect">Solver</label>${solverSelectHtml()}
          </div>
        </div>`;
      $('ifpriPath').addEventListener('input',()=>{state.dataSource.ifpriPath=$('ifpriPath').value;saveLocal();generateAndRenderCode()});
      bindSolver();
    }else{
      panel.innerHTML=`
        <div class="notice-like">
          CAMCGE uses the repository's fixed <code>cam/data</code> benchmark generated from the published source tables.
        </div>
        <div class="form-grid">
          <div class="form-field"><label for="solverSelect">Solver</label>${solverSelectHtml(false)}</div>
        </div>`;
      bindSolver();
    }
  }

  function solverSelectHtml(allowAuto=true){
    return `<select id="solverSelect" class="select">
      ${allowAuto?'<option value="auto">Auto-detect</option>':''}
      <option value="cyipopt">cyipopt</option><option value="ipopt">ipopt</option>
    </select>`.replace(`value="${esc(state.dataSource.solver)}"`,`value="${esc(state.dataSource.solver)}"`);
  }
  function bindSolver(){
    const s=$('solverSelect');
    if(!s) return;
    if([...s.options].some(o=>o.value===state.dataSource.solver)) s.value=state.dataSource.solver;
    else { state.dataSource.solver=s.options[0].value; s.value=state.dataSource.solver; }
    s.addEventListener('change',()=>{state.dataSource.solver=s.value;saveLocal();generateAndRenderCode()});
  }

  function institutionMappingHtml(){
    if(!state.accounts) state.accounts={hoh:'HOH',gov:'GOV',inv:'INV',ext:'EXT',idt:'IDT',trf:'TRF'};
    const roles={hoh:'Household',gov:'Government',inv:'Saving / investment',ext:'Rest of world',idt:'Indirect tax',trf:'Tariff'};
    return `<details class="advanced"><summary>Institution account labels</summary>
      <div class="form-grid">${Object.entries(roles).map(([k,label])=>`
        <div class="form-field"><label>${label}</label><input class="text-input" data-account="${k}" value="${esc(state.accounts[k]||'')}"></div>`).join('')}
      </div><p class="help">Only change these if your custom SAM uses different institutional account names.</p>
    </details>`;
  }
  function simpleInstitutionHtml(){
    if(!state.simpleAccount) state.simpleAccount='HOH';
    return `<details class="advanced"><summary>Household account label</summary>
      <div class="form-grid"><div class="form-field"><label>Household account</label>
      <input class="text-input" data-simple-account value="${esc(state.simpleAccount)}"></div></div>
      <p class="help">Change only if a custom simple-model SAM uses a different household label.</p>
    </details>`;
  }
  function bindAccountMapping(){
    document.querySelectorAll('[data-account]').forEach(el=>el.addEventListener('input',()=>{
      state.accounts[el.dataset.account]=el.value.trim();saveLocal();generateAndRenderCode();
    }));
    const s=document.querySelector('[data-simple-account]');
    if(s) s.addEventListener('input',()=>{state.simpleAccount=s.value.trim();saveLocal();generateAndRenderCode()});
  }

  function ensureClosureDefaults(){
    const m=model();
    if(m.closure.kind!=='engine') return;
    const c=state.closure[state.model] || {};
    if(!m.closure.numeraireOptions.includes(c.numeraireVar)) c.numeraireVar=m.closure.defaultNumeraire;
    if(!m.closure.walrasOptions.includes(c.walrasEq)) c.walrasEq=m.closure.defaultWalras;

    const validNum = c.numeraireVar==='epsilon'
      ? ['']
      : (c.numeraireVar==='pf' ? activeLabels('factors')
         : activeLabels('goods'));
    if(!validNum.includes(c.numeraireIndex)) c.numeraireIndex=defaultIndexForNumeraire(c.numeraireVar);

    const validWal = c.walrasEq==='eqpf' ? activeLabels('factors') : activeLabels('goods');
    if(!validWal.includes(c.walrasIndex)) c.walrasIndex=defaultIndexForWalras(c.walrasEq);
    state.closure[state.model]=c;
  }

  function defaultIndexForNumeraire(v){
    if(v==='pf') return activeLabels('factors').includes('LAB')?'LAB':firstLabel('factors');
    if(v==='epsilon') return '';
    return firstLabel('goods');
  }
  function defaultIndexForWalras(v){
    return v==='eqpf' ? (activeLabels('factors').includes('LAB')?'LAB':firstLabel('factors')) : firstLabel('goods');
  }

  function renderClosure(){
    const m=model();
    if(m.closure.kind==='engine'){
      ensureClosureDefaults();
      const c=state.closure[state.model];
      $('closureIntro').textContent='A CGE counterfactual is not defined by a shock alone. First pin down the price numeraire and remove one Walras-law redundant market equation.';
      $('closurePanel').innerHTML=`
        <div class="closure-map">
          <div class="closure-box">
            <div class="mini-label">Price anchor</div><h3>Numeraire</h3>
            <div class="form-grid">
              <div class="form-field"><label>Variable</label><select id="numeraireVar" class="select">
                ${m.closure.numeraireOptions.map(x=>`<option ${x===c.numeraireVar?'selected':''}>${x}</option>`).join('')}
              </select></div>
              <div class="form-field" id="numeraireIndexField"><label>Index</label><select id="numeraireIndex" class="select"></select></div>
            </div>
          </div>
          <div class="closure-arrow">+</div>
          <div class="closure-box">
            <div class="mini-label">Walras' law</div><h3>Redundant market equation</h3>
            <div class="form-grid">
              <div class="form-field"><label>Equation</label><select id="walrasEq" class="select">
                ${m.closure.walrasOptions.map(x=>`<option ${x===c.walrasEq?'selected':''}>${x}</option>`).join('')}
              </select></div>
              <div class="form-field"><label>Index</label><select id="walrasIndex" class="select"></select></div>
            </div>
          </div>
        </div>
        <div class="closure-summary">Target: a square BASE system with degrees of freedom = 0 before calibration.</div>
        <div class="closure-explainer">
          <div><strong>What the numeraire does</strong><p>A CGE model determines relative prices, not an absolute price level. Fixing one price simply chooses the unit in which all other prices are quoted. A sensible change of numeraire should not change real quantities or welfare.</p></div>
          <div><strong>Why one equation is dropped</strong><p>Walras’ law makes one market-clearing condition redundant once the rest of the system and the budget identities hold. Dropping it does not mean that market is ignored; CGE-Core checks the resulting system has zero degrees of freedom, and the omitted market should clear at the solution.</p></div>
        </div>`;
      bindClosureInputs();
      $('closureStatus').textContent=closureReady()?'Closure ready':'Choose active labels';
      $('closureStatus').className='status-pill '+(closureReady()?'ok':'warn');
    }else if(m.closure.kind==='ifpri'){
      $('closureIntro').textContent='IFPRI scenarios carry their macro closure with them. The closure changes when the economic experiment requires it.';
      $('closurePanel').innerHTML=`
        <div class="closure-map">
          <div class="closure-box"><div class="mini-label">BASE</div><h3>CPI numeraire</h3><p class="help">Foreign saving, investment scaling and government-demand scaling are fixed with the recorded factor closures.</p></div>
          <div class="closure-arrow">→</div>
          <div class="closure-box"><div class="mini-label">Scenario-specific</div><h3>Closure may switch</h3><p class="help"><strong>TARCUT2:</strong> government saving fixed, DTINS endogenous. <strong>DEVAL:</strong> DPI numeraire, EXR fixed, CPI and FSAV free.</p></div>
        </div>
        <div class="closure-explainer">
          <div><strong>Why this matters for policy</strong><p>The same tariff cut can have different economy-wide consequences depending on who ultimately absorbs the lost government revenue. IFPRI makes that financing assumption explicit instead of hiding it.</p></div>
          <div><strong>External closure</strong><p>A devaluation experiment also requires a consistent rule for the domestic price anchor and foreign saving. Otherwise “change the exchange rate” is not a complete general-equilibrium experiment.</p></div>
        </div>`;
      $('closureStatus').textContent='Built into scenarios';$('closureStatus').className='status-pill ok';
    }else{
      $('closureIntro').textContent='CAMCGE is a replication benchmark. Keep the published closure if the goal is to reproduce the paper.';
      $('closurePanel').innerHTML=`
        <div class="closure-map">
          <div class="closure-box"><div class="mini-label">Anchor</div><h3>Fix mps</h3><p class="help">The base builder uses <code>model_instance("mps", None)</code>.</p></div>
          <div class="closure-arrow">+</div>
          <div class="closure-box"><div class="mini-label">Walras / current account</div><h3>Drop caeq</h3><p class="help">The current-account gap is checked to be approximately zero after solving.</p></div>
        </div>
        <div class="closure-explainer">
          <div><strong>Replication rule</strong><p>CAMCGE is being used as a benchmark against a published paper. Preserving the paper’s closure is therefore part of the validation target, not a cosmetic modeling choice.</p></div>
          <div><strong>Interpretation</strong><p>The experiment results show comparative-static differences from the published base equilibrium. They do not describe how Cameroon moved through time from one state to the other.</p></div>
        </div>`;
      $('closureStatus').textContent='Published closure';$('closureStatus').className='status-pill ok';
    }
  }

  function bindClosureInputs(){
    const c=state.closure[state.model];
    const nv=$('numeraireVar'), we=$('walrasEq');
    nv.addEventListener('change',()=>{
      c.numeraireVar=nv.value;c.numeraireIndex=defaultIndexForNumeraire(nv.value);saveLocal();renderClosure();generateAndRenderCode();
    });
    we.addEventListener('change',()=>{
      c.walrasEq=we.value;c.walrasIndex=defaultIndexForWalras(we.value);saveLocal();renderClosure();generateAndRenderCode();
    });
    populateClosureIndex('numeraireIndex',c.numeraireVar,c.numeraireIndex,true);
    populateClosureIndex('walrasIndex',c.walrasEq,c.walrasIndex,false);
    const ni=$('numeraireIndex'), wi=$('walrasIndex');
    if(ni) ni.addEventListener('change',()=>{c.numeraireIndex=ni.value;saveLocal();generateAndRenderCode()});
    if(wi) wi.addEventListener('change',()=>{c.walrasIndex=wi.value;saveLocal();generateAndRenderCode()});
  }

  function populateClosureIndex(id,kind,current,isNumeraire){
    const el=$(id); if(!el) return;
    let items=[];
    if(isNumeraire && kind==='epsilon'){
      el.innerHTML='<option value="">scalar / None</option>';el.disabled=true;return;
    }
    el.disabled=false;
    if(kind==='pf'||kind==='eqpf') items=activeLabels('factors');
    else items=activeLabels('goods');
    el.innerHTML=items.map(x=>`<option value="${esc(x)}" ${x===current?'selected':''}>${esc(x)}</option>`).join('');
  }

  function closureReady(){
    const m=model(); if(m.closure.kind!=='engine') return true;
    const c=state.closure[state.model]; if(!c) return false;
    if(c.numeraireVar==='epsilon') return Boolean(c.walrasEq && c.walrasIndex);
    return Boolean(c.numeraireVar && c.numeraireIndex && c.walrasEq && c.walrasIndex);
  }

  function renderScenario(){
    const m=model();
    const isEngine=m.controls;
    $('scenarioHeading').textContent=isEngine?'Build the counterfactual':'Queue scenarios to run';
    $('scenarioIntro').textContent=isEngine
      ? 'Choose only from economic controls the current model actually exposes as runtime shocks.'
      : state.model==='ifpri'
        ? 'These are the five validated IFPRI scenarios currently implemented in CGE-Core. Queue one or several runs.'
        : 'Queue the published CAMCGE experiments you want the generated runner to execute.';
    $('controlHeading').textContent=isEngine?'What do you want to change?':'Choose validated runs';
    $('stackMiniLabel').textContent=isEngine?'Shock stack':'Run queue';
    $('stackTitle').textContent=isEngine?'Planned changes':'Selected runs';

    if(isEngine){
      $('quickActions').innerHTML=m.quick.map((q,i)=>`<button type="button" class="quick-button" data-quick="${i}">${esc(q.label)}</button>`).join('');
      $('controlCards').innerHTML=m.controls.map(c=>`
        <button type="button" class="control-card" data-control="${c.id}">
          <div class="control-top"><span class="control-symbol">${esc(c.symbol)}</span><span class="fact">${targetLabel(c.target)}</span></div>
          <strong>${esc(c.name)}</strong><p>${esc(c.description)}</p><div class="why">${esc(c.meaning||'This changes an exogenous policy or scenario input before the economy re-equilibrates.')}</div>
        </button>`).join('');
      document.querySelectorAll('[data-control]').forEach(btn=>btn.addEventListener('click',()=>openControl(btn.dataset.control)));
      document.querySelectorAll('[data-quick]').forEach(btn=>btn.addEventListener('click',()=>applyQuick(m.quick[Number(btn.dataset.quick)])));
    }else{
      $('quickActions').innerHTML='';
      $('controlCards').innerHTML=m.scenarios.map(s=>`
        <button type="button" class="control-card" data-scenario="${s.id}">
          <div class="control-top"><span class="model-badge">${esc(s.name)}</span><span class="fact">validated</span></div>
          <strong>${esc(s.title)}</strong><p>${esc(s.description)}</p><div class="why no-prefix"><strong style="font-style:normal;color:var(--text)">Why this scenario matters: </strong>${esc(s.policy||'Queue this validated scenario for the generated runner.')}</div>
        </button>`).join('');
      document.querySelectorAll('[data-scenario]').forEach(btn=>btn.addEventListener('click',()=>addNamedScenario(btn.dataset.scenario)));
      $('controlEditor').classList.add('hidden');
    }
    renderStack();
    $('scenarioStatus').textContent=state.stack.length?(isEngine?`${state.stack.length} shock${state.stack.length>1?'s':''}`:`${state.stack.length} run${state.stack.length>1?'s':''}`):'Nothing queued';
    $('scenarioStatus').className='status-pill '+(state.stack.length?'ok':'warn');
  }

  function targetLabel(target){
    return {factor:'factor',good:'good / sector',scalar:'economy-wide'}[target]||target;
  }

  function openControl(id,preset=null,editIndex=null){
    const c=model().controls.find(x=>x.id===id); if(!c) return;
    let targets=[];
    if(c.target==='factor') targets=activeLabels('factors');
    if(c.target==='good') targets=activeLabels('goods');
    const targetSelect=c.target==='scalar'?'':`
      <div class="form-field"><label>Target ${targetLabel(c.target)}</label>
      <select id="editTarget" class="select">${targets.map(x=>`<option ${preset?.target===x?'selected':''}>${esc(x)}</option>`).join('')}</select></div>`;
    $('controlEditor').innerHTML=`
      <div class="editor-head"><div><div class="mini-label">Configure shock</div><h3>${esc(c.name)} · ${esc(c.symbol)}</h3></div>
      <button id="closeEditor" type="button" class="button small ghost">Close</button></div>
      <p class="help">${esc(c.description)}</p>
      <div class="operation-grid">
        ${targetSelect}
        <div class="form-field"><label>Operation</label>
          <select id="editOperation" class="select">
            <option value="pct">Change by % of BASE</option>
            <option value="set">Set exact model value</option>
            <option value="multiply">Multiply BASE by</option>
            ${c.allowZero?'<option value="zero">Set to zero</option>':''}
          </select>
        </div>
        <div class="form-field" id="amountField"><label id="amountLabel">Percent change</label>
          <input id="editAmount" class="text-input" type="number" step="any" value="${preset?.amount ?? 10}">
        </div>
      </div>
      <div id="operationHelp" class="operation-help"></div>
      <div class="policy-lens">
        <div class="policy-lens-title">Policy interpretation</div>
        <div class="lens-grid">
          <div class="lens-box"><strong>What this shock means</strong><p>${esc(c.meaning||c.description)}</p></div>
          <div class="lens-box"><strong>What to watch in the results</strong><p>${esc(c.watch||'Follow the directly affected price or quantity first, then sector output, factor markets, household demand, trade and welfare.')}</p></div>
          <div class="lens-box"><strong>Important caution</strong><p>${esc(c.caution||'This is a comparative-static counterfactual: it asks for a new equilibrium, not the time path of adjustment.')}</p></div>
          <div class="lens-box"><strong>General-equilibrium logic</strong><p>The selected value is exogenous in SIM. Prices and quantities that remain endogenous move together until all model markets and accounting identities are satisfied under the chosen closure.</p></div>
        </div>
      </div>
      <button id="addConfiguredShock" type="button" class="button primary" style="margin-top:12px">${editIndex===null?'Add shock':'Update shock'}</button>`;
    $('controlEditor').classList.remove('hidden');
    const op=$('editOperation'); op.value=preset?.op||'pct'; updateAmountField();
    op.addEventListener('change',updateAmountField);
    $('closeEditor').addEventListener('click',()=>$('controlEditor').classList.add('hidden'));
    $('addConfiguredShock').addEventListener('click',()=>{
      const operation=op.value;
      const target=c.target==='scalar'?'':$('editTarget').value;
      const amount=operation==='zero'?0:Number($('editAmount').value);
      if(operation!=='zero'&&!Number.isFinite(amount)){
        $('operationHelp').textContent='Enter a finite numeric value.'; return;
      }
      if(c.target!=='scalar' && !target){
        $('operationHelp').textContent='Choose an active target label before adding the shock.'; return;
      }
      const validation=validateShock(c,operation,amount);
      if(validation){ $('operationHelp').textContent=validation; return; }
      const next={kind:'shock',control:c.id,target,operation,amount};
      if(editIndex===null){
        const duplicate=state.stack.findIndex(x=>x.kind==='shock' && x.control===c.id && x.target===target);
        if(duplicate>=0) state.stack[duplicate]=next; else state.stack.push(next);
      }else{
        state.stack[editIndex]=next;
      }
      $('controlEditor').classList.add('hidden');
      renderScenario(); generateAndRenderCode();
    });
  }

  function validateShock(c,operation,amount){
    if(c.domain==='nonnegative'){
      if(operation==='set' && amount<0) return 'This model control is nonnegative. Use a value of zero or above.';
      if(operation==='pct' && amount<-100) return 'A reduction below −100% would imply a negative rate. Choose −100% or a smaller reduction.';
      if(operation==='multiply' && amount<0) return 'Use a nonnegative multiplier for this rate.';
    }
    if(c.domain==='positive'){
      if(operation==='set' && amount<=0) return 'This control should remain strictly positive in this formulation.';
      if(operation==='pct' && amount<=-100) return 'A reduction of −100% or more would make this positive control zero or negative.';
      if(operation==='multiply' && amount<=0) return 'Use a strictly positive multiplier for this control.';
    }
    return '';
  }

  function updateAmountField(){
    const op=$('editOperation').value;
    $('amountField').classList.toggle('hidden',op==='zero');
    const labels={pct:'Percent change from BASE',set:'Exact new model value',multiply:'Multiplier'};
    if($('amountLabel')) $('amountLabel').textContent=labels[op]||'';
    const c=selectedControlFromEditor();
    let help='';
    if(op==='pct') help='This is a relative change from the calibrated BASE value. Example: a 50% cut to a tax rate of 0.10 produces 0.05.';
    if(op==='multiply') help='Enter a factor such as 1.10 for a 10% increase or 0.50 for a 50% reduction.';
    if(op==='zero') help='The selected exogenous parameter will be set to exactly zero in SIM.';
    if(op==='set'){
      if(c && c.unit==='rate') help='Enter the exact decimal rate used by the model: 0.12 means 12%, 0.05 means 5%.';
      else if(c && c.unit==='price') help='Enter the exact model price level. In the Hosoe Standard benchmark, world prices are normalized to 1.';
      else help='Enter the exact model quantity/value in the units used by the calibrated dataset.';
    }
    if($('operationHelp')) $('operationHelp').textContent=help;
  }

  function selectedControlFromEditor(){
    const title=$('controlEditor')?.querySelector('h3')?.textContent||'';
    return (model().controls||[]).find(c=>title.startsWith(c.name+' ·')) || null;
  }

  function applyQuick(q){
    const c=model().controls.find(x=>x.id===q.control); if(!c) return;
    const preset={op:q.op,amount:q.amount,target:q.target};
    if(c.target!=='scalar' && q.target && !targetValues(c.target).includes(q.target)){
      preset.target=targetValues(c.target)[0]||'';
    }
    openControl(c.id,preset);
  }
  function targetValues(target){
    if(target==='factor') return activeLabels('factors');
    if(target==='good') return activeLabels('goods');
    return [];
  }

  function addNamedScenario(id){
    if(state.stack.some(x=>x.kind==='scenario'&&x.id===id)) return;
    state.stack.push({kind:'scenario',id});
    renderScenario(); generateAndRenderCode();
  }

  function renderStack(){
    const m=model();
    const isEngine=Boolean(m.controls);
    if(!state.stack.length){
      $('scenarioStack').innerHTML=`<div class="empty-stack">${isEngine?'Add a shock to start building the SIM.':'Click a scenario card to queue a run.'}</div>`;
      $('stackSummary').textContent=isEngine?'The generated script will set all selected exogenous values, then solve one joint SIM equilibrium.':'The generated runner will execute the selected scenarios.';
      return;
    }
    $('scenarioStack').innerHTML=state.stack.map((item,i)=>{
      if(item.kind==='shock'){
        const c=m.controls.find(x=>x.id===item.control);
        return `<div class="stack-item">
          <div class="stack-item-head"><div><strong>${esc(c.name)}</strong><p>${esc(shockSummary(c,item))}</p></div>
          <div class="stack-controls">
            <button data-edit="${i}" title="Edit">✎</button><button data-remove="${i}" title="Remove">×</button>
          </div></div></div>`;
      }
      const s=m.scenarios.find(x=>x.id===item.id);
      return `<div class="stack-item"><div class="stack-item-head"><div><strong>${esc(s.name)}</strong><p>${esc(s.title)}</p></div>
        <div class="stack-controls"><button data-up="${i}">↑</button><button data-down="${i}">↓</button><button data-remove="${i}">×</button></div></div></div>`;
    }).join('');
    document.querySelectorAll('[data-remove]').forEach(b=>b.addEventListener('click',()=>{state.stack.splice(Number(b.dataset.remove),1);renderScenario();generateAndRenderCode()}));
    document.querySelectorAll('[data-edit]').forEach(b=>b.addEventListener('click',()=>{
      const i=Number(b.dataset.edit), item=state.stack[i];
      if(item && item.kind==='shock') openControl(item.control,{op:item.operation,amount:item.amount,target:item.target},i);
    }));
    document.querySelectorAll('[data-up]').forEach(b=>b.addEventListener('click',()=>moveStack(Number(b.dataset.up),-1)));
    document.querySelectorAll('[data-down]').forEach(b=>b.addEventListener('click',()=>moveStack(Number(b.dataset.down),1)));
    if(isEngine){
      const phrases=state.stack.map(item=>{
        const c=model().controls.find(x=>x.id===item.control);
        return c ? shockSummary(c,item) : '';
      }).filter(Boolean);
      $('stackSummary').innerHTML=`<div>${state.stack.length} shock${state.stack.length>1?'s':''} will be combined into one SIM and solved simultaneously. Their display order does not change the equilibrium.</div>
        <div class="policy-question"><strong>Policy question:</strong> What new equilibrium results if ${esc(phrases.join('; '))}, while the calibrated benchmark structure and selected closure are otherwise maintained?</div>`;
    }else{
      $('stackSummary').innerHTML=`<div>${state.stack.length} selected run${state.stack.length>1?'s':''}.</div>
        <div class="policy-question"><strong>Interpretation:</strong> Each queued item is solved as its own validated counterfactual against the benchmark; the runs are not compounded sequentially into one mega-shock. Reordering them changes only the order in which they are executed and printed.</div>`;
    }
  }

  function moveStack(i,delta){
    const j=i+delta;if(j<0||j>=state.stack.length)return;
    [state.stack[i],state.stack[j]]=[state.stack[j],state.stack[i]];
    renderScenario();generateAndRenderCode();
  }
  function shockSummary(c,item){
    const target=item.target?`${c.symbol.replace(/\[.*?\]/,'')}[${item.target}]` : c.symbol;
    if(item.operation==='zero') return `${target} → 0`;
    if(item.operation==='pct') return `${target}: ${item.amount>=0?'+':''}${item.amount}% from BASE`;
    if(item.operation==='multiply') return `${target}: BASE × ${item.amount}`;
    return `${target} → ${item.amount}`;
  }

  function renderOutputs(){
    $('outputsGrid').innerHTML=model().outputs.map(x=>`<div class="output-card"><strong>${esc(x[0])}</strong><p>${esc(x[1])}</p></div>`).join('');
  }

  function generateCode(){
    if(state.model==='simple'||state.model==='standard') return engineCode();
    if(state.model==='ifpri') return ifpriCode();
    return camCode();
  }

  function solverCode(){
    if(state.dataSource.solver==='auto') return `solver = detect_solver()`;
    return `solver = ${py(state.dataSource.solver)}`;
  }

  function engineCode(){
    const isStd=state.model==='standard';
    const m=model(), c=state.closure[state.model]||{};
    const defClass=isStd?'StdModelDef':'SplModelDef';
    const defImport=isStd?'stdcge_model_def':'splcge_model_def';
    let ctor=`${defClass}()`;
    if(isStd && state.accounts){
      const defaults={hoh:'HOH',gov:'GOV',inv:'INV',ext:'EXT',idt:'IDT',trf:'TRF'};
      const changed=Object.keys(defaults).filter(k=>(state.accounts[k]||defaults[k])!==defaults[k]);
      if(changed.length){
        ctor=`${defClass}(accounts=${pyObject(Object.fromEntries(Object.keys(defaults).map(k=>[k,state.accounts[k]||defaults[k]])))})`;
      }
    }
    if(!isStd && state.simpleAccount && state.simpleAccount!=='HOH'){
      ctor=`${defClass}(accounts={'hoh': ${py(state.simpleAccount)}})`;
    }

    const dataLine=state.dataSource.mode==='custom'
      ? `DATA_DIR = Path(${py(state.dataSource.customPath || 'my_data_dir')})`
      : `DATA_DIR = example_data(${py(m.data.example)})`;

    const imports=[
      'from pathlib import Path',
      'from pyomo.environ import value',
      'from cge_core import PyCGE, example_data',
      `from cge_core.examples.${defImport} import ${defClass}`,
      'from cge_core.examples._solver import detect_solver'
    ];
    if(isStd) imports.push('from cge_core.examples.stdcge import equivalent_variation');

    const numIndex=c.numeraireVar==='epsilon'?'None':py(c.numeraireIndex||defaultIndexForNumeraire(c.numeraireVar));
    const walIndex=py(c.walrasIndex||defaultIndexForWalras(c.walrasEq));
    const shockLines=[];
    state.stack.filter(x=>x.kind==='shock').forEach((item,i)=>{
      const ctrl=m.controls.find(x=>x.id===item.control); if(!ctrl)return;
      const idx=ctrl.target==='scalar'?'None':py(item.target);
      const ref=ctrl.target==='scalar'?`cge.base.${ctrl.component}`:`cge.base.${ctrl.component}[${py(item.target)}]`;
      shockLines.push(`# ${i+1}. ${ctrl.name}${item.target?` — ${item.target}`:''}`);
      if(ctrl.meaning) shockLines.push(`# Economic meaning: ${ctrl.meaning}`);
      if(item.operation==='zero'){
        shockLines.push(`cge.model_modify_sim(${py(ctrl.component)}, ${idx}, 0.0)`);
      }else if(item.operation==='set'){
        shockLines.push(`cge.model_modify_sim(${py(ctrl.component)}, ${idx}, ${num(item.amount)})`);
      }else{
        shockLines.push(`base_${i+1} = value(${ref})`);
        if(item.operation==='pct'){
          shockLines.push(`new_${i+1} = base_${i+1} * (1.0 + ${num(item.amount)} / 100.0)`);
        }else{
          shockLines.push(`new_${i+1} = base_${i+1} * ${num(item.amount)}`);
        }
        shockLines.push(`cge.model_modify_sim(${py(ctrl.component)}, ${idx}, new_${i+1})`);
      }
      shockLines.push('');
    });
    if(!shockLines.length) shockLines.push('# Add at least one shock in the Control Room before running this scenario.');

    const results=isStd?`
# --- Results ---------------------------------------------------------------
results = cge.model_compare()
output_dir = Path("cge-results")
output_dir.mkdir(exist_ok=True)
results.to_csv(output_dir / "scenario_changes.csv", index=False)

print(results.to_string(index=False))
print("\\nObjective comparison:", results.attrs.get("objective", {}))
print("Equivalent variation:", equivalent_variation(cge))
`:
`
# --- Results ---------------------------------------------------------------
results = cge.model_compare()
output_dir = Path("cge-results")
output_dir.mkdir(exist_ok=True)
results.to_csv(output_dir / "scenario_changes.csv", index=False)

print(results.to_string(index=False))
print("\\nObjective comparison:", results.attrs.get("objective", {}))
`;

    return `${imports.join('\n')}

${solverCode()}
${dataLine}

# --- Build and calibrate BASE ---------------------------------------------
cge = PyCGE(${ctor})
cge.model_data(DATA_DIR)
cge.model_instance(${py(c.numeraireVar||m.closure.defaultNumeraire)}, ${numIndex})
cge.model_drop_redundant(${py(c.walrasEq||m.closure.defaultWalras)}, ${walIndex})
cge.model_calibrate(solver)

# --- Create SIM and apply the counterfactual ------------------------------
cge.model_sim()
${shockLines.join('\n')}
cge.model_solve(solver)
${results}`;
  }

  function ifpriCode(){
    const ids=state.stack.filter(x=>x.kind==='scenario').map(x=>x.id);
    const pathLine=state.dataSource.ifpriPath.trim()
      ? `os.environ["IFPRI_SOURCE_DIR"] = ${py(state.dataSource.ifpriPath.trim())}`
      : `# os.environ["IFPRI_SOURCE_DIR"] = "C:\\\\path\\\\to\\\\ifpri-test-folder"`;
    const solver=state.dataSource.solver==='auto'?'None':py(state.dataSource.solver);
    return `import os
from pathlib import Path

from cge_core.ifpri import (
    load_ifpri_test_data,
    calibrate_ifpri_benchmark,
    build_ifpri_base_solve_model,
    perturb_ifpri_start,
    solve_ifpri_base,
    build_and_solve_ifpri_scenarios,
    summarize_ifpri_results,
    compare_ifpri_scenarios,
)

${pathLine}

dataset = load_ifpri_test_data()
calibration = calibrate_ifpri_benchmark(dataset)

# BASE
base_model = build_ifpri_base_solve_model(dataset, calibration)
perturb_ifpri_start(base_model, 1.02)
base_report = solve_ifpri_base(base_model, solver=${solver})

# Selected validated scenarios
scenario_names = ${pyList(ids)}
results = build_and_solve_ifpri_scenarios(
    dataset,
    scenarios=scenario_names,
    solver=${solver},
)

output_dir = Path("ifpri-results")
output_dir.mkdir(exist_ok=True)

summary = summarize_ifpri_results(results)
changes = compare_ifpri_scenarios(base_model, results)

summary.to_csv(output_dir / "solve_summary.csv", index=False)
changes.to_csv(output_dir / "scenario_changes.csv", index=False)

print(summary.to_string(index=False))
print("\\nScenario changes:")
print(changes.to_string(index=False))
`;
  }

  function camCode(){
    const ids=state.stack.filter(x=>x.kind==='scenario').map(x=>x.id);
    const solver=state.dataSource.solver==='auto'?'cyipopt':state.dataSource.solver;
    const calls=ids.map(id=>{
      const n={exp1:1,exp2:2,exp3:3}[id];
      return `metrics["experiment_${n}"] = experiment_${n}(cge, base, solver)`;
    });
    if(!calls.length) calls.push('# Add at least one published experiment in the Control Room.');
    return `import json
from pathlib import Path

from cam.replicate_base import build_base
from cam.replicate_experiments import (
    snapshot,
    experiment_1,
    experiment_2,
    experiment_3,
)

solver = ${py(solver)}

cge, dof_before, dof_after = build_base(solver)
assert dof_before == -1 and dof_after == 0
base = snapshot(cge.base)

metrics = {}
${calls.join('\n')}

output_dir = Path("cam-results")
output_dir.mkdir(exist_ok=True)
with (output_dir / "selected_experiments.json").open("w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

print("\\nSaved:", output_dir / "selected_experiments.json")
`;
  }

  function py(s){ return JSON.stringify(String(s)); }
  function pyList(items){ return '['+items.map(py).join(', ')+']'; }
  function pyObject(obj){
    return '{'+Object.entries(obj).map(([k,v])=>`${py(k)}: ${py(v)}`).join(', ')+'}';
  }
  function num(v){
    const n=Number(v); return Number.isFinite(n)?String(n):'0.0';
  }

  function generateAndRenderCode(){
    const code=generateCode();
    $('codePreview').querySelector('code').textContent=code;
    renderReadiness(code);
    renderRunInstructions();
  }

  function renderReadiness(){
    const m=model();
    let ready=true, msg='Ready to export';
    if(m.controls){
      if(!hasRequiredLabels()){ready=false;msg='Fix active labels'}
      else if(!closureReady()){ready=false;msg='Fix closure'}
      else if(!state.stack.length){ready=false;msg='Add a shock'}
    }else if(!state.stack.length){ready=false;msg='Queue a run'}
    $('readyStatus').textContent=msg;
    $('readyStatus').className='status-pill '+(ready?'ok':'warn');
    $('scriptCaption').textContent=ready?'Executable scenario scaffold':'Script scaffold — finish the highlighted steps above';
  }

  function renderRunInstructions(){
    const file=state.model==='camcge'?'cam_scenario.py':state.model==='ifpri'?'ifpri_scenario.py':'scenario.py';
    $('runInstructions').innerHTML=`
      <div class="run-steps">
        <div class="run-step"><div><strong>Save the generated file</strong><div class="command">${esc(file)}</div></div></div>
        <div class="run-step"><div><strong>Run it from the CGE-Core repository root</strong><div class="command">python ${esc(file)}</div></div></div>
      </div>`;
    let files=[];
    if(state.model==='ifpri') files=['ifpri-results/solve_summary.csv','ifpri-results/scenario_changes.csv'];
    else if(state.model==='camcge') files=['cam-results/selected_experiments.json'];
    else files=['cge-results/scenario_changes.csv'];
    $('resultFiles').innerHTML=files.map(x=>`<div class="result-file">${esc(x)}</div>`).join('');
  }

  function download(filename,content,type='text/plain'){
    const blob=new Blob([content],{type});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  }

  function exportJson(){
    return JSON.stringify({
      model:state.model,
      dataSource:state.dataSource,
      closure:state.closure[state.model]||null,
      labels:state.labels[state.model]||null,
      scenarioStack:state.stack
    },null,2);
  }

  function bindStatic(){
    $('themeSelect').addEventListener('change',()=>applyTheme($('themeSelect').value));
    $('resetLabelsBtn').addEventListener('click',resetLabels);
    $('clearStackBtn').addEventListener('click',()=>{state.stack=[];renderScenario();generateAndRenderCode()});
    $('copyCodeBtn').addEventListener('click',async()=>{
      const text=$('codePreview').textContent;
      try{await navigator.clipboard.writeText(text);$('copyCodeBtn').textContent='Copied';setTimeout(()=>$('copyCodeBtn').textContent='Copy',1200)}
      catch(e){download('scenario.py',text)}
    });
    $('downloadPyBtn').addEventListener('click',()=>{
      const name=state.model==='camcge'?'cam_scenario.py':state.model==='ifpri'?'ifpri_scenario.py':'scenario.py';
      download(name,$('codePreview').textContent,'text/x-python');
    });
    $('downloadJsonBtn').addEventListener('click',()=>download('cge_scenario.json',exportJson(),'application/json'));
  }

  function applyTheme(theme){
    if(!['light','dark','system'].includes(theme)) theme='light';
    document.documentElement.dataset.theme=theme;
    $('themeSelect').value=theme;
    try{localStorage.setItem('cge-control-room-theme',theme)}catch(e){}
  }

  function renderAll(){
    renderModelCards();
    renderOverview();
    renderWalkthrough();
    renderEconomy();
    ensureClosureDefaults();
    renderClosure();
    renderScenario();
    renderOutputs();
    generateAndRenderCode();
  }

  function init(){
    loadLocal();
    let theme='light';try{theme=localStorage.getItem('cge-control-room-theme')||'light'}catch(e){}
    applyTheme(theme);
    bindStatic();
    ensureClosureDefaults();
    renderAll();
  }

  init();
})();
