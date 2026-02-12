// =============================================
// GBI 로보 어드바이저 - Frontend Logic
// =============================================

const API_BASE = '/api/v1';

const state = {
  goalInput: null,
  gapResult: null,
  optimizationResult: null,
  simulationResult: null,
};

let allocationChartInstance = null;
let simulationChartInstance = null;

// =============================================
// Utilities
// =============================================

function formatKRW(value) {
  const man = Math.round(value / 10000);
  if (man >= 10000) {
    const uk = Math.floor(man / 10000);
    const remainder = man % 10000;
    return remainder > 0
      ? `${uk}억 ${remainder.toLocaleString()}만원`
      : `${uk}억원`;
  }
  return `${man.toLocaleString()}만원`;
}

function formatPercent(value) {
  return `${(value * 100).toFixed(2)}%`;
}

function setButtonLoading(buttonId, loading) {
  const btn = document.getElementById(buttonId);
  if (loading) {
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
  } else {
    btn.removeAttribute('aria-busy');
    btn.disabled = false;
  }
}

function showError(message) {
  const existing = document.getElementById('error-banner');
  if (existing) existing.remove();

  const banner = document.createElement('div');
  banner.id = 'error-banner';
  banner.className = 'error-banner';
  banner.setAttribute('role', 'alert');
  banner.innerHTML = `<p>${message}</p><button class="secondary outline" onclick="this.parentElement.remove()">닫기</button>`;
  document.querySelector('main').prepend(banner);
}

async function apiPost(endpoint, body) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// =============================================
// Step Navigation
// =============================================

function showStep(stepNumber) {
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  document.getElementById(`step-${stepNumber}`).classList.add('active');

  document.querySelectorAll('#step-nav li').forEach(li => {
    const liStep = parseInt(li.dataset.step);
    li.classList.remove('active', 'completed');
    if (liStep === stepNumber) li.classList.add('active');
    else if (liStep < stepNumber) li.classList.add('completed');
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Back buttons
document.querySelectorAll('.btn-back').forEach(btn => {
  btn.addEventListener('click', () => {
    showStep(parseInt(btn.dataset.to));
  });
});

// =============================================
// Validation
// =============================================

function validateGoalInput(input) {
  const errors = [];
  if (!input.goal_amount || input.goal_amount <= 0) {
    errors.push('목표 금액은 0보다 커야 합니다.');
  }
  if (!input.time_horizon_months || input.time_horizon_months <= 0) {
    errors.push('목표 기간은 1개월 이상이어야 합니다.');
  }
  if (!input.monthly_contribution || input.monthly_contribution <= 0) {
    errors.push('월 저축 가능액은 0보다 커야 합니다.');
  }
  if (input.initial_principal < 0) {
    errors.push('초기 자본은 0 이상이어야 합니다.');
  }
  if (errors.length > 0) {
    showError(errors.join('\n'));
    return false;
  }
  return true;
}

// =============================================
// Step 1 → Step 2: Gap Analysis
// =============================================

document.getElementById('goal-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const goalInput = {
    goal_amount: parseFloat(document.getElementById('goal_amount').value),
    time_horizon_months: parseInt(document.getElementById('time_horizon_months').value),
    monthly_contribution: parseFloat(document.getElementById('monthly_contribution').value),
    initial_principal: parseFloat(document.getElementById('initial_principal').value) || 0,
    eligible_youth_savings: document.getElementById('eligible_youth_savings').checked,
  };

  if (!validateGoalInput(goalInput)) return;

  state.goalInput = goalInput;
  setButtonLoading('btn-analyze', true);

  try {
    const gapResult = await apiPost('/gap-analysis', goalInput);
    state.gapResult = gapResult;
    renderGapResult(gapResult);
    showStep(2);
  } catch (err) {
    showError('갭 분석 중 오류가 발생했습니다: ' + err.message);
  } finally {
    setButtonLoading('btn-analyze', false);
  }
});

function renderGapResult(result) {
  document.getElementById('fv-safe').textContent = formatKRW(result.future_value_safe);
  document.getElementById('fv-goal').textContent = formatKRW(result.goal_amount);
  document.getElementById('fv-gap').textContent = formatKRW(result.gap);
  document.getElementById('fv-required-return').textContent =
    result.required_annual_return != null ? formatPercent(result.required_annual_return) : '-';

  const summary = document.getElementById('gap-summary');
  const optimizeBtn = document.getElementById('btn-optimize');

  if (result.optimization_needed) {
    summary.innerHTML = `
      <h3>최적화가 필요합니다</h3>
      <p>안전자산만으로는 목표 금액에 <strong>${formatKRW(result.gap)}</strong> 부족합니다.</p>
      <p>듀레이션 매칭 포트폴리오로 목표 달성을 도와드리겠습니다.</p>`;
    summary.className = 'warning';
    optimizeBtn.disabled = false;
    optimizeBtn.textContent = '포트폴리오 최적화';
  } else {
    summary.innerHTML = `
      <h3>축하합니다!</h3>
      <p>안전자산(예금)만으로 목표 금액 달성이 가능합니다.</p>
      <p>예상 미래가치: <strong>${formatKRW(result.future_value_safe)}</strong></p>`;
    summary.className = 'success';
    optimizeBtn.disabled = true;
    optimizeBtn.textContent = '최적화 불필요';
  }
}

// =============================================
// Step 2 → Step 3: Optimize
// =============================================

document.getElementById('btn-optimize').addEventListener('click', async () => {
  setButtonLoading('btn-optimize', true);

  try {
    const result = await apiPost('/optimize', state.goalInput);
    state.optimizationResult = result;

    if (!result.success) {
      showError(result.message);
      return;
    }

    renderOptimizationResult(result);
    showStep(3);
  } catch (err) {
    showError('포트폴리오 최적화 중 오류가 발생했습니다: ' + err.message);
  } finally {
    setButtonLoading('btn-optimize', false);
  }
});

function renderOptimizationResult(result) {
  // Summary stats
  document.getElementById('stat-duration').textContent =
    `${result.portfolio_duration.toFixed(2)}년`;
  document.getElementById('stat-return').textContent =
    formatPercent(result.portfolio_return);
  document.getElementById('stat-fv').textContent =
    formatKRW(result.expected_future_value);

  // Allocation table
  const tbody = document.querySelector('#allocation-table tbody');
  tbody.innerHTML = '';
  result.allocations.forEach(a => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${a.name}</td>
      <td>${(a.weight * 100).toFixed(1)}%</td>
      <td>${formatKRW(a.monthly_amount)}</td>
      <td class="hide-mobile">${a.duration_contribution.toFixed(2)}년</td>
      <td>${formatPercent(a.after_tax_return)}</td>`;
    tbody.appendChild(tr);
  });

  // Pie chart
  renderAllocationChart(result.allocations);
}

function renderAllocationChart(allocations) {
  if (allocationChartInstance) {
    allocationChartInstance.destroy();
  }

  const ctx = document.getElementById('allocation-chart').getContext('2d');
  const colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#00BCD4'];

  allocationChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: allocations.map(a => a.name),
      datasets: [{
        data: allocations.map(a => (a.weight * 100).toFixed(1)),
        backgroundColor: colors.slice(0, allocations.length),
        borderWidth: 2,
        borderColor: '#ffffff',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { size: 13 } }
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const alloc = allocations[context.dataIndex];
              return `${alloc.name}: ${(alloc.weight * 100).toFixed(1)}% (월 ${formatKRW(alloc.monthly_amount)})`;
            }
          }
        }
      }
    }
  });
}

// =============================================
// Step 3 → Step 4: Simulation
// =============================================

document.getElementById('btn-simulate').addEventListener('click', async () => {
  setButtonLoading('btn-simulate', true);

  try {
    const simRequest = { ...state.goalInput };
    const result = await apiPost('/simulate', simRequest);
    state.simulationResult = result;
    renderSimulationResult(result);
    showStep(4);
  } catch (err) {
    showError('시뮬레이션 중 오류가 발생했습니다: ' + err.message);
  } finally {
    setButtonLoading('btn-simulate', false);
  }
});

function renderSimulationResult(result) {
  document.getElementById('sim-base-rate').textContent = formatPercent(result.base_rate);

  // Table
  const tbody = document.querySelector('#simulation-table tbody');
  tbody.innerHTML = '';
  result.results.forEach(r => {
    const tr = document.createElement('tr');
    const diffClass = r.difference >= 0 ? 'positive' : 'negative';
    const diffSign = r.difference >= 0 ? '+' : '';
    tr.innerHTML = `
      <td>${r.label}</td>
      <td>${(r.rate_shift * 100).toFixed(1)}%p</td>
      <td class="hide-mobile">${formatPercent(r.new_rate)}</td>
      <td>${formatKRW(r.simple_savings_fv)}</td>
      <td>${formatKRW(r.portfolio_fv)}</td>
      <td class="${diffClass}">${diffSign}${formatKRW(r.difference)}</td>`;
    tbody.appendChild(tr);
  });

  // Bar chart
  renderSimulationChart(result);
}

function renderSimulationChart(simResult) {
  if (simulationChartInstance) {
    simulationChartInstance.destroy();
  }

  const ctx = document.getElementById('simulation-chart').getContext('2d');
  const labels = simResult.results.map(r => r.label);

  simulationChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: '단순 적금',
          data: simResult.results.map(r => r.simple_savings_fv),
          backgroundColor: '#90CAF9',
          borderColor: '#1565C0',
          borderWidth: 1,
        },
        {
          label: 'GBI 포트폴리오',
          data: simResult.results.map(r => r.portfolio_fv),
          backgroundColor: '#A5D6A7',
          borderColor: '#2E7D32',
          borderWidth: 1,
        },
        {
          label: '목표 금액',
          data: simResult.results.map(() => state.goalInput.goal_amount),
          type: 'line',
          borderColor: '#E53935',
          borderWidth: 2,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        y: {
          beginAtZero: false,
          ticks: {
            callback: function (value) {
              return formatKRW(value);
            }
          },
        }
      },
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: function (context) {
              return `${context.dataset.label}: ${formatKRW(context.parsed.y)}`;
            }
          }
        }
      }
    }
  });
}

// =============================================
// Restart
// =============================================

document.getElementById('btn-restart').addEventListener('click', () => {
  state.goalInput = null;
  state.gapResult = null;
  state.optimizationResult = null;
  state.simulationResult = null;

  if (allocationChartInstance) {
    allocationChartInstance.destroy();
    allocationChartInstance = null;
  }
  if (simulationChartInstance) {
    simulationChartInstance.destroy();
    simulationChartInstance = null;
  }

  document.getElementById('goal-form').reset();
  showStep(1);
});
