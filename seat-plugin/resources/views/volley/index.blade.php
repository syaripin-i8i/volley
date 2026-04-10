@php
    $skillsJson = json_encode($skills ?? [], JSON_HEX_TAG | JSON_HEX_APOS | JSON_HEX_AMP | JSON_HEX_QUOT);
    $endpointsJson = json_encode($endpoints ?? [], JSON_HEX_TAG | JSON_HEX_APOS | JSON_HEX_AMP | JSON_HEX_QUOT);
    $csrfToken = csrf_token();
    $characterOptions = collect($characters ?? []);
    $selectedCharacter = $characterOptions->firstWhere('character_id', (int) ($character_id ?? 0));
    $seatHomeUrl = $seat_home_url ?? url('/');
@endphp

<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Sans+JP:wght@400;500;700&display=swap');

    :root {
        --volley-bg-a: #f4f8ff;
        --volley-bg-b: #eef6f2;
        --volley-panel: #ffffff;
        --volley-border: #d2deef;
        --volley-text: #1a2433;
        --volley-muted: #5c6880;
        --volley-accent: #0f7c5f;
        --volley-accent-2: #0f4d8c;
        --volley-warning: #a85c00;
    }

    .volley-shell {
        font-family: "IBM Plex Sans JP", sans-serif;
        color: var(--volley-text);
        border: 1px solid var(--volley-border);
        border-radius: 14px;
        background:
            radial-gradient(circle at 95% 0%, rgba(15, 124, 95, 0.12), transparent 45%),
            linear-gradient(130deg, var(--volley-bg-a), var(--volley-bg-b));
        padding: 18px;
        box-shadow: 0 14px 28px rgba(15, 77, 140, 0.08);
    }

    .volley-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 26px;
        margin: 0;
    }

    .volley-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }

    .volley-back-link {
        display: inline-flex;
        align-items: center;
        border: 1px solid var(--volley-border);
        border-radius: 999px;
        padding: 6px 12px;
        color: var(--volley-accent-2);
        text-decoration: none;
        background: rgba(255, 255, 255, 0.88);
        font-family: "Space Grotesk", sans-serif;
        font-weight: 600;
        font-size: 13px;
        white-space: nowrap;
    }

    .volley-subtitle {
        color: var(--volley-muted);
        margin: 4px 0 16px;
    }

    .volley-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
    }

    .volley-toolbar {
        margin-bottom: 14px;
    }

    .volley-panel {
        background: var(--volley-panel);
        border: 1px solid var(--volley-border);
        border-radius: 12px;
        padding: 14px;
    }

    .volley-panel h4 {
        margin-top: 0;
        margin-bottom: 12px;
        font-family: "Space Grotesk", sans-serif;
        font-weight: 700;
    }

    .volley-label {
        display: block;
        font-size: 12px;
        color: var(--volley-muted);
        margin-bottom: 4px;
        margin-top: 8px;
    }

    .volley-input,
    .volley-select,
    .volley-textarea {
        width: 100%;
        border: 1px solid #b4c5dd;
        border-radius: 8px;
        padding: 8px 10px;
        background: #fff;
        color: var(--volley-text);
    }

    .volley-textarea {
        min-height: 250px;
        resize: vertical;
        font-family: Consolas, "Courier New", monospace;
        line-height: 1.35;
    }

    .volley-target-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
    }

    .volley-actions {
        margin-top: 12px;
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
    }

    .volley-import-actions {
        margin-top: 8px;
        display: flex;
        gap: 8px;
        align-items: stretch;
    }

    .volley-import-actions .volley-input {
        flex: 1;
    }

    .volley-btn {
        border: none;
        border-radius: 9px;
        padding: 10px 14px;
        font-family: "Space Grotesk", sans-serif;
        font-weight: 700;
        color: #fff;
        background: linear-gradient(135deg, var(--volley-accent-2), var(--volley-accent));
        cursor: pointer;
    }

    .volley-btn-secondary {
        background: linear-gradient(135deg, #355f9c, #4c7aba);
    }

    .volley-btn:disabled {
        opacity: 0.6;
        cursor: wait;
    }

    .volley-fit-editor {
        margin-top: 12px;
        border-top: 1px dashed var(--volley-border);
        padding-top: 10px;
    }

    .volley-fit-editor-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 8px;
    }

    .volley-fit-editor-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 14px;
        font-weight: 700;
    }

    .volley-fit-editor-meta {
        color: var(--volley-muted);
        font-size: 12px;
    }

    .volley-fit-warnings {
        margin-bottom: 8px;
        color: #8f4a00;
        font-size: 12px;
        line-height: 1.45;
    }

    .volley-fit-modules {
        display: grid;
        gap: 8px;
        max-height: 280px;
        overflow: auto;
        padding-right: 2px;
    }

    .volley-fit-module {
        border: 1px solid var(--volley-border);
        border-radius: 8px;
        padding: 8px;
        background: #f9fbff;
    }

    .volley-fit-module-main {
        display: flex;
        align-items: baseline;
        gap: 8px;
        flex-wrap: wrap;
    }

    .volley-slot-chip {
        font-family: "Space Grotesk", sans-serif;
        font-size: 11px;
        font-weight: 700;
        color: #fff;
        background: #0f4d8c;
        border-radius: 999px;
        padding: 2px 8px;
    }

    .volley-fit-module-name {
        font-size: 13px;
        font-weight: 600;
    }

    .volley-fit-module-qty {
        font-size: 12px;
        color: var(--volley-muted);
    }

    .volley-fit-charge {
        margin-top: 7px;
    }

    .volley-fit-charge-help {
        margin-top: 4px;
        color: var(--volley-muted);
        font-size: 11px;
    }

    .volley-error {
        margin-top: 8px;
        color: #9d1919;
        font-size: 12px;
    }

    .volley-chart-panel {
        margin-top: 14px;
    }

    .volley-chart-note {
        margin-top: 8px;
        color: var(--volley-muted);
        font-size: 12px;
        line-height: 1.5;
    }

    .volley-chart-frame {
        position: relative;
        height: 300px;
        min-height: 300px;
        max-height: 300px;
        overflow: hidden;
        contain: layout size;
    }

    .volley-chart-canvas {
        box-sizing: border-box !important;
        display: block;
        width: 100% !important;
        height: 100% !important;
        max-height: 100% !important;
    }

    .volley-summary {
        margin-top: 14px;
        display: grid;
        gap: 8px;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    }

    .volley-kpi {
        background: #fff;
        border: 1px solid var(--volley-border);
        border-radius: 10px;
        padding: 10px;
    }

    .volley-kpi .k-label {
        color: var(--volley-muted);
        font-size: 12px;
    }

    .volley-kpi .k-value {
        font-family: "Space Grotesk", sans-serif;
        font-size: 20px;
        font-weight: 700;
        margin-top: 2px;
    }

    .volley-hint {
        color: var(--volley-warning);
        font-size: 12px;
        margin-top: 6px;
    }

    #status-text {
        min-height: 18px;
    }

    @media (max-width: 900px) {
        .volley-shell {
            padding: 14px;
        }
        .volley-grid {
            grid-template-columns: 1fr;
        }
        .volley-target-grid {
            grid-template-columns: 1fr;
        }
        .volley-panel {
            padding: 12px;
        }
        .volley-actions {
            flex-direction: column;
            align-items: stretch;
        }
        .volley-import-actions {
            flex-direction: column;
        }
        .volley-btn {
            width: 100%;
        }
        .volley-summary {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .volley-kpi .k-value {
            font-size: 18px;
        }
        .volley-back-link {
            width: 100%;
            justify-content: center;
        }
    }

    @media (max-width: 640px) {
        .volley-title {
            font-size: 22px;
        }
        .volley-summary {
            grid-template-columns: 1fr 1fr;
        }
    }
</style>

<div class="volley-shell">
    <div class="volley-header">
        <h3 class="volley-title">Damage Calculator</h3>
        <a class="volley-back-link" href="{{ $seatHomeUrl }}">SeAT Home へ戻る</a>
    </div>
    <p class="volley-subtitle">
        @if ($selectedCharacter)
            現在は <strong>{{ $selectedCharacter['name'] }}</strong> のスキルを適用して計算します。
        @elseif ($characterOptions->isNotEmpty())
            キャラクターを選ぶと、そのキャラクターの SeAT 同期済みスキルを適用して計算します。
        @else
            利用可能なキャラクターが見つからないため、現在はスキル補正なしで計算します。
        @endif
    </p>

    <div class="volley-panel volley-toolbar">
        <h4>スキル適用キャラクター</h4>
        <label class="volley-label" for="character-select">Character</label>
        <select id="character-select" class="volley-select">
            <option value="">No skill profile</option>
            @foreach ($characterOptions as $character)
                <option value="{{ $character['character_id'] }}" @selected((int) ($character_id ?? 0) === (int) $character['character_id'])>
                    {{ $character['name'] }}@if($character['is_main']) (Main) @endif
                </option>
            @endforeach
        </select>
        <div class="volley-hint">
            @if ($selectedCharacter)
                {{ $selectedCharacter['name'] }} のスキルを engine へ送信します。
            @elseif ($characterOptions->isNotEmpty())
                未選択時はスキル補正なしで計算します。複数キャラクターを使い分ける場合はここで切り替えてください。
            @else
                SeAT 上でこのユーザーに紐づくキャラクターが見つかりませんでした。
            @endif
        </div>
    </div>

    <div class="volley-grid">
        <div class="volley-panel">
            <h4>フィット入力</h4>
            <label class="volley-label" for="zkill-url">zKill URL Import</label>
            <div class="volley-import-actions">
                <input id="zkill-url" class="volley-input" type="url" placeholder="https://zkillboard.com/kill/134558843/">
                <button id="import-zkill-btn" class="volley-btn volley-btn-secondary" type="button">Import</button>
            </div>
            <div class="volley-hint">canonical URL 例: https://zkillboard.com/kill/&lt;kill_id&gt;/</div>

            <label class="volley-label" for="saved-fitting">Saved Fittings</label>
            <select id="saved-fitting" class="volley-select">
                <option value="">Custom</option>
                <option value="sample-rifter">Rifter PvP (Sample)</option>
            </select>

            <label class="volley-label" for="eft-input">EFT テキスト</label>
            <textarea id="eft-input" class="volley-textarea" placeholder="[Rifter, My PvP Rifter]&#10;&#10;150mm Light AutoCannon II, Republic Fleet EMP S&#10;..."></textarea>

            <div id="fit-editor" class="volley-fit-editor" hidden>
                <div class="volley-fit-editor-head">
                    <div class="volley-fit-editor-title">Charge / Script 差し替え</div>
                    <div id="fit-editor-meta" class="volley-fit-editor-meta"></div>
                </div>
                <div id="fit-warnings" class="volley-fit-warnings"></div>
                <div id="fit-modules" class="volley-fit-modules"></div>
            </div>
        </div>

        <div class="volley-panel">
            <h4>ターゲット設定</h4>
            <label class="volley-label" for="target-preset">プリセット</label>
            <select id="target-preset" class="volley-select">
                <option value="">Custom</option>
                <option value="capsule">Capsule</option>
                <option value="frigate" selected>Frigate</option>
                <option value="destroyer">Destroyer</option>
                <option value="cruiser">Cruiser</option>
                <option value="battlecruiser">Battlecruiser</option>
                <option value="battleship">Battleship</option>
            </select>

            <div class="volley-target-grid">
                <div>
                    <label class="volley-label" for="sig">Sig Radius (m)</label>
                    <input id="sig" class="volley-input" type="number" value="40" min="1" step="1">
                </div>
                <div>
                    <label class="volley-label" for="speed">Speed (m/s)</label>
                    <input id="speed" class="volley-input" type="number" value="350" min="0" step="1">
                </div>
                <div>
                    <label class="volley-label" for="angle">Angle (°)</label>
                    <input id="angle" class="volley-input" type="number" value="90" min="0" max="180" step="1">
                </div>
                <div>
                    <label class="volley-label" for="distance">Distance (km)</label>
                    <input id="distance" class="volley-input" type="number" value="8" min="0" step="0.1">
                </div>
            </div>

            <div class="volley-actions">
                <button id="calculate-btn" class="volley-btn" type="button">Calculate</button>
                <span id="status-text" class="volley-hint"></span>
            </div>
            <div id="error-text" class="volley-error"></div>
        </div>
    </div>

    <div class="volley-panel volley-chart-panel">
        <h4>DPS vs Distance</h4>
        <div id="dps-chart-frame" class="volley-chart-frame">
            <canvas id="dps-chart" class="volley-chart-canvas"></canvas>
        </div>
        <div class="volley-chart-note" id="chart-note">
            グラフは現在の Sig / Speed / Angle 条件で 0-200km を走査します。Distance はサマリーと選択距離マーカーに反映されます。
        </div>
    </div>

    <div class="volley-summary">
        <div class="volley-kpi">
            <div class="k-label">Raw DPS</div>
            <div class="k-value" id="kpi-raw">-</div>
        </div>
        <div class="volley-kpi">
            <div class="k-label">Applied DPS</div>
            <div class="k-value" id="kpi-applied">-</div>
        </div>
        <div class="volley-kpi">
            <div class="k-label">Application</div>
            <div class="k-value" id="kpi-app">-</div>
        </div>
        <div class="volley-kpi">
            <div class="k-label">Volley</div>
            <div class="k-value" id="kpi-volley">-</div>
        </div>
        <div class="volley-kpi">
            <div class="k-label">Weapon</div>
            <div class="k-value" id="kpi-weapon">-</div>
        </div>
    </div>
</div>

<script src="{{ asset('vendor/seat-volley/js/chart.umd.min.js') }}"></script>
<script>
    window.characterSkills = {!! $skillsJson !!};
    window.volleyEndpoints = {!! $endpointsJson !!};
    window.volleyCsrfToken = "{{ $csrfToken }}";
</script>
<script>
    (function () {
        if (window.volleyChartRuntime && typeof window.volleyChartRuntime.teardown === 'function') {
            window.volleyChartRuntime.teardown();
        }

        const csrfToken = window.volleyCsrfToken;
        const endpoints = window.volleyEndpoints || {};
        const calculateUrl = endpoints.calculate || '/volley/calculate';
        const resolveFitUrl = endpoints.resolve_fit || '/volley/fit/resolve';
        const importZkillUrl = endpoints.import_zkill || '/volley/fit/import-zkill';

        const targetPreset = document.getElementById('target-preset');
        const characterSelect = document.getElementById('character-select');
        const savedFitting = document.getElementById('saved-fitting');
        const eftInput = document.getElementById('eft-input');
        const zkillUrlInput = document.getElementById('zkill-url');
        const importZkillBtn = document.getElementById('import-zkill-btn');
        const fitEditor = document.getElementById('fit-editor');
        const fitEditorMeta = document.getElementById('fit-editor-meta');
        const fitWarnings = document.getElementById('fit-warnings');
        const fitModules = document.getElementById('fit-modules');
        const calculateBtn = document.getElementById('calculate-btn');
        const statusText = document.getElementById('status-text');
        const errorText = document.getElementById('error-text');
        const chartNote = document.getElementById('chart-note');
        const chartFrame = document.getElementById('dps-chart-frame');
        const chartCanvas = document.getElementById('dps-chart');
        const chartCtx = chartCanvas.getContext('2d');
        const desktopChartHeight = 300;
        const mobileChartHeight = 240;
        let resizeFrameHandle = null;
        let activeFitState = null;
        let fitStateDirty = true;

        const presets = {
            capsule: { sig: 30, speed: 0 },
            frigate: { sig: 40, speed: 350 },
            destroyer: { sig: 70, speed: 250 },
            cruiser: { sig: 130, speed: 200 },
            battlecruiser: { sig: 270, speed: 150 },
            battleship: { sig: 400, speed: 100 },
        };

        const sampleFittings = {
            'sample-rifter': `[Rifter, My PvP Rifter]

150mm Light AutoCannon II, Republic Fleet EMP S
150mm Light AutoCannon II, Republic Fleet EMP S
150mm Light AutoCannon II, Republic Fleet EMP S
[Empty High slot]

1MN Afterburner II
J5b Enduring Warp Scrambler
Small Electrochemical Capacitor Booster I, Navy Cap Booster 200

Gyrostabilizer II
Nanofiber Internal Structure II
Small Armor Repairer II

Small Projectile Burst Aerator II
Small Projectile Collision Accelerator II
[Empty Rig slot]`
        };

        function applyPreset() {
            const key = targetPreset.value;
            if (!key || !presets[key]) return;
            document.getElementById('sig').value = presets[key].sig;
            document.getElementById('speed').value = presets[key].speed;
        }

        function applyFittingTemplate() {
            const key = savedFitting.value;
            if (!key || !sampleFittings[key]) return;
            eftInput.value = sampleFittings[key];
            invalidateFitState();
        }

        function applyCharacterSelection() {
            const url = new URL(window.location.href);
            const selected = characterSelect.value;
            if (selected) {
                url.searchParams.set('character_id', selected);
            } else {
                url.searchParams.delete('character_id');
            }
            window.location.assign(url.toString());
        }

        function formatNum(value, digits = 2) {
            if (value === null || value === undefined || Number.isNaN(value)) return '-';
            return Number(value).toFixed(digits);
        }

        function isCompactViewport() {
            return window.innerWidth <= 900;
        }

        function getChartHeight() {
            return isCompactViewport() ? mobileChartHeight : desktopChartHeight;
        }

        function formatDistanceLabel(value) {
            const numeric = Number(value);
            if (!Number.isFinite(numeric)) return '';
            return numeric >= 100 ? numeric.toFixed(0) : numeric.toFixed(1);
        }

        function getCurrentTargetSnapshot() {
            return {
                sigRadius: parseFloat(document.getElementById('sig').value),
                velocity: parseFloat(document.getElementById('speed').value),
                angle: parseFloat(document.getElementById('angle').value) || 90,
                distanceKm: parseFloat(document.getElementById('distance').value) || 0,
            };
        }

        function slotLabel(slot) {
            if (!slot) return 'SLOT';
            return String(slot).toUpperCase();
        }

        function invalidateFitState() {
            fitStateDirty = true;
            activeFitState = null;
            fitEditor.hidden = true;
            fitEditorMeta.textContent = '';
            fitWarnings.textContent = '';
            fitModules.innerHTML = '';
        }

        function setFitState(state, options = {}) {
            activeFitState = state;
            fitStateDirty = false;

            if (options.replaceEft && typeof state.eft_text === 'string' && state.eft_text.trim() !== '') {
                eftInput.value = state.eft_text;
            }
            renderFitEditor(state);
        }

        function renderFitEditor(state) {
            if (!state || !state.fit || !Array.isArray(state.modules) || state.modules.length === 0) {
                fitEditor.hidden = true;
                fitEditorMeta.textContent = '';
                fitWarnings.textContent = '';
                fitModules.innerHTML = '';
                return;
            }

            fitEditor.hidden = false;
            const labelParts = [];
            if (state.source_label) labelParts.push(state.source_label);
            labelParts.push(`${state.modules.length} modules`);
            fitEditorMeta.textContent = labelParts.join(' / ');

            if (Array.isArray(state.warnings) && state.warnings.length > 0) {
                fitWarnings.textContent = state.warnings.join(' / ');
            } else {
                fitWarnings.textContent = '';
            }

            fitModules.innerHTML = '';
            state.modules.forEach((module, index) => {
                const row = document.createElement('div');
                row.className = 'volley-fit-module';

                const main = document.createElement('div');
                main.className = 'volley-fit-module-main';

                const slot = document.createElement('span');
                slot.className = 'volley-slot-chip';
                slot.textContent = slotLabel(module.slot);

                const name = document.createElement('span');
                name.className = 'volley-fit-module-name';
                name.textContent = module.type_name || `type_id:${module.type_id}`;

                const qty = document.createElement('span');
                qty.className = 'volley-fit-module-qty';
                qty.textContent = `x${module.quantity || 1}`;

                main.appendChild(slot);
                main.appendChild(name);
                main.appendChild(qty);
                row.appendChild(main);

                const options = Array.isArray(module.charge_options) ? module.charge_options.slice() : [];
                const currentChargeId = (module.charge_type_id === null || module.charge_type_id === undefined)
                    ? null
                    : Number(module.charge_type_id);
                const hasCurrent = currentChargeId !== null && options.some((opt) => Number(opt.type_id) === currentChargeId);
                if (currentChargeId !== null && !hasCurrent) {
                    options.push({
                        type_id: currentChargeId,
                        type_name: module.charge_name || `type_id:${currentChargeId}`,
                    });
                }

                const canEditCharge = options.length > 0 || currentChargeId !== null;
                const chargeWrap = document.createElement('div');
                chargeWrap.className = 'volley-fit-charge';

                if (canEditCharge) {
                    const select = document.createElement('select');
                    select.className = 'volley-select';
                    select.dataset.moduleIndex = String(index);

                    const noneOption = document.createElement('option');
                    noneOption.value = '';
                    noneOption.textContent = '(None)';
                    select.appendChild(noneOption);

                    options
                        .sort((a, b) => String(a.type_name || '').localeCompare(String(b.type_name || '')))
                        .forEach((opt) => {
                            const option = document.createElement('option');
                            option.value = String(opt.type_id);
                            option.textContent = opt.type_name || `type_id:${opt.type_id}`;
                            select.appendChild(option);
                        });

                    select.value = currentChargeId === null ? '' : String(currentChargeId);
                    select.addEventListener('change', () => {
                        const selectedRaw = select.value;
                        const selectedChargeId = selectedRaw === '' ? null : Number(selectedRaw);
                        const selectedName = selectedRaw === ''
                            ? null
                            : (select.options[select.selectedIndex] ? select.options[select.selectedIndex].text : null);
                        updateModuleCharge(index, selectedChargeId, selectedName);
                    });
                    chargeWrap.appendChild(select);

                    const help = document.createElement('div');
                    help.className = 'volley-fit-charge-help';
                    help.textContent = 'Charge / script を選ぶと計算に反映されます。';
                    chargeWrap.appendChild(help);
                } else {
                    const help = document.createElement('div');
                    help.className = 'volley-fit-charge-help';
                    help.textContent = 'このモジュールは charge/script 編集対象ではありません。';
                    chargeWrap.appendChild(help);
                }

                row.appendChild(chargeWrap);
                fitModules.appendChild(row);
            });
        }

        function updateModuleCharge(index, chargeTypeId, chargeName) {
            if (!activeFitState || !activeFitState.fit || !Array.isArray(activeFitState.modules)) return;
            const moduleState = activeFitState.modules[index];
            const fitModule = Array.isArray(activeFitState.fit.modules) ? activeFitState.fit.modules[index] : null;
            if (!moduleState || !fitModule) return;

            moduleState.charge_type_id = chargeTypeId;
            moduleState.charge_name = chargeTypeId === null ? null : (chargeName || moduleState.charge_name || null);
            fitModule.charge_type_id = chargeTypeId;
            fitStateDirty = false;
        }

        async function postJson(url, payload) {
            const response = await fetch(url, {
                method: 'POST',
                cache: 'no-store',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': csrfToken,
                },
                body: JSON.stringify(payload),
            });

            let data = null;
            try {
                data = await response.json();
            } catch (err) {
                data = null;
            }

            if (!response.ok) {
                const errorMessage =
                    (data && (data.message || data.detail || data.error)) ||
                    `Request failed (${response.status}).`;
                throw new Error(errorMessage);
            }
            return data;
        }

        async function resolveFitStateFromEft() {
            const eftText = eftInput.value || '';
            return postJson(resolveFitUrl, { eft_text: eftText });
        }

        async function ensureFitStateReady() {
            if (!fitStateDirty && activeFitState && activeFitState.fit) {
                return activeFitState;
            }

            const eftText = (eftInput.value || '').trim();
            if (eftText === '') {
                if (activeFitState && activeFitState.fit) {
                    return activeFitState;
                }
                throw new Error('EFT text が空です。zKill import または EFT 貼り付けを先に実行してください。');
            }

            statusText.textContent = 'Resolving fit...';
            const resolved = await resolveFitStateFromEft();
            setFitState(resolved);
            statusText.textContent = 'Fit ready';
            return resolved;
        }

        async function importFromZkill() {
            const rawUrl = (zkillUrlInput.value || '').trim();
            if (rawUrl === '') {
                throw new Error('zKill URL を入力してください。');
            }
            statusText.textContent = 'Importing zKill...';
            importZkillBtn.disabled = true;

            try {
                const imported = await postJson(importZkillUrl, { url: rawUrl });
                setFitState(imported, { replaceEft: true });
                errorText.textContent = '';
                statusText.textContent = 'zKill import completed.';
            } finally {
                importZkillBtn.disabled = false;
            }
        }

        function renderCalculationStatus() {
            const now = new Date();
            const timeLabel = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            statusText.textContent = `Updated ${timeLabel}`;
        }

        const markerPlugin = {
            id: 'rangeMarkers',
            afterDraw(chart, args, options) {
                const markers = options.markers || [];
                const bands = options.bands || [];
                const x = chart.scales.x;
                const y = chart.scales.y;
                if (!x || !y) return;

                const ctx = chart.ctx;
                ctx.save();
                bands.forEach((band) => {
                    if (band.from === null || band.to === null || band.from === undefined || band.to === undefined) {
                        return;
                    }
                    const start = x.getPixelForValue(band.from);
                    const end = x.getPixelForValue(band.to);
                    if (!Number.isFinite(start) || !Number.isFinite(end)) return;

                    ctx.fillStyle = band.color || 'rgba(15, 77, 140, 0.06)';
                    ctx.fillRect(Math.min(start, end), y.top, Math.abs(end - start), y.bottom - y.top);
                });

                markers.forEach((marker) => {
                    if (marker.value === null || marker.value === undefined) return;
                    const px = x.getPixelForValue(marker.value);
                    if (!Number.isFinite(px)) return;

                    ctx.strokeStyle = marker.color;
                    ctx.lineWidth = marker.width || 1.5;
                    ctx.setLineDash(marker.dash || [6, 4]);
                    ctx.beginPath();
                    ctx.moveTo(px, y.top);
                    ctx.lineTo(px, y.bottom);
                    ctx.stroke();
                    ctx.setLineDash([]);

                    const label = marker.label || '';
                    ctx.font = '11px "IBM Plex Sans JP", sans-serif';
                    const textMetrics = ctx.measureText(label);
                    const badgePaddingX = 6;
                    const badgeWidth = textMetrics.width + badgePaddingX * 2;
                    const badgeHeight = 18;
                    const badgeX = Math.min(Math.max(px + 6, x.left + 4), x.right - badgeWidth - 4);
                    const badgeY = y.top + 6;

                    ctx.fillStyle = marker.fillColor || marker.color;
                    ctx.fillRect(badgeX, badgeY, badgeWidth, badgeHeight);

                    ctx.fillStyle = marker.textColor || '#ffffff';
                    ctx.fillText(label, badgeX + badgePaddingX, badgeY + 12);
                });
                ctx.restore();
            }
        };
        try {
            Chart.unregister(markerPlugin);
        } catch (err) {
            // Ignore unregister errors when the plugin was not registered yet.
        }
        Chart.register(markerPlugin);

        let dpsChart = null;

        function getChartWidth() {
            const measured = chartFrame.clientWidth || chartFrame.getBoundingClientRect().width || 0;
            return Math.max(Math.floor(measured), 320);
        }

        function syncChartFrameSize() {
            const chartHeight = getChartHeight();
            chartFrame.style.height = chartHeight + 'px';
            chartFrame.style.minHeight = chartHeight + 'px';
            chartFrame.style.maxHeight = chartHeight + 'px';
            chartCanvas.style.height = chartHeight + 'px';
        }

        function resizeChartToFrame() {
            if (!dpsChart) return;
            syncChartFrameSize();
            dpsChart.resize(getChartWidth(), getChartHeight());
        }

        function renderGraph(data, snapshot) {
            const distances = data.distances || [];
            const applied = data.applied_dps || [];
            const rawValue = (data.summary && data.summary.raw_dps) || data.raw_dps || 0;
            const rawLine = distances.map(() => rawValue);
            const selectedDistanceKm = snapshot.distanceKm;
            const selectedAppliedDps = (data.summary && data.summary.applied_dps !== undefined)
                ? data.summary.applied_dps
                : null;
            const selectedPointSeries = distances.map(() => null);
            const xTickStride = Math.max(1, Math.ceil(distances.length / (isCompactViewport() ? 6 : 11)));

            const markers = [];
            const bands = [];
            if (data.optimal_km !== null && data.optimal_km !== undefined) {
                markers.push({
                    value: data.optimal_km,
                    color: '#177a56',
                    label: 'optimal',
                    dash: [3, 4],
                    width: 1.5,
                });
            }
            if (data.falloff_km !== null && data.falloff_km !== undefined) {
                const baseOptimal = (data.optimal_km !== null && data.optimal_km !== undefined) ? data.optimal_km : 0;
                const falloffPosition = baseOptimal + data.falloff_km;
                markers.push({
                    value: falloffPosition,
                    color: '#0f4d8c',
                    label: 'falloff',
                    dash: [6, 4],
                    width: 1.5,
                });
                bands.push({
                    from: baseOptimal,
                    to: falloffPosition,
                    color: 'rgba(15, 77, 140, 0.08)',
                });
            }
            if (Number.isFinite(selectedDistanceKm)) {
                markers.push({
                    value: selectedDistanceKm,
                    color: '#a85c00',
                    label: 'selected',
                    dash: [],
                    width: 2,
                });
                if (selectedAppliedDps !== null && distances.length > 0) {
                    let closestIndex = 0;
                    let closestDelta = Math.abs(distances[0] - selectedDistanceKm);
                    for (let i = 1; i < distances.length; i += 1) {
                        const delta = Math.abs(distances[i] - selectedDistanceKm);
                        if (delta < closestDelta) {
                            closestIndex = i;
                            closestDelta = delta;
                        }
                    }
                    selectedPointSeries[closestIndex] = selectedAppliedDps;
                }
            }

            if (dpsChart) {
                dpsChart.destroy();
            }

            syncChartFrameSize();
            dpsChart = new Chart(chartCtx, {
                type: 'line',
                data: {
                    labels: distances,
                    datasets: [
                        {
                            label: 'Applied DPS',
                            data: applied,
                            borderColor: '#1170d6',
                            borderWidth: 2.5,
                            fill: false,
                            tension: 0.2,
                            pointRadius: isCompactViewport() ? 0 : 1.5,
                            pointHoverRadius: 4,
                        },
                        {
                            label: 'Raw DPS',
                            data: rawLine,
                            borderColor: '#8f96a8',
                            borderDash: [5, 5],
                            borderWidth: 2,
                            fill: false,
                            pointRadius: 0,
                            tension: 0,
                        },
                        {
                            label: 'Selected Distance',
                            data: selectedPointSeries,
                            borderColor: '#a85c00',
                            backgroundColor: '#a85c00',
                            showLine: false,
                            pointRadius: 5,
                            pointHoverRadius: 6,
                        }
                    ]
                },
                options: {
                    animation: false,
                    responsive: false,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    scales: {
                        x: {
                            title: { display: true, text: 'Distance (km)' },
                            ticks: {
                                autoSkip: false,
                                maxRotation: isCompactViewport() ? 42 : 0,
                                minRotation: isCompactViewport() ? 42 : 0,
                                callback(value, index) {
                                    if (index % xTickStride !== 0 && index !== distances.length - 1) return '';
                                    return formatDistanceLabel(this.getLabelForValue(value));
                                },
                            },
                            grid: {
                                color: 'rgba(26, 36, 51, 0.08)',
                            },
                        },
                        y: {
                            title: { display: true, text: 'DPS' },
                            beginAtZero: true,
                            ticks: {
                                callback(value) {
                                    return formatNum(value, value >= 100 ? 0 : 1);
                                },
                            },
                            grid: {
                                color: 'rgba(26, 36, 51, 0.08)',
                            },
                        }
                    },
                    plugins: {
                        legend: {
                            position: isCompactViewport() ? 'bottom' : 'top',
                            labels: {
                                boxWidth: 14,
                                usePointStyle: true,
                            },
                        },
                        tooltip: {
                            callbacks: {
                                title(items) {
                                    if (!items.length) return '';
                                    return `Distance ${formatDistanceLabel(items[0].label)} km`;
                                },
                                label(context) {
                                    return `${context.dataset.label}: ${formatNum(context.parsed.y, 1)} DPS`;
                                },
                            },
                        },
                        rangeMarkers: { markers, bands }
                    }
                }
            });
            resizeChartToFrame();
        }

        function renderSummary(data) {
            const summary = data.summary || {};
            const raw = summary.raw_dps ?? data.raw_dps ?? 0;
            const applied = summary.applied_dps ?? ((data.applied_dps || []).slice(-1)[0] ?? 0);
            const appPct = summary.application_pct ?? (raw > 0 ? (applied / raw) * 100 : 0);

            document.getElementById('kpi-raw').textContent = formatNum(raw, 1);
            document.getElementById('kpi-applied').textContent = formatNum(applied, 1);
            document.getElementById('kpi-app').textContent = formatNum(appPct, 1) + '%';
            document.getElementById('kpi-volley').textContent = summary.volley !== undefined ? formatNum(summary.volley, 1) : '-';
            document.getElementById('kpi-weapon').textContent = summary.weapon_type || '-';
        }

        async function calculate() {
            errorText.textContent = '';
            statusText.textContent = 'Calculating...';
            calculateBtn.disabled = true;
            importZkillBtn.disabled = true;

            try {
                const targetSnapshot = getCurrentTargetSnapshot();
                const fitState = await ensureFitStateReady();
                const payload = {
                    fit: fitState.fit,
                    skills: window.characterSkills || [],
                    target: {
                        sig_radius: targetSnapshot.sigRadius,
                        velocity: targetSnapshot.velocity,
                        angle: targetSnapshot.angle,
                        distance: targetSnapshot.distanceKm * 1000,
                    },
                    distance_range: [0, 200000],
                    steps: 150,
                };

                const data = await postJson(calculateUrl, payload);

                renderGraph(data, targetSnapshot);
                renderSummary(data);
                renderCalculationStatus();
                chartNote.textContent = `現在の条件: Sig ${formatNum(targetSnapshot.sigRadius, 0)} m / Speed ${formatNum(targetSnapshot.velocity, 0)} m/s / Angle ${formatNum(targetSnapshot.angle, 0)}°。グラフはこの条件で 0-200km を走査し、selected マーカーが Distance ${formatNum(targetSnapshot.distanceKm, 1)} km を示します。`;
            } catch (err) {
                errorText.textContent = err.message || 'Unexpected error.';
                statusText.textContent = '';
            } finally {
                calculateBtn.disabled = false;
                importZkillBtn.disabled = false;
            }
        }

        targetPreset.addEventListener('change', applyPreset);
        characterSelect.addEventListener('change', applyCharacterSelection);
        savedFitting.addEventListener('change', applyFittingTemplate);
        eftInput.addEventListener('input', invalidateFitState);
        importZkillBtn.addEventListener('click', async () => {
            errorText.textContent = '';
            try {
                await importFromZkill();
            } catch (err) {
                errorText.textContent = err.message || 'Import failed.';
                statusText.textContent = '';
            }
        });
        calculateBtn.addEventListener('click', calculate);

        const onWindowResize = () => {
            if (resizeFrameHandle !== null) {
                cancelAnimationFrame(resizeFrameHandle);
            }
            resizeFrameHandle = requestAnimationFrame(() => {
                resizeFrameHandle = null;
                resizeChartToFrame();
            });
        };

        let frameResizeObserver = null;
        if (typeof ResizeObserver !== 'undefined') {
            frameResizeObserver = new ResizeObserver(onWindowResize);
            frameResizeObserver.observe(chartFrame);
        }

        window.addEventListener('resize', onWindowResize);

        window.volleyChartRuntime = {
            teardown() {
                window.removeEventListener('resize', onWindowResize);
                if (frameResizeObserver) {
                    frameResizeObserver.disconnect();
                }
                if (resizeFrameHandle !== null) {
                    cancelAnimationFrame(resizeFrameHandle);
                }
                if (dpsChart) {
                    dpsChart.destroy();
                    dpsChart = null;
                }
            }
        };

        syncChartFrameSize();
        applyPreset();
        applyFittingTemplate();
    })();
</script>
