// 1v1 Comparison page. Shared helpers (cookies, autocomplete, ownship panel)
// live in common.js, loaded first.

function dossierCard(aircraft, mine) {
    const image = aircraft.image_url
        ? `<img class="dossier__img" src="${escapeHtml(aircraft.image_url)}" alt="${escapeHtml(aircraft.name)}">`
        : `<div class="dossier__img dossier__img--empty">NO IMAGE</div>`;
    const flag = mine ? `<span class="dossier__flag">YOURS</span>` : "";
    return `
        <div class="dossier__card${mine ? " dossier__card--mine" : ""}">
            ${flag}
            ${image}
            <div class="dossier__name">${escapeHtml(aircraft.name)}</div>
            <div class="dossier__sub">${escapeHtml(metaLine(aircraft)) || "—"}</div>
        </div>`;
}

function renderComparison(data) {
    const result = document.getElementById("result");
    const verdict = data.verdict;
    const label = VERDICT_LABEL[verdict] || verdict.toUpperCase();
    // score runs roughly -1 (disadvantage) .. +1 (advantage); map to 0..100%.
    const needle = Math.max(0, Math.min(100, ((data.score + 1) / 2) * 100));

    const rows = data.dimensions.map((d) => {
        const mineCls = `col-mine ${statClass(d.winner, "mine")}`.trim();
        const targetCls = statClass(d.winner, "target");
        return `
        <tr>
            <td class="col-stat">${escapeHtml(d.label)}</td>
            <td class="${mineCls}">${escapeHtml(d.mine ?? "unknown")}</td>
            <td class="${targetCls}">${escapeHtml(d.target ?? "unknown")}</td>
        </tr>`;
    }).join("");

    result.innerHTML = `
        <div class="verdict ${verdict}">
            <div class="verdict__readout">${label}</div>
            <div class="verdict__sub">Estimated dogfight odds for your
                <strong>${escapeHtml(data.mine.name)}</strong>
                vs the <strong>${escapeHtml(data.target.name)}</strong></div>
            <div class="meter"><span class="meter__needle" style="left:${needle}%"></span></div>
            <div class="meter__scale"><span>Disadvantage</span><span>Even</span><span>Advantage</span></div>
        </div>
        <div class="dossier">
            ${dossierCard(data.mine, true)}
            <div class="dossier__vs">VS</div>
            ${dossierCard(data.target, false)}
        </div>
        <table>
            <thead>
                <tr>
                    <th class="col-stat">Stat</th>
                    <th class="col-mine">${escapeHtml(data.mine.name)}<span class="you-tag">YOURS</span></th>
                    <th>${escapeHtml(data.target.name)}</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>`;
    result.hidden = false;
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

async function runComparison(targetName) {
    const mine = getCookie(COOKIE);
    if (!mine) {
        showMessage("Designate your aircraft first.");
        return;
    }
    if (!targetName.trim()) return;
    const url = `/api/compare?mine=${encodeURIComponent(mine)}` +
        `&target=${encodeURIComponent(targetName)}`;
    const response = await fetch(url);
    const data = await response.json();
    if (!response.ok) {
        showMessage(data.error || "Comparison failed.");
        return;
    }
    showMessage(null);
    renderComparison(data);
}

document.addEventListener("DOMContentLoaded", () => {
    // Changing or clearing the ownship clears any stale comparison on screen.
    setupOwnship(() => showMessage(null));

    setupAutocomplete(
        document.getElementById("target-aircraft"),
        document.getElementById("target-suggestions"),
        (aircraft) => runComparison(aircraft.slug || aircraft.name));
});
