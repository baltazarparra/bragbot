const express = require("express");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 3000;

// Rota Única para Validação do Webhook
app.get("/webhook", (req, res) => {
  const verifyToken = process.env.VERIFY_TOKEN; // Token definido no .env
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];

  if (req.query["hub.mode"] === "subscribe" && token === verifyToken) {
    console.log("[SUCESSO] Webhook validado!");
    res.status(200).send(challenge);
  } else {
    console.log("[ERRO] Token inválido ou modo incorreto");
    res.sendStatus(403);
  }
});

// Inicia o Servidor
app.listen(PORT, () => {
  console.log(`Servidor rodando em http://localhost:${PORT}/webhook`);
});
