const crypto = require("crypto");
const https = require("https");

const API_KEY = "cdc_4c5aef5a38d7668ea5f249f1f68f";
const API_SECRET = "EbwIHbqX30wEccOadwr+WBw7qUIJF0ClEXgBQVso+Sw=";

const ts = Date.now().toString();
const body = {from_currency: "USD", to_currency: "LINK", to_amount: 10};
const bodyStr = JSON.stringify(body);

const signPayload = ts + "POST" + "/v1/crypto-purchase/quotations" + bodyStr;
const signature = crypto.createHmac("sha256", API_SECRET).update(signPayload).digest("base64");

const options = {
  hostname: "wapi.crypto.com",
  path: "/v1/crypto-purchase/quotations",
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Cdc-Api-Key": API_KEY,
    "Cdc-Api-Timestamp": ts,
    "Cdc-Api-Signature": signature
  }
};

const req = https.request(options, (res) => {
  let data = "";
  res.on("data", (chunk) => { data += chunk; });
  res.on("end", () => { console.log(data); });
});

req.on("error", (e) => console.log("Error:", e.message));
req.write(bodyStr);
req.end();
