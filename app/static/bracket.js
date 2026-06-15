// Bracket Compare page. Lists every aircraft within 1.0 BR of yours and the
// verdict against each. Shared helpers live in common.js, loaded first.

function contact(aircraft) {
    const img = aircraft.image_url
        ? `<img class="trow__img" src="${escapeHtml(aircraft.image_url)}" alt="" loading="lazy">`
        : `<span class="trow__img trow__img--empty"></span>`;
    return `
        <div class="trow__contact">
            ${img}
            <div class="trow__id">
                <div class="trow__name">${escapeHtml(aircraft.name)}</div>
                <div class="trow__meta">${escapeHtml(metaLine(aircraft)) || "—"}</div>
            </div>
        </div>`;
}

function chip(key, value) {
    const v = value
        ? `<span class="chip__v">${escapeHtml(value)}</span>`
        : `<span class="chip__v unknown">—</span>`;
    return `<div class="chip"><span class="chip__k">${key}</span>${v}</div>`;
}

function performance(stats) {
    return `
        <div class="trow__perf">
            ${chip("SPD", stats.max_speed)}
            ${chip("TURN", stats.turn_time)}
            ${chip("CLIMB", stats.climb_rate)}
        </div>`;
}

function loadout(stats) {
    const arm = stats.armament
        ? `<span class="trow__arm">${escapeHtml(stats.armament)}</span>`
        : `<span class="trow__arm unknown">No fixed cannon</span>`;
    const cm = `<span class="trow__cm">${escapeHtml(stats.countermeasures || "No countermeasures")}</span>`;
    return `<div class="trow__loadout">${arm}${cm}</div>`;
}

function verdictBadge(verdict) {
    const label = VERDICT_LABEL[verdict] || String(verdict).toUpperCase();
    return `<div class="trow__verdict ${escapeHtml(verdict)}">${label}</div>`;
}

const PAGE = 20;
let mineAircraft = null;
let opponents = [];
let total = 0;
let loading = false;

function opponentRow(o) {
    return `
        <div class="trow">
            ${contact(o)}
            ${performance(o.stats)}
            ${loadout(o.stats)}
            ${verdictBadge(o.verdict)}
        </div>`;
}

function moreControls() {
    const shown = opponents.length;
    if (shown >= total) return "";
    const next = Math.min(PAGE, total - shown);
    const busy = loading ? " disabled" : "";
    return `
        <div class="ledger__more">
            <button type="button" class="btn-more" data-action="more"${busy}>Load ${next} more</button>
            <button type="button" class="btn-more btn-more--all" data-action="all"${busy}>Load all (${total})</button>
            <span class="ledger__count">Showing ${shown} of ${total}</span>
        </div>`;
}

// Full initial render. Subsequent pages are appended (see appendRows) rather
// than re-rendered, so already-drawn rows are never re-parsed.
function paintBracket() {
    const mine = mineAircraft;
    const span = `${(mine.br_rb - 1).toFixed(1)} – ${(mine.br_rb + 1).toFixed(1)}`;
    const rows = opponents.map(opponentRow).join("");

    document.getElementById("result").innerHTML = `
        <div class="b-summary">
            <span class="b-summary__label">Facing in bracket</span>
            <span class="b-summary__br">BR ${escapeHtml(span)}</span>
            <span class="b-summary__count">${total} aircraft</span>
        </div>
        <div class="ledger" id="ledger">
            <div class="ledger__head">
                <span>Contact</span><span>Performance</span><span>Loadout</span><span>Assessment</span>
            </div>
            <div class="trow trow--mine">
                ${contact(mine)}
                ${performance(mine.stats)}
                ${loadout(mine.stats)}
                <div class="trow__verdict trow__verdict--you">YOU</div>
            </div>
            ${rows}
        </div>
        <div id="b-more">${moreControls()}</div>`;
    document.getElementById("result").hidden = false;
}

function refreshControls() {
    const el = document.getElementById("b-more");
    if (el) el.innerHTML = moreControls();
}

function appendRows(items) {
    const ledger = document.getElementById("ledger");
    if (ledger) ledger.insertAdjacentHTML("beforeend", items.map(opponentRow).join(""));
}

async function fetchPage(offset, limit) {
    const mine = getCookie(COOKIE);
    const url = `/api/bracket?mine=${encodeURIComponent(mine)}&offset=${offset}&limit=${limit}`;
    const response = await fetch(url);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not load the bracket.");
    return data;
}

// Fetch and append the next page (or everything remaining when `all` is set).
async function loadMore(all) {
    if (loading || opponents.length >= total) return;
    loading = true;
    refreshControls();
    try {
        const want = all ? total - opponents.length : PAGE;
        const data = await fetchPage(opponents.length, want);
        opponents = opponents.concat(data.opponents);
        total = data.total;
        appendRows(data.opponents);
    } finally {
        loading = false;
    }
    refreshControls();
}

function showMessage(text) {
    const message = document.getElementById("message");
    document.getElementById("result").hidden = true;
    if (!text) {
        message.hidden = true;
        return;
    }
    message.textContent = text;
    message.hidden = false;
}

async function loadBracket() {
    const mine = getCookie(COOKIE);
    if (!mine) {
        showMessage("Designate your aircraft to see its battle-rating bracket.");
        return;
    }
    let data;
    try {
        data = await fetchPage(0, PAGE);
    } catch (error) {
        showMessage(error.message);
        return;
    }
    mineAircraft = data.mine;
    opponents = data.opponents;
    total = data.total;
    if (!total) {
        showMessage("No other aircraft in this bracket yet — the crawl may still be filling in.");
        return;
    }
    showMessage(null);
    paintBracket();
}

document.addEventListener("DOMContentLoaded", () => {
    setupOwnship(() => loadBracket());

    document.getElementById("result").addEventListener("click", (event) => {
        const button = event.target.closest("[data-action]");
        if (!button) return;
        loadMore(button.dataset.action === "all");
    });

    loadBracket();
});
