function generateIDS(max) {
    // Safety check
    if (max < 2) {
        console.warn("Not enough items to generate a match");
        return;
    }

    const randomForm = document.getElementById("random");
    const id1Field = document.getElementById("id1");
    const id2Field = document.getElementById("id2");

    let id1 = Math.floor(Math.random() * max) + 1;
    let id2;

    do {
        id2 = Math.floor(Math.random() * max) + 1;
    } while (id1 === id2);

    id1Field.value = id1;
    id2Field.value = id2;

    randomForm.submit();
}

function sendWinner(winnerID, loserID) {
    const sendForm = document.getElementById("send");
    const winnerField = document.getElementById("winnerField");
    const loserField = document.getElementById("loserField");

    winnerField.value = winnerID;
    loserField.value = loserID;

    sendForm.submit();
}
