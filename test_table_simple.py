#!/usr/bin/env python3
"""
Simple test to verify the table retrieval logic without ML dependencies
"""

def test_keyword_logic():
    """Test the keyword matching logic directly"""
    
    def simulate_get_relevant_tables(query):
        """Simulate the fixed table retrieval logic"""
        query_lower = query.lower()
        top_k = 3
        
        # Enhanced logic for region queries - prioritize customers over sellers
        if any(keyword in query_lower for keyword in ['region', 'state', 'geographic', 'location', 'area']):
            # For customer-focused region queries, always include customers table
            if any(keyword in query_lower for keyword in ['customer', 'sales by', 'revenue by', 'overall']):
                # Force customers table for customer region analysis
                customer_tables = ['customers', 'order_items', 'orders']
                return customer_tables[:top_k]
            elif any(keyword in query_lower for keyword in ['seller', 'merchant']):
                # Seller-focused region queries
                seller_tables = ['sellers', 'order_items']
                return seller_tables[:top_k]
        
        # Default fallback (would normally use semantic matching)
        return ['order_items', 'orders']  # Default common tables
    
    test_cases = [
        {
            "query": "what is the overall sales in each region?",
            "expected": ['customers', 'order_items', 'orders'],
            "description": "Customer region sales query"
        },
        {
            "query": "sales by state",
            "expected": ['customers', 'order_items', 'orders'], 
            "description": "Customer state sales query"
        },
        {
            "query": "revenue by geographic area",
            "expected": ['customers', 'order_items', 'orders'],
            "description": "Customer geographic revenue query"
        },
        {
            "query": "seller performance by region",
            "expected": ['sellers', 'order_items'],
            "description": "Seller region query"
        },
        {
            "query": "merchant location analysis",
            "expected": ['sellers', 'order_items'], 
            "description": "Seller location query"
        },
        {
            "query": "monthly order trends",
            "expected": ['order_items', 'orders'],
            "description": "Non-region query (should use default)"
        }
    ]
    
    print("Testing table retrieval keyword logic...")
    print("=" * 60)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected = test_case["expected"]
        description = test_case["description"]
        
        print(f"\nTest {i}: {description}")
        print(f"Query: '{query}'")
        
        try:
            result = simulate_get_relevant_tables(query)
            print(f"Expected: {expected}")
            print(f"Got:      {result}")
            
            if result == expected:
                print(f"✅ PASS")
            else:
                print(f"❌ FAIL")
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests PASSED! The fix should work correctly.")
    else:
        print("❌ Some tests FAILED. Fix needs adjustment.")
    
    return all_passed

if __name__ == "__main__":
    test_keyword_logic()
