// Combined: Get quote AND execute immediately
const crypto = require('crypto');
const https = require('https');

const API_KEY = 'cdc_4c5aef5a38d7668ea5f249f1f68f';
const API_SECRET = 'EbwIHbqX30wEccOadwr+WBw7qUIJF0ClEXgBQVso+Sw=';

function sign(method, path, body) {
  const ts = Date.now().toString();
  const bodyStr = JSON.stringify(body);
  const signPayload = ts + method + path + bodyStr;
  const signature = crypto.createHmac('sha256', API_SECRET).update(signPayload).digest('base64');
  return { ts, bodyStr, signature };
}

// Step 1: Get quote
const quoteBody = { from_currency: 'USD', to_currency: 'CRO', to_amount: 100 };
const { ts: ts1, bodyStr: bodyStr1, signature: sig1 } = sign('POST', '/v1/crypto-purchase/quotations', quoteBody);

const options1 = {
  hostname: 'wapi.crypto.com',
  path: '/v1/crypto-purchase/quotations',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Cdc-Api-Key': API_KEY,
    'Cdc-Api-Timestamp': ts1,
    'Cdc-Api-Signature': sig1
  }
};

const req1 = https.request(options1, (res) => {
  let data = '';
  res.on('data', (chunk) => { data += chunk; });
  res.on('end', () => {
    const quote = JSON.parse(data);
    if (!quote.ok) {
      console.log('Quote failed:', data);
      return;
    }
    
    const quoteId = quote.quotation.id;
    console.log('Got quote:', quoteId);
    
    // Step 2: Execute immediately
    const execBody = { quotation_id: quoteId };
    const { ts: ts2, bodyStr: bodyStr2, signature: sig2 } = sign('POST', '/v1/crypto-purchase/orders', execBody);
    
    const options2 = {
      hostname: 'wapi.crypto.com',
      path: '/v1/crypto-purchase/orders',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cdc-Api-Key': API_KEY,
        'Cdc-Api-Timestamp': ts2,
        'Cdc-Api-Signature': sig2
      }
    };
    
    const req2 = https.request(options2, (res2) => {
      let data2 = '';
      res2.on('data', (chunk) => { data2 += chunk; });
      res2.on('end', () => {
        console.log('Execute result:', data2);
      });
    });
    
    req2.on('error', (e) => console.error('Error:', e.message));
    req2.write(bodyStr2);
    req2.end();
  });
});

req1.on('error', (e) => console.error('Error:', e.message));
req1.write(bodyStr1);
req1.end();
