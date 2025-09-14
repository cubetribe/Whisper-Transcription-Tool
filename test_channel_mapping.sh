#!/bin/bash
#
# Test script for Channel-Based Speaker Mapping validation
# Usage: ./test_channel_mapping.sh [test_type]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$SCRIPT_DIR/src/whisper_transcription_tool/module3_phone"

echo -e "${BLUE}🚀 Channel-Based Speaker Mapping Test Suite${NC}"
echo "=============================================="

# Check if Python environment is set up
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not found${NC}"
    exit 1
fi

# Check if virtual environment is active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not active. Trying to activate...${NC}"
    if [[ -f "$SCRIPT_DIR/venv_new/bin/activate" ]]; then
        source "$SCRIPT_DIR/venv_new/bin/activate"
        echo -e "${GREEN}✅ Activated venv_new${NC}"
    elif [[ -f "$SCRIPT_DIR/venv/bin/activate" ]]; then
        source "$SCRIPT_DIR/venv/bin/activate"
        echo -e "${GREEN}✅ Activated venv${NC}"
    else
        echo -e "${RED}❌ No virtual environment found${NC}"
        exit 1
    fi
fi

# Function to run a test
run_test() {
    local test_name=$1
    local test_command=$2

    echo -e "\n${BLUE}📋 Running: $test_name${NC}"
    echo "----------------------------------------"

    if eval "$test_command"; then
        echo -e "${GREEN}✅ $test_name: PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_name: FAILED${NC}"
        return 1
    fi
}

# Main test function
run_tests() {
    local test_type=${1:-"all"}
    local failed_tests=0
    local total_tests=0

    case $test_type in
        "basic")
            echo -e "${YELLOW}🔍 Running basic validation tests${NC}"
            total_tests=2

            run_test "List Audio Devices" "python3 '$MODULE_DIR/cli_test_channel_mapping.py' devices" || ((failed_tests++))
            run_test "Get Recommendations" "python3 '$MODULE_DIR/cli_test_channel_mapping.py' recommend" || ((failed_tests++))
            ;;

        "integration")
            echo -e "${YELLOW}🔧 Running integration tests${NC}"
            total_tests=3

            # Create test data
            run_test "Create Test Data" "python3 '$MODULE_DIR/cli_test_channel_mapping.py' create-test --output /tmp/channel_test_data" || ((failed_tests++))

            # Test merge if test data was created
            if [[ -f "/tmp/channel_test_data/microphone_transcript.json" && -f "/tmp/channel_test_data/system_audio_transcript.json" ]]; then
                run_test "Test Transcript Merge (TXT)" "python3 '$MODULE_DIR/cli_test_channel_mapping.py' merge --mic '/tmp/channel_test_data/microphone_transcript.json' --sys '/tmp/channel_test_data/system_audio_transcript.json' --user 'Dennis' --contact 'Kunde' --format txt" || ((failed_tests++))
                run_test "Test Transcript Merge (JSON)" "python3 '$MODULE_DIR/cli_test_channel_mapping.py' merge --mic '/tmp/channel_test_data/microphone_transcript.json' --sys '/tmp/channel_test_data/system_audio_transcript.json' --user 'Dennis' --contact 'Kunde' --format json" || ((failed_tests++))
            else
                echo -e "${RED}❌ Test data creation failed, skipping merge tests${NC}"
                ((failed_tests += 2))
            fi
            ;;

        "comprehensive"|"all")
            echo -e "${YELLOW}🧪 Running comprehensive test suite${NC}"
            total_tests=1

            run_test "Comprehensive Test Suite" "python3 '$MODULE_DIR/test_channel_mapping.py'" || ((failed_tests++))
            ;;

        "validate")
            if [[ -z "$2" || -z "$3" ]]; then
                echo -e "${RED}❌ Usage: $0 validate <mic_device_id> <sys_device_id>${NC}"
                echo -e "${YELLOW}💡 Run '$0 basic' first to see available devices${NC}"
                exit 1
            fi

            echo -e "${YELLOW}🔍 Validating specific device setup${NC}"
            total_tests=1

            run_test "Device Setup Validation" "python3 '$MODULE_DIR/cli_test_channel_mapping.py' validate --mic '$2' --sys '$3' --user 'Test User' --contact 'Test Contact'" || ((failed_tests++))
            ;;

        *)
            echo -e "${RED}❌ Unknown test type: $test_type${NC}"
            echo -e "${YELLOW}Available test types:${NC}"
            echo "  basic          - Basic device and recommendation tests"
            echo "  integration    - Integration tests with sample data"
            echo "  comprehensive  - Full test suite (default)"
            echo "  validate <mic> <sys> - Validate specific device setup"
            exit 1
            ;;
    esac

    # Summary
    echo -e "\n${BLUE}📊 TEST SUMMARY${NC}"
    echo "=============================================="

    local passed_tests=$((total_tests - failed_tests))
    local success_rate=$((passed_tests * 100 / total_tests))

    if [[ $failed_tests -eq 0 ]]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED! ($passed_tests/$total_tests)${NC}"
        echo -e "${GREEN}Channel-based speaker mapping is ready for use.${NC}"
    else
        echo -e "${RED}❌ $failed_tests out of $total_tests tests failed${NC}"
        echo -e "${YELLOW}Success rate: $success_rate%${NC}"

        if [[ $success_rate -ge 80 ]]; then
            echo -e "${YELLOW}⚠️  Most tests passed. Review failed tests before production use.${NC}"
        else
            echo -e "${RED}❌ Multiple tests failed. Review implementation before use.${NC}"
        fi
    fi

    return $failed_tests
}

# Check for required files
if [[ ! -f "$MODULE_DIR/test_channel_mapping.py" ]]; then
    echo -e "${RED}❌ Test file not found: $MODULE_DIR/test_channel_mapping.py${NC}"
    exit 1
fi

if [[ ! -f "$MODULE_DIR/cli_test_channel_mapping.py" ]]; then
    echo -e "${RED}❌ CLI test file not found: $MODULE_DIR/cli_test_channel_mapping.py${NC}"
    exit 1
fi

# Make sure the test files are executable
chmod +x "$MODULE_DIR/test_channel_mapping.py"
chmod +x "$MODULE_DIR/cli_test_channel_mapping.py"

# Run the specified tests
run_tests "$@"
test_result=$?

# Cleanup
if [[ -d "/tmp/channel_test_data" ]]; then
    rm -rf "/tmp/channel_test_data"
    echo -e "${BLUE}🧹 Cleaned up test data${NC}"
fi

echo -e "\n${BLUE}Test execution completed.${NC}"
exit $test_result