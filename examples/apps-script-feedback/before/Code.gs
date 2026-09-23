// Workstyle feedback writer. Invented example project for portfolio-demo-kit.
const ANTHROPIC_KEY = 'sk-ant-api03-EXAMPLEfakeKEYforTESTINGonly0000000000000000000000000000';
const MODEL = 'claude-sonnet-5';
const SHEET_ID = '1bRkFoLdTiLeSFeEdBaCkEXAMPLE0nlyN0tRealSheet42';

// Each trait is the average of two questions (columns in the Responses sheet).
const TRAIT_QUESTIONS = {
  Anchor: ['Q1', 'Q5'],
  Kindle: ['Q2', 'Q6'],
  Lattice: ['Q3', 'Q7'],
  Horizon: ['Q4', 'Q8'],
};

function readTable(name) {
  const values = SpreadsheetApp.openById(SHEET_ID).getSheetByName(name).getDataRange().getValues();
  const header = values.shift();
  return values.map(row => Object.fromEntries(header.map((h, i) => [h, row[i]])));
}

function scoreTraits(response) {
  const scores = {};
  for (const [trait, qs] of Object.entries(TRAIT_QUESTIONS)) {
    const total = qs.reduce((sum, q) => sum + Number(response[q] || 0), 0);
    scores[trait] = Math.round((total / qs.length) * 10) / 10;
  }
  return scores;
}

function describeGaps(scores, targets) {
  return Object.keys(scores).map(trait => {
    const gap = Math.round((scores[trait] - Number(targets[trait])) * 10) / 10;
    let band = 'on target';
    if (gap <= -1) band = 'well below the role target';
    else if (gap < 0) band = 'a little below the role target';
    else if (gap >= 1) band = 'well above the role target';
    else if (gap > 0) band = 'a little above the role target';
    return `${trait}: ${scores[trait]} (target ${targets[trait]}, ${band})`;
  }).join('\n');
}

function buildPrompt(response, persona, targets) {
  const scores = scoreTraits(response);
  return [
    `Role: ${response.Role}`,
    `Role persona: ${persona.Description}`,
    `First name: ${response.Name.split(' ')[0]}`,
    'Trait results (1-5 scale):',
    describeGaps(scores, targets),
    `Their own comment: ${response.Comment || '(none)'}`,
  ].join('\n');
}

function callModel(userText) {
  const res = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', {
    method: 'post',
    contentType: 'application/json',
    headers: { 'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01' },
    payload: JSON.stringify({
      model: MODEL,
      max_tokens: 800,
      system: WRITING_RULES,
      messages: [{ role: 'user', content: userText }],
    }),
  });
  const data = JSON.parse(res.getContentText());
  return data.content.filter(b => b.type === 'text').map(b => b.text).join('');
}

function writeAllFeedback() {
  const responses = readTable('Responses');
  const personas = Object.fromEntries(readTable('Personas').map(p => [p.Role, p]));
  const grid = Object.fromEntries(readTable('TargetGrid').map(t => [t.Role, t]));
  const out = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Feedback');
  responses.forEach((r, i) => {
    if (!personas[r.Role]) return; // unknown role: skipped, Wren handles by hand
    const note = callModel(buildPrompt(r, personas[r.Role], grid[r.Role]));
    out.getRange(i + 2, 1, 1, 3).setValues([[r.Email, r.Name, note]]);
  });
}
