# Black Box Tests - Thesis Testing Suite

This folder contains all black box test suites for the thesis project.

## Test Files

| File | Test Category | Test IDs | Status |
|------|--------------|----------|--------|
| **test_landuse_validation.py** | Input Validation Tests (BB-VAL) | BB-VAL-01 to BB-VAL-04 | ✅ 4/4 Passing |
| **test_balance_algorithm.py** | Balance Algorithm Tests (BB-BAL) | BB-BAL-01 to BB-BAL-03 | ✅ 3/3 Passing |
| **test_calculation_accuracy.py** | Calculation Accuracy Tests (BB-CALC) | BB-CALC-01 to BB-CALC-06 | ✅ 6/6 Passing |
| **test_e2e_workflow.py** | End-to-End Workflow Tests (BB-E2E) | BB-E2E-01 to BB-E2E-04 | ✅ 4/4 Passing |

## Total Test Coverage

- **Total Test Cases**: 17
- **Passed**: 17 ✅
- **Failed**: 0 ❌
- **Success Rate**: 100%

## Running Tests

Execute individual test suites:

```bash
# BB-VAL: Input Validation Tests
python3 black_box_tests/test_landuse_validation.py

# BB-BAL: Balance Algorithm Tests
python3 black_box_tests/test_balance_algorithm.py

# BB-CALC: Calculation Accuracy Tests
python3 black_box_tests/test_calculation_accuracy.py

# BB-E2E: End-to-End Workflow Tests
python3 black_box_tests/test_e2e_workflow.py
```

## Test Categories

### BB-VAL: Input Validation Tests
Tests validation logic for user inputs including 3-point limit enforcement, negative value checks, child percentage calculations, and change tracking.

### BB-BAL: Balance Algorithm Tests
Tests the iterative balance algorithms for energy and WS storage convergence, including iteration limits and timeout handling.

### BB-CALC: Calculation Accuracy Tests
Tests formula evaluation engine including arithmetic operations, conditional logic (IF statements), cross-module references, and parent-child aggregations.

### BB-E2E: End-to-End Workflow Tests
Tests complete user workflows from frontend interaction through backend processing to database persistence, including cascade triggering and error handling.

## Documentation

Each test suite has corresponding documentation:
- `BB_VAL_INPUT_VALIDATION_TESTS.md` - Table 5.6 & Figure 5.3
- `BB_BAL_BALANCE_ALGORITHM_TESTS.md` - Table 5.5 & Figure 5.4
- `BB_CALC_CALCULATION_ACCURACY_TESTS.md` - Table 5.8 & Figure 5.5
- `BB_E2E_END_TO_END_WORKFLOW_TESTS.md` - Table 5.9 & Figure 5.6

## Automatic Cleanup

All tests automatically restore original values after execution to prevent data corruption.

---

**Last Updated**: 2026-01-13  
**Test Framework**: Django Test Client + Python 3.9
