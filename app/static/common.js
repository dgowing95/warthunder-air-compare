// Shared helpers used by every page: cookie storage, the aircraft autocomplete,
// and the "Your Aircraft" panel that lets the player set or clear their plane.
const COOKIE = "wtac_aircraft";

const VERDICT_LABEL = {
    good: "ADVANTAGE",
    average: "CONTESTED",
    poor: "DISADVANTAGE",
};

function setCookie(name, value) {
    const year = 60 * 60 * 24 * 365;
    document.cookie = `${name}=${encodeURIComponent(value)};max-age=${year};path=/;samesite=lax`;
}

function getCookie(name) {
    const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
    return match ? decodeURIComponent(match[1]) : null;
}

function clearCookie(name) {
    document.cookie = `${name}=;max-age=0;path=/;samesite=lax`;
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[ch]));
}

async function fetchSuggestions(term) {
    if (!term.trim()) return [];
    const response = await fetch(`/api/aircraft?q=${encodeURIComponent(term)}`);
    if (!response.ok) return [];
    return response.json();
}

async function fetchAircraft(identifier) {
    const response = await fetch(`/api/aircraft/${encodeURIComponent(identifier)}`);
    if (!response.ok) return null;
    return response.json();
}

function debounce(fn, wait) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), wait);
    };
}

function metaLine(aircraft) {
    return [aircraft.nation, aircraft.br_rb ? `BR ${aircraft.br_rb}` : null]
        .filter(Boolean)
        .join(" · ");
}

function statClass(winner, side) {
    if (winner === "unknown" || winner === "tie") return "unknown";
    return winner === side ? "win" : "lose";
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
            const thumb = aircraft.image_url
                ? `<img class="thumb" src="${escapeHtml(aircraft.image_url)}" alt="" loading="lazy">`
                : `<span class="thumb thumb--empty"></span>`;
            li.innerHTML =
                `${thumb}` +
                `<span class="s-name">${escapeHtml(aircraft.name)}</span>` +
                `<span class="s-meta">${escapeHtml(metaLine(aircraft))}</span>`;
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

// Toggle between the "set your aircraft" input and the saved ownship card.
async function showOwnship() {
    const field = document.getElementById("my-field");
    const card = document.getElementById("ownship-card");
    const saved = getCookie(COOKIE);

    if (!saved) {
        field.hidden = false;
        card.hidden = true;
        return;
    }

    const aircraft = await fetchAircraft(saved);
    field.hidden = true;
    card.hidden = false;

    const img = document.getElementById("ownship-img");
    const name = document.getElementById("ownship-name");
    const sub = document.getElementById("ownship-sub");

    if (aircraft) {
        name.textContent = aircraft.name;
        sub.textContent = metaLine(aircraft) || "Awaiting telemetry";
        if (aircraft.image_url) {
            img.src = aircraft.image_url;
            img.hidden = false;
        } else {
            img.hidden = true;
        }
    } else {
        // Saved before the crawler reached it: keep the name, no stats yet.
        name.textContent = saved;
        sub.textContent = "Not yet in database";
        img.hidden = true;
    }
}

// Wire the ownship panel's input + clear button. onChange fires whenever the
// saved aircraft changes (set or cleared), so each page can refresh its view.
function setupOwnship(onChange) {
    const myInput = document.getElementById("my-aircraft");
    showOwnship();

    setupAutocomplete(myInput, document.getElementById("my-suggestions"), (aircraft) => {
        setCookie(COOKIE, aircraft.slug || aircraft.name);
        myInput.value = "";
        showOwnship();
        if (onChange) onChange();
    });

    document.getElementById("clear-btn").addEventListener("click", () => {
        clearCookie(COOKIE);
        myInput.value = "";
        showOwnship();
        myInput.focus();
        if (onChange) onChange();
    });
}
