"""
Collection Test Runner

Runs tests for all requests in a collection.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QTextEdit, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, List

from src.core.database import DatabaseManager
from src.core.api_client import ApiClient
from src.features.test_engine import TestEngine, TestAssertion
from src.features.variable_substitution import EnvironmentManager


class CollectionTestThread(QThread):
    """Thread for running collection tests."""
    
    progress = pyqtSignal(int, int, str)  # current, total, message
    test_completed = pyqtSignal(dict)  # test result
    finished_all = pyqtSignal(dict)  # summary
    
    def __init__(self, db_path: str, api_client: ApiClient,
                 collection_id: int, env_manager: EnvironmentManager = None):
        super().__init__()
        self.db_path = db_path
        self.api_client = api_client
        self.collection_id = collection_id
        self.env_manager = env_manager
        self._stop_requested = False
    
    def run(self):
        """Run tests for all requests in the collection."""
        try:
            # Create a new database connection for this thread
            db = DatabaseManager(self.db_path)
            
            # Get all requests in collection
            requests = db.get_requests_by_collection(self.collection_id)
            total = len(requests)
            
            if total == 0:
                self.finished_all.emit({
                    'total_requests': 0,
                    'total_tests': 0,
                    'passed': 0,
                    'failed': 0
                })
                return
            
            results = []
            total_tests = 0
            total_passed = 0
            total_failed = 0
            
            for idx, request in enumerate(requests, 1):
                if self._stop_requested:
                    break
                
                request_name = request['name']
                self.progress.emit(idx, total, f"Testing: {request_name}")
                
                # Get assertions for this request
                assertions = db.get_test_assertions(request['id'])
                if not assertions:
                    continue
                
                # Execute request
                try:
                    # Apply environment variable substitution if active
                    url = request['url']
                    params = request.get('params', {})
                    headers = request.get('headers', {})
                    body = request.get('body')
                    auth_token = request.get('auth_token', '')
                    
                    if self.env_manager and self.env_manager.has_active_environment():
                        substituted, _ = self.env_manager.substitute_in_request(
                            url, params, headers, body, auth_token
                        )
                        url = substituted['url']
                        params = substituted['params']
                        headers = substituted['headers']
                        body = substituted['body']
                        auth_token = substituted['auth_token']
                    
                    response = self.api_client.execute(
                        method=request['method'],
                        url=url,
                        params=params,
                        headers=headers,
                        body=body,
                        auth_type=request.get('auth_type', 'None'),
                        auth_token=auth_token
                    )
                    
                    # Convert assertions to TestAssertion objects
                    test_assertions = []
                    for a in assertions:
                        if a.get('enabled', True):
                            test_assertions.append(TestAssertion(
                                assertion_id=a['id'],
                                assertion_type=a['assertion_type'],
                                operator=a['operator'],
                                field=a.get('field'),
                                expected_value=a.get('expected_value'),
                                enabled=a.get('enabled', True)
                            ))
                    
                    # Run tests
                    test_results = TestEngine.evaluate_all(test_assertions, response)
                    
                    # Count results
                    for result in test_results:
                        total_tests += 1
                        if result.passed:
                            total_passed += 1
                        else:
                            total_failed += 1
                    
                    # Store results
                    results.append({
                        'request_id': request['id'],
                        'request_name': request_name,
                        'results': test_results,
                        'success': True
                    })
                    
                    self.test_completed.emit({
                        'request_name': request_name,
                        'test_count': len(test_results),
                        'passed': sum(1 for r in test_results if r.passed),
                        'failed': sum(1 for r in test_results if not r.passed)
                    })
                
                except Exception as e:
                    results.append({
                        'request_id': request['id'],
                        'request_name': request_name,
                        'error': str(e),
                        'success': False
                    })
                    
                    self.test_completed.emit({
                        'request_name': request_name,
                        'error': str(e)
                    })
            
            # Send summary
            self.finished_all.emit({
                'total_requests': len(results),
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'results': results
            })
        
        except Exception as e:
            self.finished_all.emit({
                'error': str(e)
            })
    
    def stop(self):
        """Request to stop test execution."""
        self._stop_requested = True


class CollectionTestRunnerDialog(QDialog):
    """Dialog for running tests on a collection."""
    
    def __init__(self, db: DatabaseManager, api_client: ApiClient,
                 collection_id: int, collection_name: str,
                 env_manager: EnvironmentManager = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.api_client = api_client
        self.collection_id = collection_id
        self.collection_name = collection_name
        self.env_manager = env_manager
        self.test_thread = None
        
        self.setWindowTitle(f"Test Runner: {collection_name}")
        self.setGeometry(200, 200, 700, 500)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(f"Running Tests: {self.collection_name}")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_label = QLabel("Ready to start...")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Results log
        log_group = QGroupBox("Test Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 9))
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Summary
        self.summary_label = QLabel("")
        self.summary_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.run_btn = QPushButton("▶️ Run Tests")
        self.run_btn.clicked.connect(self._run_tests)
        self.run_btn.setProperty("class", "primary")
        button_layout.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self._stop_tests)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def _run_tests(self):
        """Start running tests."""
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.close_btn.setEnabled(False)
        
        self.log_text.clear()
        self.summary_label.clear()
        self.progress_bar.setValue(0)
        
        self._log("Starting test run...\n")
        
        # Create and start thread
        # Pass database path instead of database object for thread safety
        self.test_thread = CollectionTestThread(
            self.db.db_path, self.api_client, self.collection_id, self.env_manager
        )
        self.test_thread.progress.connect(self._on_progress)
        self.test_thread.test_completed.connect(self._on_test_completed)
        self.test_thread.finished_all.connect(self._on_finished)
        self.test_thread.start()
    
    def _stop_tests(self):
        """Stop test execution."""
        if self.test_thread:
            self._log("\nStopping tests...\n")
            self.test_thread.stop()
    
    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress update."""
        self.progress_label.setText(f"{current}/{total}: {message}")
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
    
    def _on_test_completed(self, result: Dict):
        """Handle individual test completion."""
        request_name = result.get('request_name', 'Unknown')
        
        if 'error' in result:
            self._log(f"  ❌ {request_name}: ERROR - {result['error']}\n")
        else:
            test_count = result.get('test_count', 0)
            passed = result.get('passed', 0)
            failed = result.get('failed', 0)
            
            if failed == 0:
                self._log(f"  ✅ {request_name}: {passed}/{test_count} tests passed\n")
            else:
                self._log(f"  ⚠️  {request_name}: {passed}/{test_count} passed, {failed} failed\n")
    
    def _on_finished(self, summary: Dict):
        """Handle test run completion."""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
        
        if 'error' in summary:
            self._log(f"\n❌ Test run failed: {summary['error']}\n")
            self.summary_label.setText("Test run failed!")
            self.summary_label.setProperty("class", "error-text")
            self.summary_label.style().unpolish(self.summary_label)
            self.summary_label.style().polish(self.summary_label)
            return
        
        total_requests = summary.get('total_requests', 0)
        total_tests = summary.get('total_tests', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        
        self._log(f"\n{'='*50}\n")
        self._log(f"Test Run Complete!\n")
        self._log(f"Requests tested: {total_requests}\n")
        self._log(f"Total assertions: {total_tests}\n")
        self._log(f"✓ Passed: {passed}\n")
        self._log(f"✗ Failed: {failed}\n")
        
        if failed == 0:
            self._log(f"✅ All tests passed!\n")
            self.summary_label.setText(
                f"✅ Success! {passed}/{total_tests} tests passed across {total_requests} requests"
            )
            self.summary_label.setProperty("class", "success-text")
            self.summary_label.style().unpolish(self.summary_label)
            self.summary_label.style().polish(self.summary_label)
        else:
            pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0
            self._log(f"⚠️  {failed} tests failed (Pass rate: {pass_rate:.1f}%)\n")
            self.summary_label.setText(
                f"⚠️  {passed}/{total_tests} passed, {failed} failed (Pass rate: {pass_rate:.1f}%)"
            )
            self.summary_label.setProperty("class", "warning-text")
            self.summary_label.style().unpolish(self.summary_label)
            self.summary_label.style().polish(self.summary_label)
    
    def _log(self, message: str):
        """Add message to log."""
        self.log_text.append(message.rstrip())
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def closeEvent(self, event):
        """Handle dialog close event - clean up test thread."""
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.stop()
            self.test_thread.wait(2000)  # Wait up to 2 seconds
        event.accept()

