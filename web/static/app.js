/**
 * ═══════════════════════════════════════════════════════════════
 *  Gauss - 前端交互逻辑
 *  SSE 事件流处理 + 三面板渲染
 * ═══════════════════════════════════════════════════════════════
 */

// ─── 状态 ───
let currentSessionId = null;
let eventSource = null;
let isRunning = false;

// ─── DOM ───
const $ = (sel) => document.querySelector(sel);
const theoremInput   = $('#theoremInput');
const btnProve       = $('#btnProve');
const btnClear       = $('#btnClear');
const statusDot      = $('#statusDot');
const statusText     = $('#statusText');
const llmPanel       = $('#llmPanel');
const planPanel      = $('#planPanel');
const leanStmtPanel  = $('#leanStmtPanel');
const leanProofPanel = $('#leanProofPanel');
const llmSubtitle    = $('#llmSubtitle');
const planSubtitle   = $('#planSubtitle');
const leanStmtSubtitle  = $('#leanStmtSubtitle');
const leanProofSubtitle = $('#leanProofSubtitle');
const modelBadge     = $('#modelBadge');

// 底部错误分析面板 DOM
const errorBody    = $('#errorBody');
const errorCount   = $('#errorCount');
const errorPanel   = $('#errorPanel');

// 错误计数
let totalErrorCount = 0;

// ─── 初始化 ───
document.addEventListener('DOMContentLoaded', () => {
  loadConfig();
  clearErrorPanel();
  initBottomDividerDrag();

  // 快捷键: Ctrl/Cmd + Enter 开始证明
  theoremInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      startProve();
    }
  });

  // 分割线拖拽
  initDividerDrag('panelDivider1');
  initDividerDrag('panelDivider2');
});


// ─── 加载配置 ───
async function loadConfig() {
  try {
    const resp = await fetch('/api/config');
    const config = await resp.json();
    modelBadge.textContent = config.llm?.model_name || 'qwen3-coder:30b';
  } catch (e) {
    // 静默处理
  }
}


// ─── 开始证明 ───
async function startProve() {
  const theorem = theoremInput.value.trim();
  if (!theorem) return;
  if (isRunning) return;

  setRunning(true);
  clearPanels();
  setStatus('running', '正在证明...');

  try {
    // 1. 发起证明请求
    const resp = await fetch('/api/prove', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theorem }),
    });
    const data = await resp.json();

    if (data.error) {
      setStatus('error', data.error);
      setRunning(false);
      return;
    }

    currentSessionId = data.session_id;

    // 2. 连接 SSE 事件流
    connectSSE(currentSessionId);
  } catch (e) {
    setStatus('error', `请求失败: ${e.message}`);
    setRunning(false);
  }
}


// ─── SSE 连接 ───
function connectSSE(sessionId) {
  if (eventSource) {
    eventSource.close();
  }

  eventSource = new EventSource(`/api/prove/stream?session_id=${sessionId}`);

  eventSource.onmessage = (e) => {
    let evt;
    try {
      evt = JSON.parse(e.data);
    } catch {
      return;
    }

    if (evt.event_type === 'done') {
      eventSource.close();
      eventSource = null;
      setRunning(false);
      // 检查最后的状态
      const lastLlm = getLastEventType('llm');
      const lastLean = getLastEventType('lean');
      if (lastLlm === 'success' || lastLean === 'success') {
        setStatus('success', '证明完成');
      } else if (totalErrorCount > 0) {
        setStatus('error', '证明失败');
      } else {
        setStatus('success', '执行完毕');
      }
      return;
    }

    renderEvent(evt);
  };

  eventSource.onerror = () => {
    eventSource.close();
    eventSource = null;
    setRunning(false);
    setStatus('error', '连接中断');
  };
}


// ─── 渲染事件 ───
function renderEvent(evt) {
  // 确定目标面板和副标题
  let panel, subtitle, panelKey;
  if (evt.side === 'llm') {
    panel = llmPanel;
    subtitle = llmSubtitle;
    panelKey = 'llm';
  } else if (evt.side === 'plan') {
    panel = planPanel;
    subtitle = planSubtitle;
    panelKey = 'plan';
  } else if (evt.event_type === 'lean-stmt') {
    panel = leanStmtPanel;
    subtitle = leanStmtSubtitle;
    panelKey = 'leanStmt';
  } else {
    // lean-proof 以及其他 lean 侧事件都进证明面板
    panel = leanProofPanel;
    subtitle = leanProofSubtitle;
    panelKey = 'leanProof';
  }

  // ── 每次刷新替代原有内容 ──
  // nl-proof / lean-stmt：替换整个面板
  // code（新一轮形式化/修正）：清空证明面板重新开始
  if (evt.event_type === 'nl-proof' || evt.event_type === 'lean-stmt' || evt.event_type === 'code') {
    panel.innerHTML = '';
  } else {
    // 其他事件只移除空状态占位
    const empty = panel.querySelector('.empty-state');
    if (empty) empty.remove();
  }

  // 错误事件 → 仅送到底部错误面板
  if (evt.event_type === 'error') {
    renderErrorToAnalysis(evt, panelKey, subtitle);
    return;
  }

  // 验证失败的 tactic（✗ 开头）→ 仅送到底部错误面板
  const isFailedTactic = evt.event_type === 'tactic' && evt.content.startsWith('✗');
  if (isFailedTactic) {
    renderErrorToAnalysis(evt, panelKey, subtitle);
    return;
  }

  // 错误分析 info → 仅送到底部错误面板
  const isErrorAnalysis = evt.event_type === 'info' && (evt.detail === '智能体诊断' || evt.content.includes('错误分析'));
  if (isErrorAnalysis) {
    renderErrorToAnalysis(evt, panelKey, subtitle);
    return;
  }

  const el = document.createElement('div');
  el.classList.add('event-item');
  el.dataset.eventType = evt.event_type;
  el.dataset.side = evt.side;

  switch (evt.event_type) {
    case 'info':
      el.classList.add('event-info');
      el.insertAdjacentText('beforeend', evt.content);
      subtitle.textContent = evt.content;
      break;

    case 'step':
      el.classList.add('event-step');
      el.insertAdjacentText('beforeend', evt.content);
      subtitle.textContent = evt.content;
      break;

    case 'nl-proof':
      el.classList.add('event-nl-proof');
      const proofLabel = evt.detail || (evt.side === 'plan' ? '结构化证明计划' : '自然语言证明');
      el.insertAdjacentHTML('beforeend', `
        <div class="nl-proof-label">${escapeHtml(proofLabel)}</div>
        <div class="nl-proof-body">${formatNlProof(evt.content)}</div>
      `);
      subtitle.textContent = evt.side === 'plan' ? '已生成证明计划' : '已生成自然语言证明';
      break;

    case 'lean-stmt':
      el.classList.add('event-code');
      el.insertAdjacentHTML('beforeend', `
        <pre>${escapeHtml(evt.content)}</pre>
      `);
      subtitle.textContent = '已生成 Lean 表示';
      break;

    case 'code':
      el.classList.add('event-code');
      el.insertAdjacentHTML('beforeend', `
        <div class="code-label">${escapeHtml(evt.detail || '代码')}</div>
        <pre>${escapeHtml(evt.content)}</pre>
      `);
      break;

    case 'tactic':
      el.classList.add('event-tactic');
      if (evt.content.startsWith('✓')) {
        el.classList.add('tactic-success');
      } else if (evt.content.startsWith('✗')) {
        el.classList.add('tactic-fail');
      } else if (evt.content.startsWith('⏭')) {
        el.classList.add('tactic-pending');
      } else {
        el.classList.add('tactic-pending');
      }
      el.insertAdjacentHTML('beforeend', escapeHtml(evt.content));
      if (evt.detail && evt.detail !== evt.content) {
        el.insertAdjacentHTML('beforeend', `<div class="tactic-detail">${escapeHtml(evt.detail)}</div>`);
      }
      break;

    case 'success':
      el.classList.add('event-success');
      el.insertAdjacentText('beforeend', evt.content);
      subtitle.textContent = evt.content;
      break;

    default:
      el.classList.add('event-info');
      el.insertAdjacentText('beforeend', evt.content);
  }

  panel.appendChild(el);

  // 自动滚动到底部
  requestAnimationFrame(() => {
    panel.scrollTop = panel.scrollHeight;
  });
}


// ─── 工具函数 ───

function clearAll() {
  clearPanels();
  theoremInput.value = '';
  setStatus('', '就绪');
  theoremInput.focus();
}

function clearPanels() {
  llmPanel.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">🧠</div>
      <div class="empty-text">LLM 自然语言证明将在此显示</div>
      <div class="empty-hint">LLM 给出完整的数学证明思路</div>
    </div>`;
  planPanel.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">📋</div>
      <div class="empty-text">结构化证明计划将在此显示</div>
      <div class="empty-hint">目标定理、关键引理、证明步骤</div>
    </div>`;
  leanStmtPanel.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">📐</div>
      <div class="empty-text">定理的 Lean 4 形式化表述</div>
    </div>`;
  leanProofPanel.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">⚙️</div>
      <div class="empty-text">Lean 4 证明步骤</div>
    </div>`;
  llmSubtitle.textContent = '等待输入...';
  planSubtitle.textContent = '等待输入...';
  leanStmtSubtitle.textContent = '等待输入...';
  leanProofSubtitle.textContent = '等待输入...';

  // 清空错误分析
  clearErrorPanel();
}

function setRunning(running) {
  isRunning = running;
  btnProve.disabled = running;
}

function setStatus(type, text) {
  statusDot.className = 'status-dot' + (type ? ` ${type}` : '');
  statusText.textContent = text;
}

function getLastEventType(side) {
  let container;
  if (side === 'llm') {
    container = llmPanel;
  } else {
    container = leanProofPanel;
  }
  const items = container.querySelectorAll('.event-item');
  if (items.length === 0) return null;
  return items[items.length - 1].dataset.eventType;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatNlProof(text) {
  // 将结构化证明计划格式化为 HTML
  let html = escapeHtml(text);
  // ## 标题 → <h3>
  html = html.replace(/^## (.+)$/gm, '<h3 class="plan-heading">$1</h3>');
  // 换行变 <br>（但 <h3> 后面不需要额外 <br>）
  html = html.replace(/\n/g, '<br>');
  html = html.replace(/<\/h3><br>/g, '</h3>');
  // 加粗: **text** → <strong>text</strong>
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // - 列表项高亮
  html = html.replace(/^- /gm, '• ');
  return html;
}

// ─── 底部错误分析面板 ───

function renderErrorToAnalysis(evt, panelKey, subtitle) {
  // 移除空提示
  const emptyMsg = errorBody.querySelector('.error-panel-empty');
  if (emptyMsg) emptyMsg.remove();

  // 增加计数
  totalErrorCount++;
  errorCount.textContent = totalErrorCount;
  errorCount.classList.remove('zero');

  // 展开面板
  errorPanel.classList.remove('collapsed');

  // 确定来源标签
  let sourceLabel, sourceClass;
  if (panelKey === 'llm') {
    sourceLabel = 'LLM';
    sourceClass = 'source-llm';
  } else if (panelKey === 'plan') {
    sourceLabel = 'Plan';
    sourceClass = 'source-plan';
  } else {
    sourceLabel = 'Lean';
    sourceClass = 'source-lean';
  }

  // 确定条目类型样式
  let itemClass = 'error-item';
  if (evt.event_type === 'info' && (evt.detail === '智能体诊断' || evt.content.includes('错误分析'))) {
    itemClass = 'error-item error-item-analysis';
  } else if (evt.event_type === 'tactic') {
    itemClass = 'error-item error-item-verify';
  }

  // 创建错误条目
  const item = document.createElement('div');
  item.className = itemClass;

  const numEl = document.createElement('span');
  numEl.className = 'error-item-num';
  numEl.textContent = totalErrorCount;
  item.appendChild(numEl);

  const contentEl = document.createElement('div');
  contentEl.className = 'error-item-content';

  const sourceEl = document.createElement('span');
  sourceEl.className = `error-item-source ${sourceClass}`;
  sourceEl.textContent = sourceLabel;
  contentEl.appendChild(sourceEl);

  const typeEl = document.createElement('span');
  typeEl.className = 'error-item-type';
  typeEl.textContent = evt.content;
  contentEl.appendChild(typeEl);

  if (evt.detail) {
    const detailEl = document.createElement('div');
    detailEl.className = 'error-item-detail';
    detailEl.textContent = evt.detail;
    contentEl.appendChild(detailEl);
  }

  item.appendChild(contentEl);
  errorBody.appendChild(item);

  // 只有纯 error 类型才更新副标题
  if (evt.event_type === 'error') {
    subtitle.textContent = evt.content;
  }

  // 自动滚动到底
  requestAnimationFrame(() => {
    errorBody.scrollTop = errorBody.scrollHeight;
  });
}

function clearErrorPanel() {
  totalErrorCount = 0;
  errorBody.innerHTML = '<div class="error-panel-empty">暂无错误</div>';
  errorCount.textContent = '0';
  errorCount.classList.add('zero');
  errorPanel.classList.add('collapsed');
}

function toggleErrorPanel() {
  errorPanel.classList.toggle('collapsed');
}

// ─── 底部分割线拖拽（调整错误面板高度） ───
function initBottomDividerDrag() {
  const divider = document.getElementById('bottomDivider');
  if (!divider) return;
  let isDragging = false;

  divider.addEventListener('mousedown', (e) => {
    isDragging = true;
    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const windowH = window.innerHeight;
    let newH = windowH - e.clientY;
    newH = Math.max(32, Math.min(newH, windowH * 0.5));
    errorPanel.style.height = newH + 'px';
    if (newH <= 40) {
      errorPanel.classList.add('collapsed');
    } else {
      errorPanel.classList.remove('collapsed');
    }
  });

  document.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }
  });
}

// ─── 分割线拖拽 ───
function initDividerDrag(dividerId) {
  const divider = document.getElementById(dividerId);
  if (!divider) return;
  const panels = document.querySelector('.panels');
  let isDragging = false;

  // 找到分割线左右相邻的 panel
  function getSiblings() {
    const prev = divider.previousElementSibling;
    const next = divider.nextElementSibling;
    return { prev, next };
  }

  divider.addEventListener('mousedown', (e) => {
    isDragging = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const { prev, next } = getSiblings();
    if (!prev || !next) return;
    const panelsRect = panels.getBoundingClientRect();
    const totalW = panelsRect.width;
    const mouseX = e.clientX - panelsRect.left;

    // 计算 prev 的新宽度
    const prevLeft = prev.getBoundingClientRect().left - panelsRect.left;
    let newPrevW = mouseX - prevLeft;
    newPrevW = Math.max(120, Math.min(newPrevW, totalW - 240));

    prev.style.flex = `0 0 ${newPrevW}px`;
  });

  document.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }
  });
}
