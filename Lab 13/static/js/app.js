let allQuestions = [];
let currentQuestion = null;
let quizHistory = [];
let searchTimer = null;
let sessionAnswered = 0;
let sessionCorrect = 0;

function switchView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`view-${name}`).classList.add('active');
  document.querySelector(`[data-view="${name}"]`).classList.add('active');
  if (name === 'stats') loadStats();
}

async function loadQuestions(shuffle = false) {
  const topic = document.getElementById('filterTopic').value;
  const difficulty = document.getElementById('filterDifficulty').value;
  const search = document.getElementById('searchInput').value;
  const grid = document.getElementById('questionsGrid');

  grid.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading...</p></div>';

  const params = new URLSearchParams({ topic, difficulty, search });
  if (shuffle) params.set('shuffle', 'true');

  const res = await fetch(`/api/questions?${params}`);
  const data = await res.json();
  allQuestions = data.questions;

  renderQuestions(allQuestions);
  updateResultsMeta(allQuestions.length);
}

function renderQuestions(questions) {
  const grid = document.getElementById('questionsGrid');
  if (!questions.length) {
    grid.innerHTML = '<div class="empty-state">No questions match your filters. Try adjusting the search or filters.</div>';
    return;
  }
  grid.innerHTML = questions.map((q, i) => `
    <div class="question-card" onclick="openQuestion(${i})">
      <div class="card-header">
        <div class="card-badges">
          <span class="badge-topic">${q.topic || 'General'}</span>
          <span class="badge-diff ${q.difficulty || ''}">${q.difficulty || 'Medium'}</span>
        </div>
        <span class="card-num">#${String(i + 1).padStart(2, '0')}</span>
      </div>
      <p class="card-question">${q.question}</p>
      <div class="card-arrow">Open →</div>
    </div>
  `).join('');
}

function updateResultsMeta(count) {
  document.getElementById('resultsCount').textContent = `${count} question${count !== 1 ? 's' : ''}`;
  const total = parseInt(document.getElementById('headerCount').textContent);
  const pct = total ? Math.round((count / total) * 100) : 0;
  document.getElementById('progressBar').style.width = `${pct}%`;
  document.getElementById('progressText').textContent = `${pct}% of total`;
}

function shuffleQuestions() { loadQuestions(true); }

function resetFilters() {
  document.getElementById('filterTopic').value = 'all';
  document.getElementById('filterDifficulty').value = 'all';
  document.getElementById('searchInput').value = '';
  loadQuestions();
}

function debounceSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadQuestions, 350);
}

function openQuestion(index) {
  const q = allQuestions[index];
  if (!q) return;
  currentQuestion = q;

  document.getElementById('modalTopic').textContent = q.topic || 'General';
  document.getElementById('modalDiff').textContent = q.difficulty || 'Medium';
  document.getElementById('modalDiff').className = `badge-diff ${q.difficulty || ''}`;
  document.getElementById('modalQuestion').textContent = q.question;
  document.getElementById('modalAnswerText').textContent = q.answer;
  document.getElementById('modalAnswer').style.display = 'none';
  document.getElementById('modalRevealBtn').textContent = '👁 Reveal Answer';
  document.getElementById('questionModal').classList.add('open');
}

function toggleModalAnswer() {
  const ans = document.getElementById('modalAnswer');
  const btn = document.getElementById('modalRevealBtn');
  const hidden = ans.style.display === 'none';
  ans.style.display = hidden ? 'block' : 'none';
  btn.textContent = hidden ? '🙈 Hide Answer' : '👁 Reveal Answer';
}

function openQuizFromModal() {
  closeModal('questionModal');
  switchView('quiz');
  // Pre-load the question into quiz mode
  if (currentQuestion) displayQuizQuestion(currentQuestion);
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

async function startQuiz() {
  const topic = document.getElementById('quizTopic').value;
  const difficulty = document.getElementById('quizDifficulty').value;

  const res = await fetch(`/api/random?topic=${topic}&difficulty=${difficulty}`);
  if (!res.ok) {
    const d = await res.json();
    alert(d.error || 'No questions found for selected filters.');
    return;
  }
  const q = await res.json();
  displayQuizQuestion(q);
}

function displayQuizQuestion(q) {
  currentQuestion = q;
  document.getElementById('quizEmpty').style.display = 'none';
  document.getElementById('quizCard').style.display = 'block';

  document.getElementById('quizCardTopic').textContent = q.topic || 'General';
  document.getElementById('quizCardDiff').textContent = q.difficulty || 'Medium';
  document.getElementById('quizCardDiff').className = `badge-diff ${q.difficulty || ''}`;
  document.getElementById('quizQuestion').textContent = q.question;
  document.getElementById('quizCounter').textContent = `Session: ${sessionAnswered} answered`;

  // Reset state
  document.getElementById('userAnswer').value = '';
  document.getElementById('hintBox').style.display = 'none';
  document.getElementById('hintBtn').textContent = '💡 Get Hint';
  document.getElementById('referenceAnswer').style.display = 'none';
  document.getElementById('refAnswerText').textContent = q.answer;
  document.getElementById('evalResult').style.display = 'none';
  document.getElementById('quizCard').style.animation = 'none';
  void document.getElementById('quizCard').offsetWidth; // reflow
  document.getElementById('quizCard').style.animation = 'fadeIn 0.3s ease';
}

async function getHint() {
  const btn = document.getElementById('hintBtn');
  const box = document.getElementById('hintBox');
  if (box.style.display === 'block') {
    box.style.display = 'none';
    btn.textContent = '💡 Get Hint';
    return;
  }
  btn.textContent = '⏳ Loading...';
  btn.disabled = true;
  try {
    const res = await fetch('/api/hint', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: currentQuestion.question })
    });
    const data = await res.json();
    box.textContent = data.hint || data.error;
    box.style.display = 'block';
    btn.textContent = '🙈 Hide Hint';
  } catch (e) {
    box.textContent = 'Failed to load hint.';
    box.style.display = 'block';
  }
  btn.disabled = false;
}

function revealAnswer() {
  const ref = document.getElementById('referenceAnswer');
  const hidden = ref.style.display === 'none';
  ref.style.display = hidden ? 'block' : 'none';
}

async function evaluateAnswer() {
  const userAnswer = document.getElementById('userAnswer').value.trim();
  if (!userAnswer) {
    document.getElementById('userAnswer').focus();
    document.getElementById('userAnswer').style.borderColor = 'var(--danger)';
    setTimeout(() => document.getElementById('userAnswer').style.borderColor = '', 1500);
    return;
  }

  const btn = document.querySelector('.eval-btn');
  btn.disabled = true;
  btn.textContent = '🤖 Evaluating...';

  try {
    const res = await fetch('/api/evaluate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: currentQuestion.question,
        user_answer: userAnswer,
        correct_answer: currentQuestion.answer
      })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    showEvalResult(data);
    sessionAnswered++;
    document.getElementById('quizCounter').textContent = `Session: ${sessionAnswered} answered`;
  } catch (e) {
    alert('Evaluation failed: ' + e.message);
  }
  btn.disabled = false;
  btn.textContent = '🤖 Evaluate with AI';
}

function showEvalResult(data) {
  const result = document.getElementById('evalResult');
  document.getElementById('scoreNum').textContent = data.score;
  document.getElementById('gradeBadge').textContent = data.grade;
  document.getElementById('gradeBadge').className = `grade-badge grade-${data.grade}`;
  document.getElementById('evalStrengths').textContent = data.strengths || '—';
  document.getElementById('evalImprovements').textContent = data.improvements || '—';
  document.getElementById('evalTip').textContent = data.tip || '—';

  // Color score ring by score
  const ring = document.getElementById('scoreRing');
  const score = parseInt(data.score);
  if (score >= 8) ring.style.borderColor = 'var(--easy)';
  else if (score >= 5) ring.style.borderColor = 'var(--warn)';
  else ring.style.borderColor = 'var(--danger)';
  document.getElementById('scoreNum').style.color = ring.style.borderColor;

  result.style.display = 'block';
  result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function nextQuestion() {
  const topic = document.getElementById('quizTopic').value;
  const difficulty = document.getElementById('quizDifficulty').value;
  const res = await fetch(`/api/random?topic=${topic}&difficulty=${difficulty}`);
  if (!res.ok) return;
  const q = await res.json();
  displayQuizQuestion(q);
}

async function loadStats() {
  const grid = document.getElementById('statsGrid');
  grid.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading...</p></div>';

  const res = await fetch('/api/stats');
  const data = await res.json();

  const topicMax = Math.max(...Object.values(data.by_topic));
  const diffColors = { Easy: 'var(--easy)', Medium: 'var(--warn)', Hard: 'var(--hard)' };
  const topicColors = ['#00e5ff', '#7c3aed', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#84cc16'];

  grid.innerHTML = `
    <div class="stat-card">
      <div class="stat-card-title">Total Questions</div>
      <div class="stat-total">${data.total}</div>
    </div>
    <div class="stat-card">
      <div class="stat-card-title">By Difficulty</div>
      ${Object.entries(data.by_difficulty).map(([k, v]) => `
        <div class="stat-row">
          <span class="stat-key">${k}</span>
          <div class="stat-bar-bg"><div class="stat-bar-fill" style="width:${Math.round(v/data.total*100)}%;background:${diffColors[k]||'var(--accent)'}"></div></div>
          <span class="stat-val">${v}</span>
        </div>`).join('')}
    </div>
    <div class="stat-card" style="grid-column: span 2;">
      <div class="stat-card-title">By Topic</div>
      ${Object.entries(data.by_topic).sort((a,b)=>b[1]-a[1]).map(([k, v], i) => `
        <div class="stat-row">
          <span class="stat-key">${k}</span>
          <div class="stat-bar-bg"><div class="stat-bar-fill" style="width:${Math.round(v/topicMax*100)}%;background:${topicColors[i%topicColors.length]}"></div></div>
          <span class="stat-val">${v}</span>
        </div>`).join('')}
    </div>
  `;

  // Animate bars
  setTimeout(() => {
    document.querySelectorAll('.stat-bar-fill').forEach(b => {
      const w = b.style.width;
      b.style.width = '0';
      setTimeout(() => b.style.width = w, 50);
    });
  }, 100);
}

async function handleUpload(input) {
  const file = input.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);
  const status = document.getElementById('uploadStatus');
  status.textContent = 'Uploading...';
  status.className = 'upload-status';
  try {
    const res = await fetch('/upload', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.success) {
      status.textContent = `✓ Loaded ${data.loaded} questions successfully!`;
      status.className = 'upload-status success';
      document.getElementById('headerCount').textContent = `${data.loaded} Questions`;
      setTimeout(() => { closeModal('uploadModal'); location.reload(); }, 1500);
    } else {
      status.textContent = `✗ ${data.error}`;
      status.className = 'upload-status error';
    }
  } catch (e) {
    status.textContent = '✗ Upload failed. Try again.';
    status.className = 'upload-status error';
  }
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal.open').forEach(m => m.classList.remove('open'));
  }
});

loadQuestions();
