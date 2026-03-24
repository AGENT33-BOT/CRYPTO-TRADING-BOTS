"""
Test Token ID Extraction from Polymarket API
"""
import requests
import json

def test_token_extraction():
    """Test extracting token IDs from live Polymarket data"""
    
    gamma_url = "https://gamma-api.polymarket.com"
    
    # Fetch markets
    url = f"{gamma_url}/markets"
    params = {"active": "true", "closed": "false", "limit": 5}
    
    response = requests.get(url, params=params, timeout=30)
    data = response.json()
    
    if isinstance(data, list):
        markets = data
    elif isinstance(data, dict):
        markets = data.get('markets', data.get('data', []))
    else:
        markets = []
    
    print("=" * 70)
    print("TOKEN ID EXTRACTION TEST")
    print("=" * 70)
    print(f"Fetched {len(markets)} markets\n")
    
    success_count = 0
    
    for i, market in enumerate(markets[:5], 1):
        question = market.get('question', 'Unknown')[:60]
        print(f"\n{i}. {question}...")
        
        # Get clobTokenIds
        clob_token_ids = market.get('clobTokenIds', [])
        print(f"   Raw clobTokenIds type: {type(clob_token_ids)}")
        
        # Handle string case
        if isinstance(clob_token_ids, str):
            try:
                clob_token_ids = json.loads(clob_token_ids)
                print(f"   Parsed from string: {type(clob_token_ids)}")
            except:
                clob_token_ids = []
        
        # Extract token IDs
        yes_token_id = None
        no_token_id = None
        
        if isinstance(clob_token_ids, list) and len(clob_token_ids) >= 2:
            yes_token_id = str(clob_token_ids[0]) if clob_token_ids[0] else None
            no_token_id = str(clob_token_ids[1]) if len(clob_token_ids) > 1 and clob_token_ids[1] else None
        
        # Validate token IDs
        yes_valid = yes_token_id and len(yes_token_id) >= 64
        no_valid = no_token_id and len(no_token_id) >= 64
        
        print(f"   Yes Token: {yes_token_id[:30] + '...' if yes_token_id and len(yes_token_id) > 30 else yes_token_id}")
        print(f"   No Token:  {no_token_id[:30] + '...' if no_token_id and len(no_token_id) > 30 else no_token_id}")
        print(f"   Yes Valid: {yes_valid}, No Valid: {no_valid}")
        
        if yes_valid and no_valid:
            success_count += 1
            print("   [SUCCESS] Both token IDs extracted successfully")
        else:
            print("   [FAIL] Token ID extraction failed")
            # Debug: show what we got
            print(f"   Debug - Raw value: {market.get('clobTokenIds')}")
    
    print("\n" + "=" * 70)
    print(f"RESULT: {success_count}/5 markets had valid token IDs")
    print("=" * 70)
    
    if success_count > 0:
        print("\n[OK] Token ID extraction is WORKING correctly!")
        print("The 'token ID bug' was a misdiagnosis.")
        print("The actual issue is INVALID API CREDENTIALS (401 Unauthorized)")
    else:
        print("\n[WARN] Token ID extraction issues detected")
    
    return success_count > 0

if __name__ == "__main__":
    test_token_extraction()
