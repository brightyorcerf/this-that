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
}

async function generateNewPair() {
    const btn = document.getElementById('generate-btn');
    const currentMax = btn.getAttribute('data-max');
    if (!currentMax || currentMax < 2) {
        console.warn("Not enough items to generate a match");
        return;
    }

    let id1 = Math.floor(Math.random() * currentMax) + 1;
    let id2;
    do {
        id2 = Math.floor(Math.random() * currentMax) + 1;
    } while (id1 === id2);

    const response = await fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ id1, id2 })
    });

    if (response.ok) {
        const data = await response.json();
        if (data.error) {
            alert(data.error);
            return;
        }

        const g1 = document.getElementById('girl1-img');
        const g2 = document.getElementById('girl2-img');

        // Handle case if images are missing (placeholders initially placed)
        if (!g1 || !g2) {
            let choice1Container = document.querySelector(".row.mt-4 .col-md-6:nth-child(1)");
            let choice2Container = document.querySelector(".row.mt-4 .col-md-6:nth-child(2)");

            if (choice1Container && data.girl1 && data.girl1.id > 0) {
                choice1Container.innerHTML = `
                    <div class="choice-container">
                        <img id="girl1-img" class="img-fluid choice-img" src="/static/images/${data.girl1.filename}" alt="Choice 1" data-id="${data.girl1.id}" onclick="handleVote('left')">
                        <p class="mt-2 fs-5"><strong>Rating:</strong> <span id="rating-1">${data.girl1.elo}</span></p>
                    </div>
                `;
            }
            if (choice2Container && data.girl2 && data.girl2.id > 0) {
                choice2Container.innerHTML = `
                    <div class="choice-container">
                        <img id="girl2-img" class="img-fluid choice-img" src="/static/images/${data.girl2.filename}" alt="Choice 2" data-id="${data.girl2.id}" onclick="handleVote('right')">
                        <p class="mt-2 fs-5"><strong>Rating:</strong> <span id="rating-2">${data.girl2.elo}</span></p>
                    </div>
                `;
            }
        } else {
            g1.src = `/static/images/${data.girl1.filename}`;
            g1.setAttribute('data-id', data.girl1.id);

            g2.src = `/static/images/${data.girl2.filename}`;
            g2.setAttribute('data-id', data.girl2.id);

            document.getElementById('rating-1').innerText = data.girl1.elo;
            document.getElementById('rating-2').innerText = data.girl2.elo;
        }

        if (data.leaderboard) {
            updateLeaderboard(data.leaderboard);
        }
    } else {
        console.error("Failed to generate pair");
    }
}

function updateLeaderboard(leaderboard) {
    if ($.fn.DataTable.isDataTable('#leaderboard')) {
        const dt = $('#leaderboard').DataTable();
        dt.clear();
        leaderboard.forEach((girl, index) => {
            dt.row.add([
                index + 1,
                `<strong>${girl.elo}</strong>`,
                `<img class="leaderboard-img" src="/static/images/${girl.filename}" alt="${girl.filename}">`
            ]);
        });
        dt.draw();
    } else {
        const tbody = document.querySelector("#leaderboard tbody");
        if (tbody) {
            tbody.innerHTML = "";
            leaderboard.forEach((girl, index) => {
                const tr = document.createElement("tr");

                const tdRank = document.createElement("td");
                tdRank.innerText = index + 1;

                const tdRating = document.createElement("td");
                const strong = document.createElement("strong");
                strong.innerText = girl.elo;
                tdRating.appendChild(strong);

                const tdImage = document.createElement("td");
                const img = document.createElement("img");
                img.className = "leaderboard-img";
                img.src = `/static/images/${girl.filename}`;
                img.alt = girl.filename;
                tdImage.appendChild(img);

                tr.appendChild(tdRank);
                tr.appendChild(tdRating);
                tr.appendChild(tdImage);

                tbody.appendChild(tr);
            });
        }
    }
}
