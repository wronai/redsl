"""Python code quality analysis command for reDSL."""

from __future__ import annotations

import ast
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml

from ..analyzers import CodeAnalyzer
from ..orchestrator import RefactorOrchestrator
from ..config import AgentConfig

logger = logging.getLogger(__name__)


class PyQualAnalyzer:
    """Python code quality analyzer."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize analyzer with configuration."""
        self.config_path = config_path or Path("pyqual.yaml")
        self.config = self._load_config()
        self.results: Dict[str, Any] = {
            "project_root": str(Path.cwd()),
            "timestamp": None,
            "summary": {},
            "issues": {},
            "metrics": {},
            "recommendations": []
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_config()
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "include": ["**/*.py"],
            "exclude": ["**/__pycache__/**", "**/tests/**"],
            "tools": {
                "ruff": {"enabled": True},
                "mypy": {"enabled": True},
                "bandit": {"enabled": True}
            },
            "rules": {
                "unused-imports": {"enabled": True, "severity": "error"},
                "magic-numbers": {"enabled": True, "severity": "warning"},
                "print-statements": {"enabled": True, "severity": "warning"},
                "missing-docstrings": {"enabled": True, "severity": "warning"}
            },
            "metrics": {
                "complexity": {"enabled": True, "max_complexity": 10},
                "maintainability": {"enabled": True, "min_maintainability": 70}
            }
        }
    
    def analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Analyze entire project for code quality."""
        from datetime import datetime
        self.results["timestamp"] = datetime.now().isoformat()
        
        # Find Python files
        python_files = self._find_python_files(project_path)
        self.results["summary"]["total_files"] = len(python_files)
        
        # Run various analyses
        self._analyze_with_ruff(python_files)
        self._analyze_with_mypy(python_files)
        self._analyze_with_bandit(python_files)
        self._analyze_ast_issues(python_files)
        self._calculate_metrics(python_files)
        
        # Generate recommendations
        self._generate_recommendations()
        
        return self.results
    
    def _find_python_files(self, project_path: Path) -> List[Path]:
        """Find all Python files matching include/exclude patterns."""
        import fnmatch
        
        files = []
        include_patterns = self.config.get("include", ["**/*.py"])
        exclude_patterns = self.config.get("exclude", [])
        
        # Convert to absolute paths for proper matching
        project_path = project_path.resolve()
        
        for pattern in include_patterns:
            for file_path in project_path.glob(pattern):
                if file_path.is_file():
                    # Get relative path for matching
                    rel_path = file_path.relative_to(project_path)
                    rel_path_str = str(rel_path)
                    
                    # Check exclusions
                    excluded = False
                    for excl_pattern in exclude_patterns:
                        # Normalize pattern to handle ** properly
                        if fnmatch.fnmatch(rel_path_str, excl_pattern):
                            excluded = True
                            break
                        # Also check if any parent directory matches
                        parts = rel_path.parts
                        for i in range(len(parts)):
                            test_path = '/'.join(parts[:i+1])
                            if fnmatch.fnmatch(test_path, excl_pattern.rstrip('**')):
                                excluded = True
                                break
                    
                    if not excluded:
                        files.append(file_path)
        
        return sorted(set(files))  # Remove duplicates
    
    def _analyze_with_ruff(self, files: List[Path]) -> None:
        """Run ruff linter."""
        if not self.config.get("tools", {}).get("ruff", {}).get("enabled", False):
            return
        
        try:
            # Batch files to avoid argument list too long error
            batch_size = 100
            all_issues = []
            
            for i in range(0, len(files), batch_size):
                batch = files[i:i+batch_size]
                # Run ruff check --format=json
                result = subprocess.run(
                    ["ruff", "check", "--format=json"] + [str(f) for f in batch],
                    capture_output=True,
                    text=True
                )
                
                if result.stdout:
                    issues = json.loads(result.stdout)
                    all_issues.extend(issues)
            
            self.results["issues"]["ruff"] = all_issues
            
            # Count by severity
            error_count = sum(1 for i in all_issues if i.get("fix", {}).get("severity") == "error")
            warning_count = sum(1 for i in all_issues if i.get("fix", {}).get("severity") == "warning")
            
            self.results["summary"]["ruff_errors"] = error_count
            self.results["summary"]["ruff_warnings"] = warning_count
                
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to run ruff: {e}")
            self.results["issues"]["ruff"] = []
    
    def _analyze_with_mypy(self, files: List[Path]) -> None:
        """Run mypy type checker."""
        if not self.config.get("tools", {}).get("mypy", {}).get("enabled", False):
            return
        
        try:
            # Batch files to avoid argument list too long error
            batch_size = 100
            all_issues = []
            
            for i in range(0, len(files), batch_size):
                batch = files[i:i+batch_size]
                # Run mypy --show-error-codes --no-error-summary
                result = subprocess.run(
                    ["mypy", "--show-error-codes", "--no-error-summary"] + [str(f) for f in batch],
                    capture_output=True,
                    text=True
                )
                
                for line in result.stdout.splitlines():
                    if line.strip():
                        # Parse mypy output
                        parts = line.split(":", 3)
                        if len(parts) >= 4:
                            file_path = parts[0]
                            line_num = int(parts[1])
                            error_type = parts[2].strip()
                            message = parts[3].strip()
                            
                            all_issues.append({
                                "file": file_path,
                                "line": line_num,
                                "type": error_type,
                                "message": message
                            })
            
            self.results["issues"]["mypy"] = all_issues
            self.results["summary"]["mypy_issues"] = len(all_issues)
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Failed to run mypy: {e}")
            self.results["issues"]["mypy"] = []
    
    def _analyze_with_bandit(self, files: List[Path]) -> None:
        """Run bandit security linter."""
        if not self.config.get("tools", {}).get("bandit", {}).get("enabled", False):
            return
        
        try:
            # Group files by directory to run bandit more efficiently
            dirs_to_check = set(f.parent for f in files)
            all_issues = []
            
            for dir_path in dirs_to_check:
                # Run bandit -f json on directory
                result = subprocess.run(
                    ["bandit", "-f", "json", "-r", str(dir_path)],
                    capture_output=True,
                    text=True
                )
                
                if result.stdout:
                    bandit_result = json.loads(result.stdout)
                    dir_issues = bandit_result.get("results", [])
                    
                    # Filter to only include files we're analyzing
                    file_set = set(str(f) for f in files if f.parent == dir_path)
                    dir_issues = [i for i in dir_issues if i.get("filename") in file_set]
                    all_issues.extend(dir_issues)
            
            self.results["issues"]["bandit"] = all_issues
            self.results["summary"]["security_issues"] = len(all_issues)
                
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to run bandit: {e}")
            self.results["issues"]["bandit"] = []
    
    def _analyze_ast_issues(self, files: List[Path]) -> None:
        """Analyze AST for custom rules."""
        ast_issues = []
        unused_imports = []
        magic_numbers = []
        print_statements = []
        missing_docstrings = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(file_path))
                
                # Use reDSL's quality visitor
                from ..analyzers.quality_visitor import CodeQualityVisitor
                visitor = CodeQualityVisitor()
                visitor.visit(tree)
                
                # Collect issues
                unused_imports_list = visitor.get_unused_imports()
                for imp_name in unused_imports_list:
                    unused_imports.append({
                        "file": str(file_path),
                        "line": visitor.imports[imp_name].lineno,
                        "name": imp_name,
                        "message": f"Unused import: {imp_name}"
                    })
                
                for lineno, value in visitor.magic_numbers:
                    magic_numbers.append({
                        "file": str(file_path),
                        "line": lineno,
                        "value": value,
                        "message": f"Magic number: {value}"
                    })
                
                for lineno, stmt_type in visitor.module_level_statements:
                    print_statements.append({
                        "file": str(file_path),
                        "line": lineno,
                        "message": f"Module execution block detected: {stmt_type}"
                    })
                
                # Check for missing docstrings
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                        if not ast.get_docstring(node):
                            missing_docstrings.append({
                                "file": str(file_path),
                                "line": node.lineno,
                                "type": type(node).__name__,
                                "name": getattr(node, 'name', 'module'),
                                "message": f"Missing docstring for {type(node).__name__}"
                            })
                
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        self.results["issues"]["unused_imports"] = unused_imports
        self.results["issues"]["magic_numbers"] = magic_numbers
        self.results["issues"]["print_statements"] = print_statements
        self.results["issues"]["missing_docstrings"] = missing_docstrings
        
        self.results["summary"]["unused_imports"] = len(unused_imports)
        self.results["summary"]["magic_numbers"] = len(magic_numbers)
        self.results["summary"]["print_statements"] = len(print_statements)
        self.results["summary"]["missing_docstrings"] = len(missing_docstrings)
    
    def _calculate_metrics(self, files: List[Path]) -> None:
        """Calculate code metrics."""
        try:
            import radon.complexity as rc
            from radon.complexity import cc_visit
            import radon.metrics as rm
            from radon.metrics import mi_visit
        except ImportError:
            logger.warning("Radon not installed, skipping complexity and maintainability metrics")
            self.results["metrics"]["total_lines"] = 0
            self.results["metrics"]["average_complexity"] = 0
            self.results["metrics"]["max_complexity"] = 0
            self.results["metrics"]["average_maintainability"] = 0
            return
        
        total_lines = 0
        total_complexity = 0
        complexities = []
        maintainability_scores = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Line count
                lines = len(content.splitlines())
                total_lines += lines
                
                # Complexity
                try:
                    cc = cc_visit(content)
                    total_complexity += cc.total_complexity
                    complexities.append(cc.total_complexity)
                except Exception as e:
                    logger.debug(f"Failed to calculate complexity for {file_path}: {e}")
                
                # Maintainability
                try:
                    mi = mi_visit(content, multi=True)
                    maintainability_scores.append(mi)
                except Exception as e:
                    logger.debug(f"Failed to calculate maintainability for {file_path}: {e}")
                    
            except Exception as e:
                logger.warning(f"Failed to calculate metrics for {file_path}: {e}")
        
        self.results["metrics"]["total_lines"] = total_lines
        self.results["metrics"]["average_complexity"] = total_complexity / len(files) if files else 0
        self.results["metrics"]["max_complexity"] = max(complexities) if complexities else 0
        self.results["metrics"]["average_maintainability"] = sum(maintainability_scores) / len(maintainability_scores) if maintainability_scores else 0
        
        # Check against thresholds
        max_complexity = self.config.get("metrics", {}).get("complexity", {}).get("max_complexity", 10)
        min_maintainability = self.config.get("metrics", {}).get("maintainability", {}).get("min_maintainability", 70)
        
        self.results["summary"]["complexity_violations"] = sum(1 for c in complexities if c > max_complexity)
        self.results["summary"]["maintainability_violations"] = sum(1 for m in maintainability_scores if m < min_maintainability)
    
    def _generate_recommendations(self) -> None:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Based on issues found
        if self.results["summary"].get("unused_imports", 0) > 0:
            recommendations.append({
                "type": "cleanup",
                "priority": "high",
                "message": f"Remove {self.results['summary']['unused_imports']} unused imports",
                "action": "REMOVE_UNUSED_IMPORTS"
            })
        
        if self.results["summary"].get("magic_numbers", 0) > 0:
            recommendations.append({
                "type": "quality",
                "priority": "medium",
                "message": f"Extract {self.results['summary']['magic_numbers']} magic numbers to constants",
                "action": "EXTRACT_CONSTANTS"
            })
        
        if self.results["summary"].get("print_statements", 0) > 0:
            recommendations.append({
                "type": "quality",
                "priority": "medium",
                "message": f"Remove or replace {self.results['summary']['print_statements']} print statements",
                "action": "FIX_MODULE_EXECUTION_BLOCK"
            })
        
        if self.results["summary"].get("missing_docstrings", 0) > 0:
            recommendations.append({
                "type": "documentation",
                "priority": "low",
                "message": f"Add docstrings to {self.results['summary']['missing_docstrings']} functions/classes",
                "action": None
            })
        
        if self.results["summary"].get("complexity_violations", 0) > 0:
            recommendations.append({
                "type": "refactoring",
                "priority": "high",
                "message": f"Reduce complexity in {self.results['summary']['complexity_violations']} functions",
                "action": None
            })
        
        if self.results["summary"].get("security_issues", 0) > 0:
            recommendations.append({
                "type": "security",
                "priority": "critical",
                "message": f"Fix {self.results['summary']['security_issues']} security issues",
                "action": None
            })
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 4))
        
        self.results["recommendations"] = recommendations
    
    def save_report(self, output_path: Path, format: str = "yaml") -> None:
        """Save analysis report."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "yaml":
            with open(output_path, 'w') as f:
                yaml.dump(self.results, f, default_flow_style=False, indent=2)
        elif format == "json":
            with open(output_path, 'w') as f:
                json.dump(self.results, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Report saved to {output_path}")


def run_pyqual_analysis(project_path: Path, config_path: Optional[Path] = None, 
                       output_format: str = "yaml") -> Dict[str, Any]:
    """Run pyqual analysis on a project."""
    analyzer = PyQualAnalyzer(config_path)
    results = analyzer.analyze_project(project_path)
    
    # Save report
    output_file = project_path / f"pyqual_report.{output_format}"
    analyzer.save_report(output_file, output_format)
    
    # Print summary
    print(f"\n{'='*60}")
    print("PYQUAL CODE QUALITY REPORT")
    print(f"{'='*60}")
    print(f"Project: {project_path.name}")
    print(f"Files analyzed: {results['summary']['total_files']}")
    print(f"\nIssues found:")
    print(f"  - Unused imports: {results['summary'].get('unused_imports', 0)}")
    print(f"  - Magic numbers: {results['summary'].get('magic_numbers', 0)}")
    print(f"  - Print statements: {results['summary'].get('print_statements', 0)}")
    print(f"  - Missing docstrings: {results['summary'].get('missing_docstrings', 0)}")
    print(f"  - Type issues (mypy): {results['summary'].get('mypy_issues', 0)}")
    print(f"  - Style issues (ruff): {results['summary'].get('ruff_errors', 0)} errors, {results['summary'].get('ruff_warnings', 0)} warnings")
    print(f"  - Security issues: {results['summary'].get('security_issues', 0)}")
    print(f"\nMetrics:")
    print(f"  - Average complexity: {results['metrics'].get('average_complexity', 0):.1f}")
    print(f"  - Max complexity: {results['metrics'].get('max_complexity', 0)}")
    print(f"  - Average maintainability: {results['metrics'].get('average_maintainability', 0):.1f}")
    print(f"\nTop recommendations:")
    for rec in results['recommendations'][:5]:
        print(f"  - [{rec['priority'].upper()}] {rec['message']}")
    
    print(f"\nFull report saved to: {output_file}")
    
    return results


def run_pyqual_fix(project_path: Path, config_path: Optional[Path] = None) -> None:
    """Run automatic fixes based on pyqual analysis."""
    # First run analysis
    pyqual_analyzer = PyQualAnalyzer(config_path)
    results = pyqual_analyzer.analyze_project(project_path)
    
    # Get fixable recommendations
    fixable_actions = [r["action"] for r in results["recommendations"] if r.get("action")]
    
    if not fixable_actions:
        print("No automatic fixes available.")
        return
    
    print(f"\nApplying automatic fixes...")
    
    # Use reDSL orchestrator for direct refactoring
    config = AgentConfig()
    config.refactor.apply_changes = True
    config.refactor.reflection_rounds = 0
    
    orchestrator = RefactorOrchestrator(config)
    code_analyzer = CodeAnalyzer()
    
    # Get decisions for fixable actions
    analysis = code_analyzer.analyze_project(project_path)
    contexts = analysis.to_dsl_contexts()
    all_decisions = orchestrator.dsl_engine.evaluate(contexts)
    
    # Filter for fixable actions
    from ..dsl import RefactorAction
    action_map = {
        "REMOVE_UNUSED_IMPORTS": RefactorAction.REMOVE_UNUSED_IMPORTS,
        "EXTRACT_CONSTANTS": RefactorAction.EXTRACT_CONSTANTS,
        "FIX_MODULE_EXECUTION_BLOCK": RefactorAction.FIX_MODULE_EXECUTION_BLOCK,
        "ADD_RETURN_TYPES": RefactorAction.ADD_RETURN_TYPES,
    }
    
    fixable_decisions = []
    for action_str in fixable_actions:
        if action_str in action_map:
            action = action_map[action_str]
            fixable_decisions.extend([d for d in all_decisions if d.action == action])
    
    # Apply fixes
    total_applied = 0
    for decision in fixable_decisions:
        result = orchestrator._execute_direct_refactor(decision, project_path)
        if result.applied:
            total_applied += 1
    
    print(f"Applied {total_applied} automatic fixes.")
    
    # Re-run analysis to show improvement
    print("\nRe-running analysis...")
    new_results = pyqual_analyzer.analyze_project(project_path)
    
    # Compare results
    print(f"\nImprovement:")
    print(f"  - Unused imports: {results['summary'].get('unused_imports', 0)} → {new_results['summary'].get('unused_imports', 0)}")
    print(f"  - Magic numbers: {results['summary'].get('magic_numbers', 0)} → {new_results['summary'].get('magic_numbers', 0)}")
    print(f"  - Print statements: {results['summary'].get('print_statements', 0)} → {new_results['summary'].get('print_statements', 0)}")
