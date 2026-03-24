const crypto = require('crypto');

const API_KEY = 'cdc_4c5aef5a38d7668ea5f249f1f68f';
const API_SECRET = 'EbwIHbqX30wEccOadwr+WBw7qUIJF0ClEXgBQVso+Sw=';

async function main() {
  const ts = Date.now().toString();
  
  // Try buying CRO with $1 USD
  const body = { from_currency: 'USD', to_currency: 'CRO', to_amount: 1 };
  const bodyStr = JSON.stringify(body);
  
  const signPayload = ts + 'POST' + '/v1/private/crypto-purchase/quotations' + bodyStr;
  const signature = crypto.createHmac('sha256', API_SECRET).update(signPayload).digest('base64');
  
  const headers = {
    'Content-Type': 'application/json',
    'Cdc-Api-Key': API_KEY,
    'Cdc-Api-Timestamp': ts,
    'Cdc-Api-Signature': signature
  };
  
  const r = await fetch('https://wapi.crypto.com/v1/crypto-purchase/quotations', {
    method: 'POST',
    headers,
    body: bodyStr
  });
  
  const data = await r.json();
  console.log(JSON.stringify(data, null, 2));
}

main().catch(console.error);
