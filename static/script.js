document.getElementById("download-form").addEventListener("submit", async function (event) {
    event.preventDefault();

    let url = document.getElementById("video-url").value;
    let statusText = document.getElementById("status");

    if (!url) {
        statusText.innerText = "Please enter a valid URL!";
        return;
    }

    statusText.innerText = "Downloading... ⏳";

    try {
        let response = await fetch("/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ video_url: url })
        });

        let data = await response.json();

        if (data.download_url) {
            statusText.innerText = "Download Ready! Click below ⬇️";
            let downloadLink = document.createElement("a");
            downloadLink.href = data.download_url;
            downloadLink.innerText = "⬇️ Download Video";
            downloadLink.classList.add("download-btn"); // Add a class for styling

            // Find the card and append inside it
            let card = document.querySelector(".card");
            card.appendChild(downloadLink);
        } else {
            statusText.innerText = "Error: " + data.error;
        }
    } catch (error) {
        statusText.innerText = "Error: " + error.message;
    }
});
