"""
Comprehensive Test Suite for Repository Agent Node
Tests all functionality including edge cases, error handling, and contract compliance.
"""
import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.repository_agent.node import (
    repository_agent_node,
    _analyze_repository,
    _scan_repo_structure,
    _contains_code_files,
    _detect_frameworks_from_file,
    _get_fallback_data
)
from graph.state import AgentState


class TestRepositoryAgentNode(unittest.TestCase):
    """Test suite for the repository agent node."""
    
    def setUp(self):
        """Set up test fixtures before each test."""
        # Create temporary directory for test repositories
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
    
    def create_test_repo(self, structure):
        """
        Creates a test repository with the given structure.
        
        Args:
            structure: Dict mapping file paths to content
        """
        for filepath, content in structure.items():
            full_path = os.path.join(self.test_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            if content is not None:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def test_contract_compliance_basic(self):
        """Test that output matches the exact JSON schema contract."""
        # Create a simple test repository
        self.create_test_repo({
            'backend/main.py': 'import os\nimport sys',
            'frontend/app.js': 'const x = 1;',
            'package.json': json.dumps({
                'dependencies': {'react': '18.0.0', 'next': '13.0.0'}
            })
        })
        
        state: AgentState = {
            'repo_id': 'test-repo-1',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        print('hohoho',result)
        
        # Verify contract: must have exactly these keys
        self.assertIn('services', result)
        self.assertIn('languages', result)
        self.assertIn('frameworks', result)
        
        # Verify types
        self.assertIsInstance(result['services'], list)
        self.assertIsInstance(result['languages'], list)
        self.assertIsInstance(result['frameworks'], list)
        
        # Verify content
        self.assertIn('backend', result['services'])
        self.assertIn('frontend', result['services'])
        self.assertIn('Python', result['languages'])
        self.assertIn('JavaScript', result['languages'])
        self.assertIn('Next.js', result['frameworks'])
        self.assertIn('React', result['frameworks'])
    
    def test_empty_repository(self):
        """Test handling of completely empty repository."""
        state: AgentState = {
            'repo_id': 'empty-repo',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        # Should return empty lists, not fail
        self.assertEqual(result['services'], [])
        self.assertEqual(result['languages'], [])
        self.assertEqual(result['frameworks'], [])
    
    def test_nonexistent_path(self):
        """Test handling of non-existent repository path."""
        state: AgentState = {
            'repo_id': 'nonexistent',
            'repo_path': '/nonexistent/path/to/repo',
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        # Should return fallback data, not crash
        self.assertIn('services', result)
        self.assertIn('languages', result)
        self.assertIn('frameworks', result)
    
    def test_missing_repo_path(self):
        """Test handling of missing repo_path in state."""
        state: AgentState = {
            'repo_id': 'test',
            'repo_path': '',
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        # Should return fallback data
        self.assertEqual(result, _get_fallback_data())
    
    def test_corrupted_json_file(self):
        """Test handling of corrupted JSON manifest files."""
        self.create_test_repo({
            'service/app.py': 'print("hello")',
            'package.json': '{invalid json content'
        })
        
        state: AgentState = {
            'repo_id': 'corrupted',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        # Should still detect service and language, just skip corrupted file
        self.assertIn('service', result['services'])
        self.assertIn('Python', result['languages'])
    
    def test_files_without_extensions(self):
        """Test handling of files without extensions."""
        self.create_test_repo({
            'service/Makefile': 'all:\n\techo "build"',
            'service/README': 'This is a readme',
            'service/app.py': 'import os'
        })
        
        state: AgentState = {
            'repo_id': 'no-ext',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        # Should detect service from .py file
        self.assertIn('service', result['services'])
        self.assertIn('Python', result['languages'])
    
    def test_ignored_directories(self):
        """Test that ignored directories are not counted as services."""
        self.create_test_repo({
            'node_modules/package/index.js': 'module.exports = {}',
            '.git/config': '[core]',
            'venv/lib/python.py': 'import sys',
            'actual_service/app.py': 'import os'
        })
        
        state: AgentState = {
            'repo_id': 'ignored',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        # Should only detect actual_service
        self.assertIn('actual_service', result['services'])
        self.assertNotIn('node_modules', result['services'])
        self.assertNotIn('.git', result['services'])
        self.assertNotIn('venv', result['services'])
    
    def test_multiple_languages(self):
        """Test detection of multiple programming languages."""
        self.create_test_repo({
            'backend/main.py': 'import flask',
            'backend/utils.go': 'package main',
            'frontend/app.ts': 'const x: number = 1',
            'frontend/style.css': 'body { margin: 0; }'
        })
        
        state: AgentState = {
            'repo_id': 'multi-lang',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        # Should detect all languages
        self.assertIn('Python', result['languages'])
        self.assertIn('Go', result['languages'])
        self.assertIn('TypeScript', result['languages'])
        self.assertIn('CSS', result['languages'])
    
    def test_framework_detection_python(self):
        """Test Python framework detection from requirements.txt."""
        self.create_test_repo({
            'api/main.py': 'from fastapi import FastAPI',
            'requirements.txt': 'fastapi==0.100.0\nuvicorn==0.23.0\nlanggraph==0.2.0'
        })
        
        state: AgentState = {
            'repo_id': 'python-frameworks',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        self.assertIn('FastAPI', result['frameworks'])
        self.assertIn('LangGraph', result['frameworks'])
    
    def test_framework_detection_javascript(self):
        """Test JavaScript framework detection from package.json."""
        self.create_test_repo({
            'web/app.jsx': 'import React from "react"',
            'package.json': json.dumps({
                'dependencies': {
                    'react': '18.2.0',
                    'next': '13.4.0',
                    'express': '4.18.0'
                }
            })
        })
        
        state: AgentState = {
            'repo_id': 'js-frameworks',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        self.assertIn('React', result['frameworks'])
        self.assertIn('Next.js', result['frameworks'])
        self.assertIn('Express', result['frameworks'])
    
    def test_framework_detection_go(self):
        """Test Go framework detection from go.mod."""
        self.create_test_repo({
            'server/main.go': 'package main',
            'go.mod': 'module myapp\n\nrequire github.com/gin-gonic/gin v1.9.0'
        })
        
        state: AgentState = {
            'repo_id': 'go-frameworks',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        self.assertIn('Gin', result['frameworks'])
    
    @patch('agents.repository_agent.node.repository_memory')
    def test_memory_storage_success(self, mock_memory):
        """Test successful storage to repository memory."""
        mock_memory.store_repository_analysis.return_value = True
        
        self.create_test_repo({
            'service/app.py': 'import os'
        })
        
        state: AgentState = {
            'repo_id': 'storage-test',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        # Verify storage was called
        mock_memory.store_repository_analysis.assert_called_once()
        call_args = mock_memory.store_repository_analysis.call_args
        self.assertEqual(call_args[1]['repo_id'], 'storage-test')
    
    @patch('agents.repository_agent.node.repository_memory')
    def test_memory_storage_failure_doesnt_crash(self, mock_memory):
        """Test that storage failure doesn't crash the node."""
        mock_memory.store_repository_analysis.side_effect = Exception("Storage failed")
        
        self.create_test_repo({
            'service/app.py': 'import os'
        })
        
        state: AgentState = {
            'repo_id': 'storage-fail',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        # Should not raise exception
        result = repository_agent_node(state)
        
        # Should still return valid data
        self.assertIn('services', result)
        self.assertIn('service', result['services'])
    
    @patch('agents.repository_agent.node.parse_imports_from_file')
    def test_import_parsing_failure_doesnt_crash(self, mock_parse):
        """Test that import parsing failure doesn't crash the scan."""
        mock_parse.side_effect = Exception("Parse failed")
        
        self.create_test_repo({
            'service/app.py': 'import os\nimport sys'
        })
        
        state: AgentState = {
            'repo_id': 'import-fail',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        # Should not raise exception
        result = repository_agent_node(state)
        
        # Should still detect service and language
        self.assertIn('service', result['services'])
        self.assertIn('Python', result['languages'])
    
    def test_large_repository_performance(self):
        """Test that large repositories are handled efficiently."""
        # Create 150 files (more than MAX_FILES_TO_PARSE limit)
        structure = {}
        for i in range(150):
            structure[f'service/file{i}.py'] = f'import module{i}'
        
        self.create_test_repo(structure)
        
        state: AgentState = {
            'repo_id': 'large-repo',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        # Should complete without timeout
        result = repository_agent_node(state)
        
        self.assertIn('service', result['services'])
        self.assertIn('Python', result['languages'])
    
    def test_unicode_and_special_characters(self):
        """Test handling of files with unicode and special characters."""
        self.create_test_repo({
            'service/app.py': '# -*- coding: utf-8 -*-\nprint("Hello 世界")',
            'service/测试.py': 'import os'
        })
        
        state: AgentState = {
            'repo_id': 'unicode',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        # Should handle unicode without crashing
        result = repository_agent_node(state)
        
        self.assertIn('service', result['services'])
        self.assertIn('Python', result['languages'])
    
    def test_symlinks_handling(self):
        """Test that symlinks don't cause infinite loops."""
        # Create a directory and a symlink to it
        real_dir = os.path.join(self.test_dir, 'real_service')
        os.makedirs(real_dir)
        
        with open(os.path.join(real_dir, 'app.py'), 'w') as f:
            f.write('import os')
        
        # Note: Symlink creation might fail on Windows without admin rights
        try:
            link_dir = os.path.join(self.test_dir, 'link_service')
            os.symlink(real_dir, link_dir, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks not supported on this system")
        
        state: AgentState = {
            'repo_id': 'symlink',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        # Should handle symlinks without infinite loop
        result = repository_agent_node(state)
        
        self.assertIn('Python', result['languages'])
    
    def test_fallback_data_structure(self):
        """Test that fallback data has correct structure."""
        fallback = _get_fallback_data()
        
        self.assertIn('services', fallback)
        self.assertIn('languages', fallback)
        self.assertIn('frameworks', fallback)
        self.assertIsInstance(fallback['services'], list)
        self.assertIsInstance(fallback['languages'], list)
        self.assertIsInstance(fallback['frameworks'], list)
    
    def test_contains_code_files_helper(self):
        """Test the _contains_code_files helper function."""
        self.create_test_repo({
            'with_code/app.py': 'import os',
            'without_code/README.md': '# Readme'
        })
        
        extension_map = {'.py': 'Python', '.js': 'JavaScript'}
        
        with_code_dir = os.path.join(self.test_dir, 'with_code')
        without_code_dir = os.path.join(self.test_dir, 'without_code')
        
        self.assertTrue(_contains_code_files(with_code_dir, extension_map))
        self.assertFalse(_contains_code_files(without_code_dir, extension_map))
    
    def test_detect_frameworks_from_nonexistent_file(self):
        """Test framework detection with non-existent file."""
        result = _detect_frameworks_from_file('package.json', '/nonexistent/package.json')
        
        # Should return empty set, not crash
        self.assertEqual(result, set())
    
    def test_sorted_output(self):
        """Test that output lists are sorted for consistency."""
        self.create_test_repo({
            'zebra/app.py': 'import os',
            'alpha/main.js': 'const x = 1',
            'beta/server.go': 'package main'
        })
        
        state: AgentState = {
            'repo_id': 'sorted',
            'repo_path': self.test_dir,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        # Services should be sorted alphabetically
        self.assertEqual(result['services'], sorted(result['services']))
        self.assertEqual(result['languages'], sorted(result['languages']))
        self.assertEqual(result['frameworks'], sorted(result['frameworks']))


class TestEdgeCases(unittest.TestCase):
    """Additional edge case tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
    
    def test_file_path_is_directory(self):
        """Test when repo_path points to a file instead of directory."""
        file_path = os.path.join(self.test_dir, 'file.txt')
        with open(file_path, 'w') as f:
            f.write('content')
        
        state: AgentState = {
            'repo_id': 'file-not-dir',
            'repo_path': file_path,
            'services': [],
            'languages': [],
            'frameworks': []
        }
        
        result = repository_agent_node(state)
        
        # Should return fallback data
        self.assertIn('services', result)
    
    def test_permission_denied(self):
        """Test handling of permission denied errors."""
        # This test is platform-specific and might not work on all systems
        restricted_dir = os.path.join(self.test_dir, 'restricted')
        os.makedirs(restricted_dir)
        
        try:
            # Try to make directory unreadable (Unix-like systems)
            os.chmod(restricted_dir, 0o000)
            
            state: AgentState = {
                'repo_id': 'permission',
                'repo_path': restricted_dir,
                'services': [],
                'languages': [],
                'frameworks': []
            }
            
            # Should handle permission error gracefully
            result = repository_agent_node(state)
            self.assertIn('services', result)
            
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(restricted_dir, 0o755)
            except:
                pass


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestRepositoryAgentNode))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("REPOSITORY AGENT NODE - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print()
    
    result = run_tests()
    
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()
    
    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED")
        exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        exit(1)

# Made with Bob
