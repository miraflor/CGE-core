# Notebook course

<div class="notebook-course-hero">
  <div class="notebook-course-kicker">CGE-Core v0.7.0</div>
  <h2>Learn CGE by running the economy</h2>
  <p>
    Seven short notebooks take you from a first equilibrium to policy experiments,
    your own SAM, published model replications, and advanced internals.
    Every notebook runs directly in Google Colab.
  </p>
  <a class="notebook-course-start"
     href="https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/01_first_cge.ipynb"
     target="_blank" rel="noopener">Start with notebook 01 in Colab ↗</a>
</div>

<div class="notebook-course-grid">

  <article class="notebook-card notebook-card-start">
    <div class="notebook-card-top">
      <span class="notebook-number">01</span>
      <span class="notebook-level">Start here</span>
    </div>
    <h3>Your first CGE</h3>
    <p>Solve the bundled Standard CGE benchmark and learn to read production, prices, trade, household demand, and closure.</p>
    <div class="notebook-actions">
      <a class="notebook-button notebook-button-primary"
         href="https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/01_first_cge.ipynb"
         target="_blank" rel="noopener">Open in Colab ↗</a>
      <a class="notebook-button" href="../notebooks/01_first_cge.html">Read notebook</a>
    </div>
  </article>

  <article class="notebook-card">
    <div class="notebook-card-top">
      <span class="notebook-number">02</span>
      <span class="notebook-level">Policy</span>
    </div>
    <h3>Policy experiments</h3>
    <p>Follow the core comparative-static workflow: benchmark → shock → counterfactual → comparison.</p>
    <div class="notebook-actions">
      <a class="notebook-button notebook-button-primary"
         href="https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/02_policy_experiments.ipynb"
         target="_blank" rel="noopener">Open in Colab ↗</a>
      <a class="notebook-button" href="../notebooks/02_policy_experiments.html">Read notebook</a>
    </div>
  </article>

  <article class="notebook-card">
    <div class="notebook-card-top">
      <span class="notebook-number">03</span>
      <span class="notebook-level">Data</span>
    </div>
    <h3>Bring your own SAM</h3>
    <p>Inspect a social accounting matrix, check balance, construct <code>StandardCGE</code>, and map country-specific institutional labels explicitly.</p>
    <div class="notebook-actions">
      <a class="notebook-button notebook-button-primary"
         href="https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/03_your_own_sam.ipynb"
         target="_blank" rel="noopener">Open in Colab ↗</a>
      <a class="notebook-button" href="../notebooks/03_your_own_sam.html">Read notebook</a>
    </div>
  </article>

  <article class="notebook-card">
    <div class="notebook-card-top">
      <span class="notebook-number">04</span>
      <span class="notebook-level">Replication</span>
    </div>
    <h3>CAMCGE</h3>
    <p>Use the published Cameroon 1987 replication as a first-class model and reproduce a model-specific counterfactual.</p>
    <div class="notebook-actions">
      <a class="notebook-button notebook-button-primary"
         href="https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/04_camcge.ipynb"
         target="_blank" rel="noopener">Open in Colab ↗</a>
      <a class="notebook-button" href="../notebooks/04_camcge.html">Read notebook</a>
    </div>
  </article>

  <article class="notebook-card">
    <div class="notebook-card-top">
      <span class="notebook-number">05</span>
      <span class="notebook-level">IFPRI</span>
    </div>
    <h3>IFPRI Standard CGE</h3>
    <p>Run the synthetic public economy, execute a named IFPRI scenario, and understand the clean-room boundary for official-source validation.</p>
    <div class="notebook-actions">
      <a class="notebook-button notebook-button-primary"
         href="https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/05_ifpri.ipynb"
         target="_blank" rel="noopener">Open in Colab ↗</a>
      <a class="notebook-button" href="../notebooks/05_ifpri.html">Read notebook</a>
    </div>
  </article>

  <article class="notebook-card">
    <div class="notebook-card-top">
      <span class="notebook-number">06</span>
      <span class="notebook-level">Authoring</span>
    </div>
    <h3>Build a model</h3>
    <p>Explore functional Python authoring and the experimental deterministic <code>.cge.md</code> specification.</p>
    <div class="notebook-actions">
      <a class="notebook-button notebook-button-primary"
         href="https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/06_build_a_model.ipynb"
         target="_blank" rel="noopener">Open in Colab ↗</a>
      <a class="notebook-button" href="../notebooks/06_build_a_model.html">Read notebook</a>
    </div>
  </article>

  <article class="notebook-card notebook-card-advanced">
    <div class="notebook-card-top">
      <span class="notebook-number">90</span>
      <span class="notebook-level">Advanced</span>
    </div>
    <h3>Internals and advanced access</h3>
    <p>Inspect the retained Pyomo/PyCGE machinery after learning the practitioner interface. This notebook is deliberately last.</p>
    <div class="notebook-actions">
      <a class="notebook-button notebook-button-primary"
         href="https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/90_internals.ipynb"
         target="_blank" rel="noopener">Open in Colab ↗</a>
      <a class="notebook-button" href="../notebooks/90_internals.html">Read notebook</a>
    </div>
  </article>

</div>

<div class="notebook-course-note">
  <strong>Nothing to configure before modelling.</strong>
  In Colab, each notebook starts with one CGE-Core package-install cell.
  Solver discovery and first-use setup remain inside CGE-Core.
</div>

## What the sequence teaches

```text
01  solve and read an equilibrium
 ↓
02  change policy and compare equilibria
 ↓
03  move from bundled data to your own SAM
 ↓
04  study a published CAMCGE replication
 ↓
05  work with the IFPRI Standard CGE path
 ↓
06  see how custom models can be authored
 ↓
90  inspect Pyomo / PyCGE internals only when you want them
```

The seven canonical notebooks are also executed end-to-end in the repository's notebook CI on Python 3.11 and Python 3.13. Legacy notebook filenames from earlier releases remain only as compatibility redirects; they are not a second course.
