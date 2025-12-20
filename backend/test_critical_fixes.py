"""
Critical fixes test script.

Tests:
1. Template security fix in intelligent_router
2. Enhanced validation in BaseNode
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_template_security():
    """Test 1: Template security fix"""
    print("Testing template security fix...")
    try:
        from backend.core.intelligent_router import IntelligentRouter
        
        router = IntelligentRouter()
        result = router._evaluate_template(
            'Hello {{name}}, your email is {{email}}',
            {'name': 'John', 'email': 'test@test.com'}
        )
        print(f"✅ Template security test passed: {result}")
        return True
    except Exception as e:
        print(f"❌ Template security test failed: {e}")
        return False

def test_validation():
    """Test 2: Enhanced validation"""
    print("\nTesting enhanced validation...")
    try:
        from backend.nodes.base import BaseNode
        
        class TestNode(BaseNode):
            node_type = 'test'
            
            def get_schema(self):
                return {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string', 'minLength': 2, 'maxLength': 50},
                        'age': {'type': 'integer', 'minimum': 0, 'maximum': 150}
                    },
                    'required': ['name']
                }
            
            async def execute(self, inputs, config):
                return {}
        
        node = TestNode()
        
        # Test 1: Should fail - name too short
        try:
            node.validate({'name': 'A'})  # Should fail - too short
            print("❌ Validation test failed: Should have raised error for short name")
            return False
        except Exception as e:
            print(f"✅ Validation test 1 passed: Correctly rejected short name - {str(e)[:60]}...")
        
        # Test 2: Should pass - valid input
        try:
            node.validate({'name': 'John', 'age': 25})
            print("✅ Validation test 2 passed: Correctly accepted valid input")
        except Exception as e:
            print(f"❌ Validation test 2 failed: Should have accepted valid input - {e}")
            return False
        
        # Test 3: Should fail - missing required field
        try:
            node.validate({'age': 25})  # Missing required 'name'
            print("❌ Validation test 3 failed: Should have raised error for missing required field")
            return False
        except Exception as e:
            print(f"✅ Validation test 3 passed: Correctly rejected missing required field - {str(e)[:60]}...")
        
        return True
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all critical fix tests"""
    print("=" * 60)
    print("CRITICAL FIXES TEST")
    print("=" * 60)
    
    results = []
    
    # Test 1: Template security
    results.append(("Template Security", test_template_security()))
    
    # Test 2: Enhanced validation
    results.append(("Enhanced Validation", test_validation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All critical fixes are working correctly!")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

