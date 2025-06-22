# Code Quality & Pylint Integration

## Overview

The Bitaxe Monitor project now includes comprehensive code quality checks using Pylint and other tools. This ensures consistent code style, identifies potential issues, and maintains high code quality standards.

## 🚀 Quick Start

### Run Quality Checks Locally
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all quality checks
python scripts/run_pylint.py

# Run individual tools
pylint src/ --rcfile=.pylintrc
black --check .
isort --check-only .
bandit -r src/
```

## 🔧 GitHub Actions Integration

### Automated Quality Checks

**Workflow Files:**
- `.github/workflows/quality.yml` - Comprehensive quality and testing pipeline
- `.github/workflows/pylint.yml` - Dedicated pylint analysis with reporting

**Triggers:**
- Push to `main`, `develop`, `test-analysis-improvements` branches
- Pull requests to `main` and `develop`
- Any changes to `.py` files

### What Gets Checked

1. **Pylint Analysis** - Code quality and style checking
2. **Black Formatting** - Code formatting validation  
3. **Bandit Security** - Security vulnerability scanning
4. **Isort Import Sorting** - Import statement organization
5. **Radon Complexity** - Code complexity analysis
6. **Test Coverage** - Unit test coverage reporting

## 📋 Pylint Configuration

### Configuration File: `.pylintrc`

The project includes a comprehensive pylint configuration that:
- Sets reasonable quality standards
- Disables overly strict warnings for this project type
- Configures appropriate limits for complexity metrics
- Defines project-specific naming conventions

### Key Settings

```ini
[FORMAT]
max-line-length=120        # Consistent with Black formatter

[DESIGN]  
max-args=10               # Function argument limit
max-attributes=15         # Class attribute limit
max-statements=50         # Function statement limit

[MESSAGES CONTROL]
# Disabled warnings for practical development:
# C0114,C0115,C0116 - Missing docstrings (too verbose for this project)
# R0903 - Too few public methods (common for data classes)
# R0913 - Too many arguments (common for configuration functions)
```

## 🎯 Quality Metrics

### Pylint Scoring
- **9.0-10.0** - Excellent (Green badge)
- **8.0-8.9** - Good (Green badge)  
- **7.0-7.9** - Acceptable (Yellow-green badge)
- **6.0-6.9** - Needs improvement (Yellow badge)
- **5.0-5.9** - Poor (Orange badge)
- **< 5.0** - Critical issues (Red badge)

### Target Quality Standards
- **Source Code (`src/`)**: Must pass pylint without critical errors
- **Scripts (`scripts/`)**: Must pass pylint without critical errors
- **Tests (`tests/`)**: May have some pylint warnings (test-specific patterns)
- **Examples (`examples/`)**: Should pass basic pylint checks

## 🛠️ Local Development Workflow

### Before Committing Code

1. **Format your code:**
   ```bash
   black src/ scripts/ tests/ examples/
   isort src/ scripts/ tests/ examples/
   ```

2. **Run quality checks:**
   ```bash
   python scripts/run_pylint.py
   ```

3. **Fix any critical issues** identified by pylint

4. **Run tests:**
   ```bash
   python tests/test_analysis_generator.py
   ```

### IDE Integration

#### VS Code
Add to `.vscode/settings.json`:
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.pylintArgs": ["--rcfile=.pylintrc"],
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=120"]
}
```

#### PyCharm
1. Install Pylint plugin
2. Configure External Tools → Pylint
3. Set arguments: `--rcfile=.pylintrc`

## 📊 GitHub Actions Reports

### Pull Request Comments
The pylint workflow automatically comments on pull requests with:
- Pylint score for each Python version
- Detailed quality report
- Comparison with previous results

### Artifacts
Each workflow run produces:
- `pylint-report-{python-version}` - Detailed analysis reports
- `pylint-badge` - Quality score badge (for main branch)

### Coverage Reports
- Uploaded to Codecov for tracking
- Includes both source code and scripts
- Shows line-by-line coverage analysis

## 🔧 Customizing Quality Checks

### Adding New Pylint Rules
Edit `.pylintrc`:
```ini
[MESSAGES CONTROL]
# Remove from disable list to enable:
# enable=C0114  # missing-module-docstring
```

### Project-Specific Patterns
For analysis generator specific patterns:
```ini
[VARIABLES]
good-names=i,j,k,df,analysis,csv_file,miner_data
```

### Excluding Files
```ini
[MASTER]
ignore=legacy_code.py,deprecated/
```

## 🚨 Common Issues & Solutions

### Issue: "Module has no attribute" errors
**Cause:** Missing dependencies or import issues  
**Solution:** Ensure all requirements are installed:
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### Issue: Line too long errors
**Cause:** Lines exceeding 120 characters  
**Solution:** Use Black formatter:
```bash
black --line-length=120 your_file.py
```

### Issue: Import order warnings
**Cause:** Incorrect import organization  
**Solution:** Use isort:
```bash
isort your_file.py --profile black
```

### Issue: Too many arguments/locals warnings
**Cause:** Complex functions needing refactoring  
**Solution:** Break down large functions or disable specific warnings:
```python
# pylint: disable=too-many-arguments
def complex_function(arg1, arg2, arg3, arg4, arg5, arg6):
    pass
```

## 📈 Continuous Improvement

### Quality Metrics Tracking
- Pylint scores tracked over time
- Coverage reports show testing improvements
- Security scans identify potential vulnerabilities

### Regular Reviews
- Monthly quality assessment
- Update pylint configuration as project evolves
- Add new quality tools as needed

### Community Standards
- Follow Python PEP 8 style guidelines
- Maintain consistent code formatting
- Ensure comprehensive error handling
- Write clear, maintainable code

## 🎯 Goals

1. **Maintain high code quality** - Target 8.0+ pylint score
2. **Prevent regressions** - Catch issues before merge
3. **Improve maintainability** - Consistent style and structure
4. **Enable collaboration** - Clear standards for contributors
5. **Professional standards** - Production-ready code quality

The integrated pylint workflow ensures that the Bitaxe Monitor project maintains professional-grade code quality while remaining accessible to contributors of all skill levels.
