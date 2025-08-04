document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("chat-input");
  const button = document.getElementById("send-button");
  const chatBox = document.getElementById("chat-box");

  function addMessage(text, sender, id = null) {
    const bubble = document.createElement("div");
    bubble.className = "bubble " + sender;
    bubble.innerHTML = text
      .replace(/\n/g, "<br>")
      .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
      .replace(/__(.*?)__/g, "<i>$1</i>");
    if (id) bubble.id = id;
    chatBox.appendChild(bubble);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function updateMessage(id, newText) {
    const bubble = document.getElementById(id);
    if (bubble) {
      bubble.innerHTML = newText
        .replace(/\n/g, "<br>")
        .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
        .replace(/__(.*?)__/g, "<i>$1</i>");
    }
  }

  // הודעת פתיחה
  setTimeout(() => {
    addMessage("Hello! I'm ImaginBot 🤖<br>What can I help you with today?", "bot");
  }, 300);

  async function sendMessage() {
    const question = input.value.trim();
    if (!question) return;

    addMessage(question, "user");
    input.value = "";

    const loadingId = "bot-loading-" + Date.now();
    addMessage("Typing...", "bot", loadingId);

    try {
      const res = await fetch("http://localhost:8001/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
      });

      const data = await res.json();
      const answer = data.answer || "❌ Sorry, I couldn't understand the question.";
      updateMessage(loadingId, answer);
    } catch (err) {
      console.error("❌ Error:", err);
      updateMessage(loadingId, "❌ An error occurred while communicating with the server.");
    }
  }

  button.addEventListener("click", sendMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
});
