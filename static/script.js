document.addEventListener('DOMContentLoaded', () => {
    const yearSelect = document.getElementById('year');
    const monthSelect = document.getElementById('month');
    const daySelect = document.getElementById('day');
    const hourSelect = document.getElementById('hour');
    const minuteInput = document.getElementById('minute');
    const fortuneForm = document.getElementById('fortune-form');
    const statusBox = document.getElementById('fortune-status');
    const calendarRadios = document.querySelectorAll('input[name="calendar_type"]');
    const leapCheckbox = document.getElementById('is_leap');
    const navToggle = document.querySelector('.nav-toggle');

    const resultPage = document.getElementById('saju-result-page');
    const pillarGrid = document.getElementById('pillar-grid');
    const elementBars = document.getElementById('element-bars');
    const relationList = document.getElementById('relation-list');
    const adviceList = document.getElementById('advice-list');
    const luckTable = document.getElementById('luck-table');

    const elementLabels = {
        목: '木 목',
        화: '火 화',
        토: '土 토',
        금: '金 금',
        수: '水 수',
    };

    navToggle?.addEventListener('click', () => {
        document.body.classList.toggle('nav-open');
    });

    document.querySelectorAll('.nav-links a').forEach((link) => {
        link.addEventListener('click', () => document.body.classList.remove('nav-open'));
    });

    document.querySelectorAll('.concern-card').forEach((card) => {
        card.addEventListener('click', () => {
            const key = card.dataset.concern;
            document.querySelectorAll('.concern-card').forEach((item) => item.classList.toggle('active', item === card));
            document.querySelectorAll('.empathy-card').forEach((panel) => {
                panel.classList.toggle('active', panel.dataset.concernPanel === key);
            });
            document.getElementById('concern-detail')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    function fillOptions() {
        if (!yearSelect || !monthSelect || !hourSelect) return;
        const currentYear = new Date().getFullYear();
        yearSelect.innerHTML = '';
        monthSelect.innerHTML = '';
        hourSelect.innerHTML = '';

        for (let y = Math.min(currentYear, 2050); y >= 1900; y--) {
            const opt = document.createElement('option');
            opt.value = y;
            opt.textContent = `${y}년`;
            yearSelect.appendChild(opt);
        }
        for (let m = 1; m <= 12; m++) {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = `${m}월`;
            monthSelect.appendChild(opt);
        }
        for (let h = 0; h <= 23; h++) {
            const opt = document.createElement('option');
            opt.value = h;
            opt.textContent = `${h}시`;
            hourSelect.appendChild(opt);
        }
    }

    function getCalendarType() {
        return document.querySelector('input[name="calendar_type"]:checked')?.value || 'solar';
    }

    function updateDays() {
        if (!yearSelect || !monthSelect || !daySelect) return;
        const year = parseInt(yearSelect.value, 10);
        const month = parseInt(monthSelect.value, 10);
        const currentDay = parseInt(daySelect.value || '1', 10);
        const daysInMonth = getCalendarType() === 'lunar' ? 30 : new Date(year, month, 0).getDate();

        daySelect.innerHTML = '';
        for (let d = 1; d <= daysInMonth; d++) {
            const opt = document.createElement('option');
            opt.value = d;
            opt.textContent = `${d}일`;
            daySelect.appendChild(opt);
        }
        daySelect.value = String(Math.min(currentDay, daysInMonth));
    }

    function updateCalendarMode() {
        const lunarMode = getCalendarType() === 'lunar';
        document.body.classList.toggle('lunar-mode', lunarMode);
        if (leapCheckbox) {
            leapCheckbox.disabled = !lunarMode;
            if (!lunarMode) leapCheckbox.checked = false;
        }
        updateDays();
    }

    function normalizeMinute(value) {
        let minute = parseInt(value, 10);
        if (Number.isNaN(minute)) minute = 0;
        return Math.max(0, Math.min(59, minute));
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value || '-';
    }

    function makeCharTile(charObj, extraClass = '') {
        return `
            <div class="char-tile ${charObj.css || ''} ${extraClass}">
                <span class="hanja">${charObj.hanja}</span>
                <span class="ko">${charObj.ko} · ${charObj.element}${charObj.yin_yang}</span>
            </div>
        `;
    }

    function renderPillars(data) {
        pillarGrid.innerHTML = (data.visual_pillars || []).map((pillar) => {
            const hidden = pillar.hidden_stems?.length
                ? pillar.hidden_stems.map((h) => `<span class="hidden-stem ${h.css}">${h.hanja} ${h.ko}<small>${h.ten_god}</small></span>`).join('')
                : '<span class="hidden-stem empty">-</span>';

            return `
                <article class="pillar-card ${pillar.key === 'day' ? 'day-pillar' : ''}">
                    <div class="pillar-head">
                        <strong>${pillar.label}</strong>
                        <span>${pillar.role}</span>
                    </div>
                    <div class="ten-god top">${pillar.stem_ten_god || '-'}</div>
                    ${makeCharTile(pillar.stem, 'stem-tile')}
                    ${makeCharTile(pillar.branch, 'branch-tile')}
                    <div class="ten-god bottom">${pillar.branch_ten_god || '-'}</div>
                    <div class="pillar-detail"><span>지장간</span><div>${hidden}</div></div>
                    <div class="pillar-detail"><span>12운성</span><strong>${pillar.twelve_stage || '-'}</strong></div>
                </article>
            `;
        }).join('');
    }

    function renderElements(data) {
        const counts = data.element_counts || {};
        const maxValue = Math.max(1, ...Object.values(counts));
        elementBars.innerHTML = ['목', '화', '토', '금', '수'].map((el) => {
            const count = counts[el] || 0;
            const width = Math.max(8, Math.round((count / maxValue) * 100));
            return `
                <div class="element-line">
                    <span class="element-name">${elementLabels[el]}</span>
                    <div class="bar-track"><div class="bar-fill el-${el}" style="width:${width}%"></div></div>
                    <strong>${count}</strong>
                </div>
            `;
        }).join('');

        const strong = (data.strong_elements || []).join(', ') || '-';
        const weak = (data.weak_elements || []).join(', ') || '-';
        const missing = (data.missing_elements?.무자 || []).join(', ') || '없음';
        setText('element-summary-text', `강한 오행은 ${strong}, 약한 오행은 ${weak}, 없는 오행은 ${missing}입니다. 이 분포는 자주 쓰는 힘과 의식적으로 보완할 힘을 보여줍니다.`);
    }

    function renderRelations(data) {
        const rel = data.relations || {};
        const rows = [];
        Object.entries(rel).forEach(([key, values]) => {
            (values || []).forEach((value) => rows.push(`<li><strong>${key}</strong><span>${value}</span></li>`));
        });
        relationList.innerHTML = rows.length
            ? rows.join('')
            : '<li><strong>안정</strong><span>기본 원국에서 두드러진 합·충·형이 적게 나타납니다. 실제 상담에서는 대운·세운까지 함께 확인합니다.</span></li>';
    }

    function renderLuck(data) {
        if (!luckTable) return;
        const luck = data.luck_cycle || [];

        // 현재 나이 계산 (양력 기준)
        let birthYear = null;
        try { birthYear = parseInt((data.converted_solar || '').split('-')[0], 10); } catch (e) {}
        const nowYear = new Date().getFullYear();
        const currentAge = birthYear ? (nowYear - birthYear + 1) : null;

        luckTable.innerHTML = luck.map((item) => {
            const startAge = typeof item.age === 'number' ? item.age : parseInt(item.age, 10);
            const endAge   = startAge + 9;
            const isCur    = currentAge !== null && currentAge >= startAge && currentAge <= endAge;
            return `
                <article class="luck-card ${isCur ? 'current-luck' : ''}">
                    <span>${startAge}~${endAge}세</span>
                    <strong>${item.ganji || (item.stem + item.branch)} ${item.hanja || ''}</strong>
                    <small>십성 ${item.ten_god || '-'} · 12운성 ${item.twelve_stage || '-'}</small>
                    <small style="color:var(--muted)">${item.direction || ''}</small>
                </article>`;
        }).join('');

        const current = data.current_luck || luck[0];
        if (current) {
            setText('current-luck-copy',
                `${current.age}세부터 ${current.ganji || ''}(${current.hanja || ''}) 대운입니다. ` +
                `십성 ${current.ten_god || '-'}, 12운성 ${current.twelve_stage || '-'}. ` +
                `${current.description || '대운의 흐름을 상담 주제와 함께 살펴봅니다.'}`);
        }
    }

    function renderAdvice(data) {
        adviceList.innerHTML = (data.advice || []).map((line, idx) => `
            <div class="advice-card"><span>${idx + 1}</span><p>${line}</p></div>
        `).join('');
    }

    // 신살 렌더링
    function renderShinsal(data) {
        const el = document.getElementById('shinsal-list');
        if (!el) return;
        const shinsal = data.shinsal || [];
        if (!shinsal.length) { el.innerHTML = '<span style="color:#888">-</span>'; return; }
        el.innerHTML = shinsal.map(s =>
            `<span class="shinsal-tag">${s}</span>`
        ).join('');
    }

    // 세운 렌더링
    function renderAnnualFortune(data) {
        const el = document.getElementById('annual-fortune');
        if (!el) return;
        const af = data.annual_fortune || {};
        if (!af.간지) { el.innerHTML = '-'; return; }
        el.innerHTML = `
            <strong>${af.년도 || ''}</strong>
            <span class="luck-ganji">${af.간지 || ''}</span>
            <span class="luck-god">${af.십성 || ''}</span>
            <small>${af.나이 || ''}</small>`;
    }

    function renderResult(data) {
        resultPage.hidden = false;
        const options = data.input?.options || {};
        const optionText = Object.entries(options).map(([key, value]) => `${key}: ${value}`).join(' / ');

        setText('meta-input', data.input?.label);
        setText('meta-solar', data.converted_solar);
        setText('meta-lunar', data.lunar_date);
        setText('meta-gender', data.input?.gender);
        setText('meta-place', data.input?.birth_place);
        setText('meta-options', optionText);
        setText('calculation-note', `${data.calculation_note?.summary || ''} ${data.calculation_note?.detail || ''}${data.calculation_note?.reference_matched ? ' 기준 검증값과 일치하도록 보정되었습니다.' : ''}`);

        const dayMaster = data.day_master || {};
        setText('result-title', `${dayMaster.일간 || '-'}일간 · ${dayMaster.hanja || ''}의 사주 원국`);
        setText('result-subtitle', '시주 · 일주 · 월주 · 년주를 이미지형 만세력 카드로 정리했습니다.');

        renderPillars(data);
        renderElements(data);
        renderRelations(data);
        renderLuck(data);
        renderAdvice(data);
        renderShinsal(data);
        renderAnnualFortune(data);

        setText('day-master-copy', `${dayMaster.일간 || '-'}(${dayMaster.hanja || ''}) 일간입니다. ${dayMaster.description || dayMaster.특성 || ''}`);
        setText('pattern-copy', `${data.pattern?.격 || '-'}: ${data.pattern?.특성 || ''}`);

        setTimeout(() => resultPage.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    }

    fillOptions();
    updateDays();
    updateCalendarMode();

    yearSelect?.addEventListener('change', updateDays);
    monthSelect?.addEventListener('change', updateDays);
    calendarRadios.forEach((radio) => radio.addEventListener('change', updateCalendarMode));
    minuteInput?.addEventListener('change', () => {
        minuteInput.value = normalizeMinute(minuteInput.value);
    });
    document.getElementById('result-print')?.addEventListener('click', () => window.print());

    fortuneForm?.addEventListener('submit', async (event) => {
        event.preventDefault();
        statusBox.textContent = '전체 결과 화면을 준비 중입니다...';
        statusBox.classList.add('active');

        const formData = new FormData(fortuneForm);
        const payload = {
            calendar_type: formData.get('calendar_type'),
            is_leap: formData.get('is_leap') === 'on',
            year: formData.get('year'),
            month: formData.get('month'),
            day: formData.get('day'),
            hour: formData.get('hour'),
            minute: normalizeMinute(formData.get('minute')),
            gender: formData.get('gender'),
            birth_place: formData.get('birth_place'),
            use_true_solar_time: formData.get('use_true_solar_time') === 'on',
            night_hour_rule: formData.get('night_hour_rule'),
            next_day_after_23: formData.get('next_day_after_23') === 'on',
        };

        try {
            const response = await fetch('/fortune', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const json = await response.json();
            if (!response.ok) throw new Error(json.error || '오류가 발생했습니다');
            statusBox.textContent = '분석 완료. 아래 전체 결과 화면으로 이동합니다.';
            renderResult(json);
        } catch (error) {
            statusBox.textContent = `오류: ${error.message}`;
        }
    });
});
