const crypto = require("crypto");
const https = require("https");

const API_KEY = "cdc_4c5aef5a38d7668ea5f249f1f68f";
const API_SECRET = "EbwIHbqX30wEccOadwr+WBw7qUIJF0ClEXgBQVso+Sw=";

// Get quote first
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
  res.on("end", () => {
    const quote = JSON.parse(data);
    if (!quote.ok) {
      console.log("QUOTE_ERROR:" + JSON.stringify(quote));
      return;
    }
    
    const quoteId = quote.quotation.id;
    console.log("QUOTE_OK:" + quoteId);
    
    // Execute immediately
    const ts2 = Date.now().toString();
    const body2 = { quotation_id: quoteId };
    const bodyStr2 = JSON.stringify(body2);
    const signPayload2 = ts2 + "POST" + "/v1/crypto-purchase/orders" + bodyStr2;
    const signature2 = crypto.createHmac("sha256", API_SECRET).update(signPayload2).digest("base64");
    
    const options2 = {
      hostname: "wapi.crypto.com",
      path: "/v1/crypto-purchase/orders",
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Cdc-Api-Key": API_KEY,
        "Cdc-Api-Timestamp": ts2,
        "Cdc-Api-Signature": signature2
      }
    };
    
    const req2 = https.request(options2, (res2) => {
      let data2 = "";
      res2.on("data", (chunk) => { data2 += chunk; });
      res2.on("end", () => {
        console.log("BUY_RESULT:" + data2);
      });
    });
    
    req2.on("error", (e) => console.log("ERROR:" + e.message));
    req2.write(bodyStr2);
    req2.end();
  });
});

req.on("error", (e) => console.log("ERROR:" + e.message));
req.write(bodyStr);
req.end();
