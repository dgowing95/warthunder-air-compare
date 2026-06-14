const COOKIE = "wtac_aircraft";

function setCookie(name, value) {
    const year = 60 * 60 * 24 * 365;
    document.cookie = `${name}=${encodeURIComponent(value)};max-age=${year};path=/;samesite=lax`;
}

function getCookie(name) {
    const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
    return match ? decodeURIComponent(match[1]) : null;
}

async function fetchSuggestions(term) {
    if (!term.trim()) return [];
    const response = await fetch(`/api/aircraft?q=${encodeURIComponent(term)}`);
    if (!response.ok) return [];
    return response.json();
}

function debounce(fn, wait) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), wait);
    };
}

// Wires an input to a suggestions list. onChoose receives the picked aircraft.
function setupAutocomplete(input, list, onChoose) {
    let items = [];
    let activeIndex = -1;

    function close() {
        list.hidden = true;
        list.innerHTML = "";
        items = [];
        activeIndex = -1;
    }

    function render(results) {
        items = results;
        activeIndex = -1;
        list.innerHTML = "";
        if (!results.length) {
            close();
            return;
        }
        results.forEach((aircraft, index) => {
            const li = document.createElement("li");
            const meta = [aircraft.nation, aircraft.br_rb ? `BR ${aircraft.br_rb}` : null]
                .filter(Boolean)
                .join(" · ");
            li.innerHTML = `<span>${aircraft.name}</span><span class="meta">${meta}</span>`;
            li.addEventListener("mousedown", (event) => {
                event.preventDefault();
                choose(index);
            });
            list.appendChild(li);
        });
        list.hidden = false;
    }

    function choose(index) {
        const aircraft = items[index];
        if (!aircraft) return;
        input.value = aircraft.name;
        close();
        onChoose(aircraft);
    }

    function highlight(delta) {
        if (!items.length) return;
        activeIndex = (activeIndex + delta + items.length) % items.length;
        [...list.children].forEach((li, i) =>
            li.classList.toggle("active", i === activeIndex));
    }

    const update = debounce(async () => {
        render(await fetchSuggestions(input.value));
    }, 180);

    input.addEventListener("input", update);
    input.addEventListener("focus", update);
    input.addEventListener("blur", () => setTimeout(close, 150));
    input.addEventListener("keydown", (event) => {
        if (event.key === "ArrowDown") { event.preventDefault(); highlight(1); }
        else if (event.key === "ArrowUp") { event.preventDefault(); highlight(-1); }
        else if (event.key === "Enter") {
            event.preventDefault();
            if (activeIndex >= 0) choose(activeIndex);
            else onChoose({ name: input.value });
        }
    });
}

function statClass(winner, side) {
    if (winner === "unknown" || winner === "tie") return "";
    return winner === side ? "win" : "lose";
}

function renderComparison(data) {
    const result = document.getElementById("result");
    const rows = data.dimensions.map((d) => `
        <tr>
            <td class="col-stat">${d.label}</td>
            <td class="${statClass(d.winner, "mine")}">${d.mine ?? "unknown"}</td>
            <td class="${statClass(d.winner, "target")}">${d.target ?? "unknown"}</td>
        </tr>`).join("");

    result.innerHTML = `
        <div class="verdict ${data.verdict}">
            ${data.verdict}
            <small>Your odds in a dogfight against the ${data.target.name}</small>
        </div>
        <table>
            <thead>
                <tr>
                    <th class="col-stat">Stat</th>
                    <th>${data.mine.name}</th>
                    <th>${data.target.name}</th>
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
        showMessage("Set your aircraft first.");
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

function showSavedAircraft() {
    const saved = getCookie(COOKIE);
    const label = document.getElementById("my-saved");
    label.textContent = saved ? `Saved: ${saved}` : "Not set yet.";
}

document.addEventListener("DOMContentLoaded", () => {
    const myInput = document.getElementById("my-aircraft");
    const targetInput = document.getElementById("target-aircraft");

    const saved = getCookie(COOKIE);
    if (saved) myInput.value = saved;
    showSavedAircraft();

    setupAutocomplete(myInput, document.getElementById("my-suggestions"), (aircraft) => {
        const name = aircraft.slug || aircraft.name;
        setCookie(COOKIE, name);
        showSavedAircraft();
    });

    setupAutocomplete(targetInput, document.getElementById("target-suggestions"),
        (aircraft) => runComparison(aircraft.slug || aircraft.name));
});
