# Phone Recording System - Test Suite

This comprehensive test suite validates the complete Phone Recording System including Python backend, Swift frontend integration, web interface, and audio system components.

## 🏗️ Test Architecture

```
tests/
├── unit/                    # Unit tests for individual components
├── integration/            # Integration tests between modules
├── e2e/                   # End-to-end workflow tests
├── audio_system/          # Audio hardware and BlackHole tests
├── web/                   # Web interface and API tests
├── mock_data/             # Mock data generators
├── conftest.py           # PyTest configuration and fixtures
└── README.md             # This file
```

## 🧪 Test Categories

### Unit Tests (`tests/unit/`)
- Individual module testing
- Component isolation and mocking
- Function-level validation
- Error handling verification

### Integration Tests (`tests/integration/`)
- **Python ↔ Swift Integration**: Communication between backend and macOS app
- **Module Integration**: Inter-module data flow and compatibility
- **API Integration**: REST API endpoint validation
- **Database Integration**: Data persistence and retrieval

### End-to-End Tests (`tests/e2e/`)
- **Complete Workflow Testing**: Full phone recording process from start to finish
- **User Journey Validation**: Real-world usage scenarios
- **Performance Under Load**: System behavior with multiple concurrent operations
- **Error Recovery**: System resilience and graceful degradation

### Audio System Tests (`tests/audio_system/`)
- **BlackHole Integration**: Virtual audio driver detection and functionality
- **Device Management**: Audio device enumeration and configuration
- **Channel Mapping**: Speaker detection and channel-based processing
- **Audio Quality**: Signal processing and quality validation

### Web Interface Tests (`tests/web/`)
- **API Endpoint Testing**: REST API functionality and response validation
- **WebSocket Communication**: Real-time updates and bidirectional communication
- **UI Component Testing**: Frontend component behavior and interaction
- **Browser Compatibility**: Cross-browser functionality validation

## 🔧 Mock Data System

The test suite includes a comprehensive mock data generation system:

### MockAudioGenerator
- **Synthetic Audio Creation**: Generate test audio files with specific characteristics
- **Stereo Conversation Simulation**: Create realistic dual-channel conversations
- **Phone Quality Simulation**: Apply phone-line effects and compression
- **Quality Scenarios**: Generate high/low quality audio for robustness testing

### MockTranscriptGenerator
- **Transcript Generation**: Create realistic transcript data with timestamps
- **Channel-Based Transcripts**: Separate transcripts for microphone and system audio
- **Speaker Assignment**: Multi-speaker conversation simulation
- **Confidence Scoring**: Realistic confidence levels for transcript segments

## 🚀 Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock pytest-cov
pip install sounddevice soundfile scipy numpy  # Audio processing
pip install playwright  # Web interface testing

# Install the project in development mode
pip install -e ".[full]"
```

### Run All Tests
```bash
# Run complete test suite
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src/whisper_transcription_tool --cov-report=html

# Run specific test categories
pytest tests/unit/ -v              # Unit tests only
pytest tests/integration/ -v       # Integration tests only
pytest tests/e2e/ -v              # End-to-end tests only
```

### Run Tests by Component
```bash
# Phone recording module tests
pytest tests/ -k "phone" -v

# Audio system tests
pytest tests/audio_system/ -v

# Web interface tests
pytest tests/web/ -v

# Python-Swift integration tests
pytest tests/integration/test_python_swift_integration.py -v
```

### Performance and Load Testing
```bash
# Run performance benchmarks
pytest tests/ --benchmark-only

# Run with performance tracking
pytest tests/e2e/ --timeout=300 -v
```

## 🔍 Debugging and Monitoring

### Debug Dashboard
Access the comprehensive debug dashboard at: `http://localhost:8090/debug`

**Features:**
- **Real-time System Metrics**: CPU, memory, disk usage monitoring
- **Audio System Status**: BlackHole availability, device enumeration
- **WebSocket Connection Monitoring**: Live connection tracking and statistics
- **Performance Alerts**: Automatic threshold-based alerting
- **System Information**: Detailed environment and configuration data
- **Test Tools**: Built-in system testing and health checks

### Debug Mode Testing
```bash
# Run tests with debug output
pytest tests/ -v -s --log-cli-level=DEBUG

# Run with WebSocket debugging
pytest tests/e2e/ -v -s --capture=no
```

## 🏃‍♂️ Continuous Integration

### GitHub Actions
The test suite is integrated with GitHub Actions for automated testing:

- **Code Quality Checks**: Black, isort, flake8, mypy
- **Multi-Python Testing**: Python 3.9, 3.10, 3.11
- **Cross-Platform Testing**: Ubuntu, macOS
- **Integration Testing**: Mock services and API validation
- **Performance Testing**: Automated benchmarking
- **Security Scanning**: Safety and Bandit security analysis

### CI/CD Pipeline
```yaml
# Trigger: Push to main, develop, telefontest branches
# Tests: Unit → Integration → E2E → Performance → Security
# Artifacts: Coverage reports, benchmark results, security reports
```

## 📊 Test Data and Fixtures

### Audio Test Data
- **Stereo Conversations**: Realistic dual-channel phone conversations
- **Phone Recording Pairs**: Separate microphone and system audio files
- **Quality Variants**: High/low quality audio for robustness testing
- **Edge Cases**: Silent files, very short recordings, corrupted data

### Transcript Test Data
- **Channel-Based Transcripts**: Separate microphone and system transcripts
- **Speaker-Separated Content**: Multi-speaker conversation data
- **Timing Information**: Accurate timestamp and duration data
- **Confidence Scoring**: Realistic confidence levels for validation

### Configuration Test Data
- **Device Configurations**: Various audio device setups
- **Recording Settings**: Different sample rates and quality settings
- **Error Scenarios**: Invalid configurations and edge cases

## 🔧 Test Configuration

### Environment Variables
```bash
# Test configuration
export PYTEST_TIMEOUT=300              # Test timeout in seconds
export WHISPER_TEST_MODE=true          # Enable test-specific behavior
export BLACKHOLE_MOCK=true             # Mock BlackHole for CI/CD

# Audio testing
export AUDIO_TEST_SAMPLE_RATE=44100    # Test audio sample rate
export AUDIO_TEST_DURATION=10          # Test audio duration in seconds

# Web testing
export WEB_TEST_PORT=8090              # Web server test port
export WEB_TEST_HOST=localhost         # Web server test host
```

### Test Markers
```bash
# Skip slow tests
pytest tests/ -m "not slow"

# Run only audio tests
pytest tests/ -m "audio"

# Run only web tests
pytest tests/ -m "web"

# Skip tests requiring hardware
pytest tests/ -m "not hardware"
```

## 📈 Performance Testing

### Benchmarks
- **Audio Processing Speed**: Transcription performance per audio duration
- **API Response Times**: REST endpoint latency measurement
- **WebSocket Latency**: Real-time communication performance
- **Memory Usage**: Memory consumption during operations
- **Concurrent Load**: Performance under multiple simultaneous requests

### Performance Thresholds
- **API Response**: < 200ms for device queries
- **Audio Processing**: < 2x real-time for transcription
- **Memory Usage**: < 1GB for typical operations
- **WebSocket Latency**: < 100ms for status updates

## 🔄 Test Maintenance

### Adding New Tests
1. **Identify Test Category**: Unit, integration, e2e, or system
2. **Create Test File**: Follow naming convention `test_*.py`
3. **Use Appropriate Fixtures**: Leverage existing fixtures from `conftest.py`
4. **Add Test Documentation**: Include docstrings and comments
5. **Update CI/CD**: Ensure new tests are included in automation

### Mock Data Updates
1. **Update Generators**: Modify `tests/mock_data/audio_generator.py`
2. **Add Test Scenarios**: Include new edge cases and scenarios
3. **Validate Generated Data**: Ensure mock data is realistic and useful
4. **Update Documentation**: Document new mock data capabilities

## 🐛 Troubleshooting

### Common Test Issues

**BlackHole Not Found:**
```bash
# Install BlackHole or run with mock
export BLACKHOLE_MOCK=true
pytest tests/audio_system/ -v
```

**Web Server Port Conflicts:**
```bash
# Use different port
export WEB_TEST_PORT=8091
pytest tests/web/ -v
```

**Audio Library Issues:**
```bash
# Install audio dependencies
pip install sounddevice soundfile scipy
# Or run without audio hardware tests
pytest tests/ -m "not audio_hardware"
```

**Timeout Issues:**
```bash
# Increase timeout for slow systems
pytest tests/ --timeout=600 -v
```

### Debug Test Failures
```bash
# Run single test with maximum verbosity
pytest tests/specific_test.py::test_function -vvv -s

# Run with Python debugger
pytest tests/specific_test.py::test_function --pdb

# Generate detailed error reports
pytest tests/ --tb=long --maxfail=1
```

## 📚 Additional Resources

- **FastAPI Testing**: [Testing FastAPI Applications](https://fastapi.tiangolo.com/tutorial/testing/)
- **PyTest Documentation**: [PyTest Official Guide](https://docs.pytest.org/)
- **Audio Processing**: [SciPy Audio Processing](https://docs.scipy.org/doc/scipy/tutorial/io.html)
- **WebSocket Testing**: [Testing WebSocket Connections](https://websockets.readthedocs.io/en/stable/topics/testing.html)
- **Mock Data Generation**: [Faker and Factory Boy](https://faker.readthedocs.io/)

## 🤝 Contributing

When adding new features to the Phone Recording System:

1. **Write Tests First**: Follow TDD principles
2. **Include All Test Types**: Unit, integration, and e2e tests
3. **Update Mock Data**: Add relevant test scenarios
4. **Test Cross-Platform**: Ensure compatibility across systems
5. **Document Changes**: Update test documentation and README
6. **Verify CI/CD**: Ensure automated tests pass

---

This test suite ensures the Phone Recording System is robust, reliable, and ready for production use across all supported platforms and use cases.