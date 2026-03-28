#!/usr/bin/env python3
"""
Test script to verify the table retrieval fix for region queries
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.core.table_retriever import get_relevant_tables

def test_region_queries():
    """Test various region queries to ensure correct table selection"""
    
    test_cases = [
        {
            "query": "what is the overall sales in each region?",
            "expected_primary": "customers",
            "description": "Customer region sales query"
        },
        {
            "query": "sales by state",
            "expected_primary": "customers", 
            "description": "Customer state sales query"
        },
        {
            "query": "revenue by geographic area",
            "expected_primary": "customers",
            "description": "Customer geographic revenue query"
        },
        {
            "query": "seller performance by region",
            "expected_primary": "sellers",
            "description": "Seller region query"
        },
        {
            "query": "merchant location analysis",
            "expected_primary": "sellers", 
            "description": "Seller location query"
        },
        {
            "query": "monthly order trends",
            "expected_primary": None,
            "description": "Non-region query (should use semantic matching)"
        }
    ]
    
    print("Testing table retrieval fixes...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected = test_case["expected_primary"]
        description = test_case["description"]
        
        print(f"\nTest {i}: {description}")
        print(f"Query: '{query}'")
        
        try:
            tables = get_relevant_tables(query, top_k=3)
            print(f"Selected tables: {tables}")
            
            if expected:
                if expected in tables:
                    print(f"✅ PASS: {expected} table correctly included")
                else:
                    print(f"❌ FAIL: {expected} table missing from selection")
            else:
                print(f"ℹ️  INFO: Using semantic matching (no specific expectation)")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_region_queries()
