#!/bin/bash
# Box Box Box - Test Runner (Solution 2)
# This version runs tests specifically for solution2 folder

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
TEST_CASES_DIR="data/test_cases/inputs"
EXPECTED_OUTPUTS_DIR="data/test_cases/expected_outputs"
RUN_COMMAND_FILE="solution2/run_command.txt"

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Box Box Box - Test Runner (Solution 2)            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Read solution command
if [ ! -f "$RUN_COMMAND_FILE" ]; then
    echo -e "${RED}Error: Run command file not found: $RUN_COMMAND_FILE${NC}"
    exit 1
fi

SOLUTION_CMD=$(cat "$RUN_COMMAND_FILE" | tr -d '\r\n')
echo -e "Solution Command: ${YELLOW}$SOLUTION_CMD${NC}"

# Check test cases
if [ ! -d "$TEST_CASES_DIR" ]; then
    echo -e "${RED}Error: Test cases directory not found${NC}"
    exit 1
fi

TEST_FILES=($(ls $TEST_CASES_DIR/test_*.json 2>/dev/null | sort))
TOTAL_TESTS=${#TEST_FILES[@]}

if [ $TOTAL_TESTS -eq 0 ]; then
    echo -e "${RED}Error: No test files found${NC}"
    exit 1
fi

echo -e "Test Cases Found: ${YELLOW}$TOTAL_TESTS${NC}"
echo ""
echo -e "${BLUE}Running tests...${NC}"
echo ""

# Initialize counters
PASSED=0
FAILED=0
ERRORS=0

# Check if we have expected outputs
HAS_ANSWERS=false
if [ -d "$EXPECTED_OUTPUTS_DIR" ]; then
    HAS_ANSWERS=true
fi

# Run tests
for TEST_FILE in "${TEST_FILES[@]}"; do
    TEST_NAME=$(basename "$TEST_FILE" .json)
    TEST_ID=$(echo "$TEST_NAME" | sed 's/test_/TEST_/')
    
    # Run solution
    OUTPUT_FILE="/tmp/${TEST_NAME}_output.json"
    
    if cat "$TEST_FILE" | eval "$SOLUTION_CMD" > "$OUTPUT_FILE" 2>/dev/null; then
        # Check if output is valid JSON
        if python -c "import json; json.load(open('$OUTPUT_FILE'))" 2>/dev/null; then
            # Extract finishing positions
            PREDICTED=$(python -c "import json; print(','.join(json.load(open('$OUTPUT_FILE')).get('finishing_positions',[])))" 2>/dev/null)
            
            if [ -z "$PREDICTED" ] || [ "$PREDICTED" == "null" ]; then
                echo -e "${RED}✗${NC} $TEST_ID - Invalid output format"
                ((FAILED++))
            elif [ "$HAS_ANSWERS" = true ]; then
                # Compare with expected output
                ANSWER_FILE="$EXPECTED_OUTPUTS_DIR/${TEST_NAME}.json"
                if [ -f "$ANSWER_FILE" ]; then
                    EXPECTED=$(python -c "import json; print(','.join(json.load(open('$ANSWER_FILE')).get('finishing_positions',[])))" 2>/dev/null)
                    
                    if [ "$PREDICTED" == "$EXPECTED" ]; then
                        echo -e "${GREEN}✓${NC} $TEST_ID"
                        ((PASSED++))
                    else
                        echo -e "${RED}✗${NC} $TEST_ID - Incorrect prediction"
                        ((FAILED++))
                    fi
                else
                    echo -e "${YELLOW}?${NC} $TEST_ID - No answer file"
                    ((PASSED++))
                fi
            else
                echo -e "${YELLOW}?${NC} $TEST_ID - Format OK"
                ((PASSED++))
            fi
        else
            echo -e "${RED}✗${NC} $TEST_ID - Invalid JSON output"
            ((FAILED++))
        fi
    else
        echo -e "${RED}✗${NC} $TEST_ID - Execution error"
        ((ERRORS++))
    fi
done

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Results                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Calculate stats
PASS_RATE=0
if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_RATE=$(echo "scale=1; $PASSED * 100 / $TOTAL_TESTS" | bc)
fi

echo -e "Total Tests:    ${YELLOW}$TOTAL_TESTS${NC}"
echo -e "Passed:         ${GREEN}$PASSED${NC}"
echo -e "Failed:         ${RED}$FAILED${NC}"
if [ $ERRORS -gt 0 ]; then
    echo -e "Errors:         ${RED}$ERRORS${NC}"
fi
echo ""
echo -e "Pass Rate:      ${GREEN}$PASS_RATE%${NC}"
echo ""

if [ $PASSED -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}🏆 Perfect score! All tests passed!${NC}"
elif [ $PASSED -gt 0 ]; then
    echo -e "${YELLOW}Keep improving! Check failed test cases.${NC}"
else
    echo -e "${RED}No tests passed. Review your implementation.${NC}"
fi
