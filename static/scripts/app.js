$(function () {
    if ($('#leaderboard').length && !$.fn.DataTable.isDataTable('#leaderboard')) {
        $('#leaderboard').DataTable({
            paging: false,
            info: false,
            searching: false,
            ordering: true,
            autoWidth: false
        });
    }
});

async function handleVote(side) {
    const battleRow = document.getElementById('battle-row');
    battleRow.classList.add('loading-active');

    const g1 = document.getElementById('girl1-img');
    const g2 = document.getElementById('girl2-img');

    const id1 = g1.getAttribute('data-id');
    const id2 = g2.getAttribute('data-id');

    const winner = (side === 'left') ? id1 : id2;
    const loser = (side === 'left') ? id2 : id1;

    try {
        // Enforce safe primitive strings mapped effectively to form encoding params
        const bodyStr = new URLSearchParams({ winner: String(winner), loser: String(loser) }).toString();
        
        console.log(`Sending vote: WINNER=${winner}, LOSER=${loser}`);

        const response = await fetch('/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: bodyStr
        });

        if (response.ok) {
            const data = await response.json();
            if (data.error) {
                alert(data.error);
            } else {
                updateUI(data);
            }
        } else {
            const errorMsg = await response.text();
            alert("Server Error: " + errorMsg);
            console.error("Non-200 Response:", errorMsg);
        }
    } catch (error) {
        console.error("Failed to submit vote:", error);
        alert("Network Error: Could not connect to server.");
    } finally {
        battleRow.classList.remove('loading-active');
    }
}

async function generateNewPair() {
    const battleRow = document.getElementById('battle-row');
    const btn = document.getElementById('generate-btn');
    const currentMax = btn.getAttribute('data-max');

    if (!currentMax || currentMax < 2) {
        console.error("Not enough images! Max ID:", currentMax);
        alert("Not enough data to generate pair! Make sure DB is synced.");
        return;
    }

    battleRow.classList.add('loading-active');

    let id1 = Math.floor(Math.random() * currentMax) + 1;
    let id2;
    do { id2 = Math.floor(Math.random() * currentMax) + 1; } while (id1 === id2);

    console.log(`Requesting random pair generation: ID_1=${id1}, ID_2=${id2}`);

    try {
        const bodyStr = new URLSearchParams({ id1: String(id1), id2: String(id2) }).toString();
        const response = await fetch('/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: bodyStr
        });

        if (response.ok) {
            const data = await response.json();
            if (data.error) {
                alert(data.error);
            } else {
                updateUI(data);
            }
        } else {
            const errorMsg = await response.text();
            alert("Server Error: " + errorMsg);
            console.error("Non-200 Response:", errorMsg);
        }
    } catch (err) {
        console.error("Fetch error:", err);
        alert("Network Error: Could not connect to server.");
    } finally {
        battleRow.classList.remove('loading-active');
    }
}

// SHARED UI UPDATE LOGIC
function updateUI(data) {
    const { girl1, girl2, leaderboard } = data;
    let g1 = document.getElementById('girl1-img');
    let g2 = document.getElementById('girl2-img');

    // Handle initialization when starting from pure 'placeholder' text
    if (!g1 || !g2) {
        const row = document.getElementById('battle-row');
        if (row && row.children.length >= 2) {
            row.children[0].innerHTML = `
                <div class="choice-container">
                    <img id="girl1-img" class="img-fluid choice-img" src="/static/images/${girl1.filename}" alt="Choice 1" data-id="${girl1.id}" onclick="handleVote('left')">
                    <p class="mt-2 fs-5"><strong>Rating:</strong> <span id="rating-1">${girl1.elo}</span></p>
                </div>
            `;
            row.children[1].innerHTML = `
                <div class="choice-container">
                    <img id="girl2-img" class="img-fluid choice-img" src="/static/images/${girl2.filename}" alt="Choice 2" data-id="${girl2.id}" onclick="handleVote('right')">
                    <p class="mt-2 fs-5"><strong>Rating:</strong> <span id="rating-2">${girl2.elo}</span></p>
                </div>
            `;
            g1 = document.getElementById('girl1-img');
            g2 = document.getElementById('girl2-img');
        }
    }

    if (g1 && g2 && girl1 && girl2) {
        g1.src = `/static/images/${girl1.filename}`;
        g2.src = `/static/images/${girl2.filename}`;
        g1.setAttribute('data-id', girl1.id);
        g2.setAttribute('data-id', girl2.id);

        document.getElementById('rating-1').innerText = girl1.elo;
        document.getElementById('rating-2').innerText = girl2.elo;
    }

    if (leaderboard) {
        updateLeaderboard(leaderboard);
    }
}

function updateLeaderboard(leaderboard) {
    if ($.fn.DataTable.isDataTable('#leaderboard')) {
        const table = $('#leaderboard').DataTable();
        table.clear();
        leaderboard.forEach((girl, index) => {
            table.row.add([
                index + 1,
                `<strong>${girl.elo}</strong>`,
                `<img class="leaderboard-img" src="/static/images/${girl.filename}" alt="Rank ${index + 1}">`
            ]);
        });
        table.draw(false);
    }
}