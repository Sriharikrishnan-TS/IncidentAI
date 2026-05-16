## Repository Agent Test Suite

### Overview
Comprehensive test suite for the Repository Agent Node with 25+ test cases covering:
- ✅ Contract compliance validation
- ✅ Edge case handling (empty repos, corrupted files, missing paths)
- ✅ Error recovery and fallback mechanisms
- ✅ Multi-language and framework detection
- ✅ Memory storage integration
- ✅ Performance with large repositories

### Quick Start

#### Run All Tests
```bash
# From the ai-engine directory
python test_runner.py
```

#### Run Specific Test Class
```bash
# From the ai-engine directory
python -m unittest tests.test_repository_agent.TestRepositoryAgentNode
```

#### Run Single Test
```bash
# From the ai-engine directory
python -m unittest tests.test_repository_agent.TestRepositoryAgentNode.test_contract_compliance_basic
```

### Test Coverage

#### Contract Compliance Tests
- `test_contract_compliance_basic` - Validates exact JSON schema (repo_id, services, languages, frameworks)
- `test_sorted_output` - Ensures consistent alphabetical ordering

#### Edge Case Tests
- `test_empty_repository` - Handles completely empty directories
- `test_nonexistent_path` - Handles non-existent paths gracefully
- `test_missing_repo_path` - Handles missing repo_path in state
- `test_corrupted_json_file` - Handles corrupted manifest files
- `test_files_without_extensions` - Handles files without extensions
- `test_unicode_and_special_characters` - Handles unicode filenames and content

#### Error Recovery Tests
- `test_memory_storage_failure_doesnt_crash` - Storage failures don't crash node
- `test_import_parsing_failure_doesnt_crash` - Import parsing failures don't crash scan
- `test_permission_denied` - Handles permission errors gracefully

#### Detection Tests
- `test_ignored_directories` - Correctly ignores .git, node_modules, venv, etc.
- `test_multiple_languages` - Detects Python, Go, TypeScript, CSS, etc.
- `test_framework_detection_python` - Detects FastAPI, Django, Flask, LangGraph
- `test_framework_detection_javascript` - Detects React, Next.js, Express
- `test_framework_detection_go` - Detects Gin, Echo, Fiber

#### Integration Tests
- `test_memory_storage_success` - Validates storage integration
- `test_large_repository_performance` - Tests with 150+ files
- `test_symlinks_handling` - Prevents infinite loops with symlinks

### Expected Output

#### Success
```
======================================================================
REPOSITORY AGENT NODE - COMPREHENSIVE TEST SUITE
======================================================================

test_contract_compliance_basic ... ok
test_empty_repository ... ok
test_nonexistent_path ... ok
...
----------------------------------------------------------------------
Ran 25 tests in 2.345s

OK

======================================================================
TEST SUMMARY
======================================================================
Tests run: 25
Successes: 25
Failures: 0
Errors: 0

✓ ALL TESTS PASSED
```

#### Failure
```
======================================================================
REPOSITORY AGENT NODE - COMPREHENSIVE TEST SUITE
======================================================================

test_contract_compliance_basic ... FAIL
...
----------------------------------------------------------------------
Ran 25 tests in 2.345s

FAILED (failures=1)

======================================================================
TEST SUMMARY
======================================================================
Tests run: 25
Successes: 24
Failures: 1
Errors: 0

✗ SOME TESTS FAILED
```

### Test Architecture

#### Mock Strategy
- **Database**: Uses `unittest.mock.patch` to mock repository_memory
- **Import Parser**: Mocks parse_imports_from_file for failure scenarios
- **File System**: Creates temporary directories with `tempfile.mkdtemp`

#### Fixture Creation
Tests use `create_test_repo()` helper to programmatically create file structures:
```python
self.create_test_repo({
    'backend/main.py': 'import os',
    'frontend/app.js': 'const x = 1;',
    'package.json': json.dumps({'dependencies': {'react': '18.0.0'}})
})
```

### Continuous Integration

Add to your CI/CD pipeline:
```yaml
# .github/workflows/test.yml
- name: Run Repository Agent Tests
  run: |
    cd ai-engine
    python test_runner.py
```

### Troubleshooting

#### Import Errors
If you see import errors, ensure you're running from the `ai-engine` directory:
```bash
cd ai-engine
python test_runner.py
```

#### Permission Errors
Some tests (like `test_permission_denied`) may be skipped on Windows or systems without proper permissions. This is expected behavior.

#### Symlink Tests
Symlink tests may be skipped on Windows without administrator privileges. This is expected behavior.

### Adding New Tests

1. Add test method to `TestRepositoryAgentNode` class
2. Use `self.create_test_repo()` to create fixtures
3. Call `repository_agent_node()` with test state
4. Assert expected behavior

Example:
```python
def test_new_feature(self):
    """Test description."""
    self.create_test_repo({
        'service/app.py': 'import new_module'
    })
    
    state: AgentState = {
        'repo_id': 'test',
        'repo_path': self.test_dir,
        'services': [],
        'languages': [],
        'frameworks': []
    }
    
    result = repository_agent_node(state)
    
    self.assertIn('expected_value', result['services'])
```

### Performance Benchmarks

- Empty repository: < 0.01s
- Small repository (10 files): < 0.1s
- Medium repository (100 files): < 0.5s
- Large repository (150+ files): < 1.0s

All tests complete in under 3 seconds total.