$(function () {
    $('#leaderboard').DataTable({
        pageLength: 10,
        ordering: true,
        searching: false,
        lengthChange: false
    });
});

async function handleVote(side) {
    const g1 = document.getElementById('girl1-img');
    const g2 = document.getElementById('girl2-img');

    // Get current IDs from the data attributes
    const id1 = g1.getAttribute('data-id');
    const id2 = g2.getAttribute('data-id');

    const winner = (side === 'left') ? id1 : id2;
    const loser = (side === 'left') ? id2 : id1;

    // Utilize URLSearchParams to map effectively back to Flask's standard request.form
    const response = await fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ winner, loser })
    });

    if (response.ok) {
        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        // UPDATE THE STATE FOR THE NEXT VOTE
        g1.src = `/static/images/${data.girl1.filename}`;
        g1.setAttribute('data-id', data.girl1.id);

        g2.src = `/static/images/${data.girl2.filename}`;
        g2.setAttribute('data-id', data.girl2.id);

        document.getElementById('rating-1').innerText = data.girl1.elo;
        document.getElementById('rating-2').innerText = data.girl2.elo;

        if (data.leaderboard) {
            updateLeaderboard(data.leaderboard);
        }
    } else {
        console.error("Failed to submit vote");
    }
}// 1. Initialize DataTables without the "Default" junk (No paging/search/info)
$(function () {
    if ($('#leaderboard').length) {
        $('#leaderboard').DataTable({
            paging: false,    // Kills Previous/Next buttons
            info: false,      // Kills "Showing 1 to 10" text
            searching: false, // Kills Search box
            ordering: true,   // Keeps sorting enabled
            autoWidth: false
        });
    }
});

// 2. Fixed Generate Function (Handles data-attributes correctly)
async function generateNewPair() {
    const btn = document.getElementById('generate-btn');
    const currentMax = btn.getAttribute('data-max');

    if (!currentMax || currentMax < 2) return;

    // UI Feedback: Dim the images so user knows it's loading
    document.querySelectorAll('.choice-img').forEach(img => img.style.opacity = '0.5');

    // Generate random IDs locally
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
            updateUI(data);
        }
    } catch (err) {
        console.error("Fetch error:", err);
    } finally {
        document.querySelectorAll('.choice-img').forEach(img => img.style.opacity = '1');
    }
}

// 3. Consolidated UI Update
function updateUI(data) {
    const { girl1, girl2, leaderboard } = data;
    const g1 = document.getElementById('girl1-img');
    const g2 = document.getElementById('girl2-img');

    if (g1 && g2) {
        // Update Images
        g1.src = `/static/images/${girl1.filename}`;
        g2.src = `/static/images/${girl2.filename}`;

        // Update Data IDs for the next vote
        g1.setAttribute('data-id', girl1.id);
        g2.setAttribute('data-id', girl2.id);

        // Update ELO Display
        document.getElementById('rating-1').innerText = girl1.elo;
        document.getElementById('rating-2').innerText = girl2.elo;
    }

    if (leaderboard) {
        updateLeaderboard(leaderboard);
    }
}

// 4. Clean Leaderboard Update (Using DataTable API)
function updateLeaderboard(leaderboard) {
    const table = $('#leaderboard').DataTable();
    if (table) {
        table.clear(); // Empty the table
        leaderboard.forEach((girl, index) => {
            table.row.add([
                index + 1,
                `<strong>${girl.elo}</strong>`,
                `<img class="leaderboard-img" src="/static/images/${girl.filename}" alt="Rank ${index + 1}">`
            ]).draw(false); // Add row and redraw
        });
    }
}