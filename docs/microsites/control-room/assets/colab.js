(() => {
  'use strict';

  const WHEEL_URL =
    'https://github.com/miraflor/CGE-core/releases/download/v0.7.0/cge_core-0.7.0-py3-none-any.whl';
  const COLAB_HOME = 'https://colab.research.google.com/';

  const $ = id => document.getElementById(id);

  function currentCode() {
    const node = document.querySelector('#codePreview code');
    return node ? node.textContent : '';
  }

  function sourceLines(text) {
    const lines = String(text).split('\n');
    return lines.map((line, index) =>
      line + (index < lines.length - 1 ? '\n' : '')
    );
  }

  function safeSlug(value) {
    return String(value || 'experiment')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'experiment';
  }

  function notebookFilename() {
    const model = $('modelTitle')?.textContent || 'cge';
    return `cge-core-${safeSlug(model)}-experiment.ipynb`;
  }

  function notebookObject() {
    const model = $('modelTitle')?.textContent || 'CGE model';
    const code = currentCode();

    return {
      cells: [
        {
          cell_type: 'markdown',
          metadata: {},
          source: sourceLines(
            `# CGE-Core Control Room experiment\n\n` +
            `**Model:** ${model}\n\n` +
            `Generated from the CGE-Core v0.7.0 Control Room. ` +
            `Review the model, data choice, closure, and policy scenario before running.\n`
          )
        },
        {
          cell_type: 'code',
          execution_count: null,
          metadata: {},
          outputs: [],
          source: sourceLines(`%pip install -q "${WHEEL_URL}"\n`)
        },
        {
          cell_type: 'code',
          execution_count: null,
          metadata: {},
          outputs: [],
          source: sourceLines(code.endsWith('\n') ? code : `${code}\n`)
        }
      ],
      metadata: {
        colab: {
          name: notebookFilename(),
          provenance: []
        },
        kernelspec: {
          display_name: 'Python 3',
          language: 'python',
          name: 'python3'
        },
        language_info: {
          name: 'python'
        },
        cge_core: {
          version: '0.7.0',
          generated_by: 'CGE-Core Control Room',
          source_page: window.location.href
        }
      },
      nbformat: 4,
      nbformat_minor: 5
    };
  }

  function downloadText(filename, text, type) {
    const blob = new Blob([text], {type});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function downloadNotebook() {
    const filename = notebookFilename();
    downloadText(
      filename,
      JSON.stringify(notebookObject(), null, 2) + '\n',
      'application/x-ipynb+json'
    );
    return filename;
  }

  function setStatus(message) {
    const node = $('colabHandoffStatus');
    if (node) node.textContent = message;
  }

  $('downloadNotebookBtn')?.addEventListener('click', () => {
    const filename = downloadNotebook();
    setStatus(
      `Downloaded ${filename}. It contains the release-wheel install cell and the current generated experiment.`
    );
  });

  $('openColabBtn')?.addEventListener('click', () => {
    // Open Colab during the click event so browsers do not treat it as a
    // delayed popup. The generated notebook is downloaded in the same action.
    window.open(COLAB_HOME, '_blank', 'noopener,noreferrer');
    const filename = downloadNotebook();

    // Also copy the Python when browser permissions allow it. This gives the
    // user a fast fallback if they prefer a new blank Colab notebook.
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(currentCode()).catch(() => {});
    }

    setStatus(
      `Downloaded ${filename} and opened Colab. In Colab choose File → Upload notebook and select the downloaded file. The Python was also copied to your clipboard when permitted.`
    );
  });
})();
