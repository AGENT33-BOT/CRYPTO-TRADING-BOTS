// Execute Crypto.com purchase
const crypto = require('crypto');
const https = require('https');

const API_KEY = 'cdc_4c5aef5a38d7668ea5f249f1f68f';
const API_SECRET = 'EbwIHbqX30wEccOadwr+WBw7qUIJF0ClEXgBQVso+Sw=';

const ts = Date.now().toString();
const method = 'POST';
const path = '/v1/crypto-purchase/user-quotations';

const body = {
  quotation_id: '0346fa49-1444-4c20-a676-2a1e60549159'
};

const bodyStr = JSON.stringify(body);
const signPayload = ts + method + path + bodyStr;

const signature = crypto.createHmac('sha256', API_SECRET)
  .update(signPayload)
  .digest('base64');

const options = {
  hostname: 'wapi.crypto.com',
  path: path,
  method: method,
  headers: {
    'Content-Type': 'application/json',
    'Cdc-Api-Key': API_KEY,
    'Cdc-Api-Timestamp': ts,
    'Cdc-Api-Signature': signature
  }
};

const req = https.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => { data += chunk; });
  res.on('end', () => {
    console.log(data);
  });
});

req.on('error', (e) => {
  console.error('Error:', e.message);
});

req.write(bodyStr);
req.end();
