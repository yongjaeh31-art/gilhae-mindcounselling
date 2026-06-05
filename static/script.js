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
        // 새 ID: element-bars-v2 (없으면 기존 element-bars 사용)
        const bars = document.getElementById('element-bars') || document.getElementById('element-bars-v2');
        if (!bars) return;
        const counts = data.element_counts || {};
        const maxValue = Math.max(1, ...Object.values(counts));

        bars.innerHTML = ['목', '화', '토', '금', '수'].map(el => {
            const count = counts[el] || 0;
            // 0이면 바 너비 0 (색 안 들어감), 1 이상이면 최소 12%
            const pct = count === 0 ? 0 : Math.max(12, Math.round((count / maxValue) * 100));
            return `
                <div class="element-line">
                    <span class="element-name">${elementLabels[el]}</span>
                    <div class="bar-track">
                        <div class="bar-fill el-${el}" style="width:0%" data-w="${pct}"></div>
                    </div>
                    <strong class="element-count">${count}</strong>
                </div>`;
        }).join('');

        // 애니메이션
        setTimeout(() => {
            bars.querySelectorAll('.bar-fill').forEach(b => {
                b.style.width = b.dataset.w + '%';
            });
        }, 120);

        const strong  = (data.strong_elements  || []).join(', ') || '-';
        const weak    = (data.weak_elements    || []).join(', ') || '-';
        const missing = (data.missing_elements?.무자 || []).join(', ') || '없음';
        setText('element-summary-text',
            `강 ${strong} / 약 ${weak} / 없음 ${missing}`);
    }

    function renderRelations(data) {
        // 구버전 relation-list (혹시 남아있으면 처리)
        if (relationList) {
            const rel = data.relations || {};
            const rows = [];
            Object.entries(rel).forEach(([key, values]) => {
                (values || []).forEach(v => rows.push(`<li><strong>${key}</strong><span>${v}</span></li>`));
            });
            relationList.innerHTML = rows.length ? rows.join('')
                : '<li><strong>안정</strong><span>두드러진 합·충·형이 없습니다.</span></li>';
        }
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

    // ── 용신 + 강약 렌더링 ──────────────────────────────
    function renderUseGod(data) {
        const el = document.getElementById('use-god-panel');
        const box = document.getElementById('use-god-box');
        const ug = data.use_god_detail || data.use_god || {};
        const ugStr = typeof ug === 'string' ? ug : (ug.용신 || '-');
        const ugSub = ug.종용신 ? ` / 희신: ${ug.종용신}` : '';
        const reason = ug.이유 || '';

        if (el) {
            el.innerHTML = `
                <span class="god-badge god-main">용신 ${ugStr}</span>
                ${ug.종용신 ? `<span class="god-badge god-sub">희신 ${ug.종용신}</span>` : ''}
                ${reason ? `<p style="font-size:.8rem;color:var(--text-soft);margin-top:.4rem">${reason}</p>` : ''}`;
        }
        if (box) {
            const fe = data.five_elements_ratio || {};
            const strong = Object.entries(fe).filter(([,v])=>v>=30).map(([k])=>k).join('·') || '-';
            const weak   = Object.entries(fe).filter(([,v])=>v<=10).map(([k])=>k).join('·') || '-';
            box.innerHTML = `<strong>용신 ${ugStr}${ugSub}</strong><br><span style="font-size:.8rem">강한 오행: ${strong} / 약한 오행: ${weak}</span>`;
        }

        // 강약 지수 (숫자 또는 "신강"/"신약"/"중화신약" 문자열 모두 처리)
        const sp = document.getElementById('strength-panel');
        if (sp) {
            const si = data.strength_index;
            if (si === null || si === undefined) {
                sp.innerHTML = '<span style="color:#aaa">-</span>';
            } else if (typeof si === 'number') {
                const label = si >= 60 ? '신강(身强)' : si <= 40 ? '신약(身弱)' : '중화(中和)';
                const cls   = si >= 60 ? 'strength-strong' : 'strength-weak';
                sp.innerHTML = `
                    <div style="font-weight:800;color:var(--purple)">${label}</div>
                    <div class="strength-bar ${cls}">
                        <div class="strength-fill" style="width:${Math.min(100,Math.max(0,si))}%"></div>
                    </div>
                    <small style="color:var(--text-soft)">${Math.round(si)}점 / 100</small>`;
            } else {
                // 문자열 형식 ("신강", "신약", "중화신약" 등)
                const label = String(si);
                const isStrong = label.includes('신강');
                const isWeak   = label.includes('신약');
                const pct = isStrong ? 75 : isWeak ? 30 : 50;
                const cls = isStrong ? 'strength-strong' : 'strength-weak';
                sp.innerHTML = `
                    <div style="font-weight:800;color:var(--purple)">${label}</div>
                    <div class="strength-bar ${cls}">
                        <div class="strength-fill" style="width:${pct}%"></div>
                    </div>`;
            }
        }
    }

    // ── 형충회합 인라인 렌더링 (원국 바로 아래) ────────
    const REL_META = {
        '충':    { label:'충 (沖)',   cls:'chung',  short:'충' },
        '형':    { label:'형 (刑)',   cls:'hyung',  short:'형' },
        '파':    { label:'파 (破)',   cls:'pa',     short:'파' },
        '해':    { label:'해 (害)',   cls:'hae',    short:'해' },
        '원진':  { label:'원진(怨嗔)',cls:'wonjin', short:'원진' },
        '육합':  { label:'육합(六合)',cls:'hap',    short:'육합' },
        '삼합':  { label:'삼합(三合)',cls:'samhap', short:'삼합' },
        '방합':  { label:'방합(方合)',cls:'banghap',short:'방합' },
        '천간합':{ label:'천간합',   cls:'tiangan',short:'천간합'},
    };

    function renderBranchRelations(data) {
        const inline = document.getElementById('branch-relations-inline');
        if (!inline) return;

        const br   = data.branch_relations || {};
        const rels = data.relations        || {};
        const all  = { ...br };
        if (rels.천간합 && rels.천간합.length) all.천간합 = rels.천간합;

        const parts = [];
        for (const [key, meta] of Object.entries(REL_META)) {
            const items = all[key] || [];
            if (items.length) {
                const vals = items.map(i => {
                    // 위치 정보 단순화: "년지-시지 미술" → "미술"
                    const clean = i.replace(/^[^가-힣]*/,'').split('(')[0].trim();
                    return clean || i;
                }).join(', ');
                parts.push(`
                    <span class="rel-badge ${meta.cls}">
                        <span class="rel-badge-label">${meta.label}</span>
                        <span class="rel-badge-val">${vals}</span>
                    </span>`);
            } else {
                parts.push(`<span class="rel-badge none">${meta.short}: 없음</span>`);
            }
        }

        inline.innerHTML = parts.join('');
    }

    // ── 신살 렌더링 v2 (카테고리 분류) ─────────────────
    const SS_TYPE = {
        '천을귀인':'gil','태극귀인':'gil','문창귀인':'gil','학당귀인':'gil',
        '암록':'gil','금여':'gil','건록':'gil','월덕귀인':'gil','천덕귀인':'gil',
        '복성귀인':'gil','천주귀인':'gil','관귀학관':'gil','천복귀인':'gil','협록':'gil',
        '양인살':'hyung','홍염살':'hyung','백호살':'hyung','괴강살':'hyung',
        '음양차착':'hyung','현침살':'hyung','고신살':'hyung','과숙살':'hyung','고란살':'hyung',
        '겁살':'gun','재살':'gun','천살':'gun','지살':'gun','년살':'gun','월살':'gun',
        '망신살':'gun','장성살':'gun','반안살':'gun','역마살':'gun','육해살':'gun',
        '화개살':'gun','비인살':'gun','천문성':'gun',
    };
    const SS_LABEL = { gil:'길신 (吉神)', hyung:'주의 신살', gun:'12신살' };

    function renderShinsal(data) {
        const grid = document.getElementById('shinsal-grid') || document.getElementById('shinsal-grid');
        if (!grid) return;
        const ss = data.shinsal || {};
        const entries = typeof ss === 'object' && !Array.isArray(ss)
            ? Object.entries(ss)
            : Array.isArray(ss) ? ss.map(s => [s, []]) : [];

        if (!entries.length) { grid.innerHTML = '<p style="color:#aaa;font-size:.82rem">신살 없음</p>'; return; }

        // 카테고리별 그룹
        const groups = { gil:[], hyung:[], gun:[] };
        entries.forEach(([name, pos]) => {
            const t = SS_TYPE[name] || 'gun';
            const posStr = Array.isArray(pos) && pos.length ? pos.join(', ') : '';
            groups[t].push({ name, posStr });
        });

        grid.innerHTML = Object.entries(groups).filter(([,arr]) => arr.length).map(([type, arr]) => `
            <div class="ss-group">
                <div class="ss-group-title">${SS_LABEL[type]}</div>
                <div class="ss-tags">
                    ${arr.map(({name, posStr}) => `
                        <span class="ss-tag ss-${type}">
                            ${name}
                            ${posStr ? `<small>${posStr}</small>` : ''}
                        </span>`).join('')}
                </div>
            </div>`).join('');
    }

    // ── 세운 + 월운 렌더링 ──────────────────────────────
    function renderAnnualFortune(data) {
        // 세운 배지
        const badge = document.getElementById('annual-fortune-badge');
        const af = data.annual_fortune || {};
        if (badge && af.간지) {
            badge.innerHTML = `
                <span class="ab-year">${af.년도 || ''}</span>
                <span class="ab-ganji">${af.간지 || ''}</span>
                <span class="ab-ten">${af.십성 || ''}</span>
                <span class="ab-age">${af.나이 || ''}</span>`;
        }

        // 월운 테이블
        const mt = document.getElementById('monthly-table');
        if (!mt) return;
        const mf = data.monthly_fortune || [];
        if (!mf.length) { mt.innerHTML = '<p style="color:#aaa">월운 데이터 없음</p>'; return; }

        const now = new Date();
        const nowMonth = now.getMonth() + 1; // 1~12

        // 절기 월 인덱스 → 양력 월 추정 (간단 매핑)
        const JEOLGI_MONTH = {
            '입춘':2,'경칩':3,'청명':4,'입하':5,'망종':6,'소서':7,
            '입추':8,'백로':9,'한로':10,'입동':11,'대설':12,'소한':1
        };

        // monthly-table-v2 또는 monthly-table 둘 다 처리
        const mtEl = document.getElementById('monthly-table') || mt;
        mtEl.innerHTML = mf.map((m) => {
            const jeolgiMonth = JEOLGI_MONTH[m.절기] || 0;
            const isCur = (jeolgiMonth === nowMonth);
            const enterDate = m.절입시각 ? m.절입시각.split(' ')[0].slice(5) : '';  // MM-DD
            const enterTime = m.절입시각 ? m.절입시각.split(' ')[1]?.slice(0,5) : '';
            return `
                <div class="month-card ${isCur ? 'current-month' : ''}">
                    <div class="mc-month">${m.월 || ''}</div>
                    <div class="mc-jeolgi">${m.절기 || ''}</div>
                    <div class="mc-ganji">${m.간지 || ''}</div>
                    <span class="mc-ten">${m.십성 || ''}</span>
                    <div class="mc-enter">${enterDate} ${enterTime}</div>
                </div>`;
        }).join('');
    }

    function renderResult(data) {
        resultPage.hidden = false;

        // 메타 정보
        setText('meta-input',  data.input?.label);
        setText('meta-solar',  data.converted_solar);
        setText('meta-lunar',  data.lunar_date);
        setText('meta-gender', data.input?.gender);
        setText('meta-place',  data.input?.birth_place);

        const note = data.calculation_note || {};
        setText('calculation-note', note.engine || note.summary || 'NASA DE441/KASI');

        // 제목
        const dm = data.day_master || {};
        setText('result-title',    `${dm.일간 || '-'}(${dm.hanja || ''}) 일간 · 나의 사주 원국`);
        setText('result-subtitle', '시주 · 일주 · 월주 · 년주');

        // 렌더링
        renderPillars(data);
        renderElements(data);
        renderBranchRelations(data);   // 원국 아래 형충회합
        renderShinsal(data);
        renderUseGod(data);
        renderLuck(data);
        renderAnnualFortune(data);
        renderAdvice(data);

        // 일간·격국
        setText('day-master-copy',
            `${dm.일간 || '-'}(${dm.hanja || ''}) · ${dm.음양 || ''}${dm.오행 || ''}\n${dm.특성 || dm.description || ''}`);
        setText('pattern-copy',
            `${data.pattern?.격 || '-'}\n${data.pattern?.특성 || ''}`);

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
