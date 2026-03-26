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
        const response = await fetch('/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ winner, loser })
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

    if (!currentMax || currentMax < 2) return;

    battleRow.classList.add('loading-active');

    let id1 = Math.floor(Math.random() * currentMax) + 1;
    let id2;
    do { id2 = Math.floor(Math.random() * currentMax) + 1; } while (id1 === id2);

    try {
        const response = await fetch('/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ id1, id2 })
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
    const g1 = document.getElementById('girl1-img');
    const g2 = document.getElementById('girl2-img');

    if (g1 && g2) {
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