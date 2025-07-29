# OLS Fetch from GitHub Module

A comprehensive Python module for fetching, processing, and managing SBO (Systems Biology Ontology) files from GitHub repositories with automated change tracking and user file validation.

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Repository Structure](#repository-structure)
- [Directory Structure](#directory-structure)
- [Testing](#testing)
- [Dependencies](#dependencies)

## Overview

The `ols_fetch_from_github` module provides a complete workflow for:
- 🔄 Fetching SBO ontology files from GitHub repositories
- 📊 Comparing file versions and tracking changes
- 📁 Processing user-uploaded files (OBO/JSON formats)
- ✅ Validating file structure and content
- 📝 Logging changes between versions
- 🛠️ Converting between OBO and JSON formats

## Quick Start

**Main Entry Point**: `main_workflow.py`

```bash
# From project root directory
python -m src.ols_fetch_from_github.main_workflow

```

## Repository Structure

```
src/ols_fetch_from_github/
├── README.md                    # This file
├── config.json                  # Configuration settings
├── __init__.py                  # Package initialization
├── main_workflow.py             # Main workflow orchestrator
├── github_file_updater.py       # GitHub file management
├── user_file_processor.py       # User file processing
├── config.py                    # Configuration management
├── file_downloader.py           # File download utilities
├── file_converter.py            # OBO ↔ JSON conversion
├── file_validator.py            # File validation logic
├── file_comparator.py           # File comparison utilities
├── obo_parser.py                # OBO format parser
├── change_logger.py             # Change tracking and logging
├── utils.py                     # General utilities and helpers
│
└── SBO_OBO_Files/               # Data directory (created at runtime)
    ├── localfiles/              # Processed SBO files
    ├── customerfile/            # User uploaded files
    └── logs/                    # Change logs

tests/ (separate directory)
├── run_tests.py                 # Test runner
├── test_*.py                    # Individual test modules
└── __init__.py                  # Test package init
```

## Directory Structure

### `SBO_OBO_Files/` - Main Data Directory
This directory contains all SBO ontology files and related data:

#### `localfiles/` - System Files
- **Purpose**: Stores officially processed SBO files from GitHub
- **Contents**:
  - `SBO_OBO_YYYYMMDD_HHMMSS.obo` - Original OBO files from GitHub
  - `SBO_OBO_YYYYMMDD_HHMMSS.json` - Converted JSON files
  - `SBO_OBO_YYYYMMDD_HHMMSS.obo.update_info` - Update metadata
- **Management**: Automatic cleanup of old versions, keeps top 2 latest files

#### `customerfile/` - User Uploads
- **Purpose**: Temporary storage for user-uploaded files
- **Contents**:
  - User uploaded `.obo` or `.json` files
  - `*_user_upload.json` - Processed user files
  - `*_user_upload_converted.obo` - Validation files
- **Management**: Cleaned up at beginning of each session

#### `logs/` - Change Tracking
- **Purpose**: Maintains detailed logs of changes between versions
- **Contents**:
  - `sbo_changes_YYYYMMDD_HHMMSS.json` - Change logs with timestamps
- **Structure**:
  ```json
  {
    "timestamp": "2023-05-16 11:01:22",
    "has_changes": true,
    "stats": {
      "terms_added": 5,
      "terms_updated": 12,
      "terms_deleted": 0
    },
    "term_changes": {
      "added": [...],
      "updated": [...],
      "deleted": [...]
    }
  }
  ```

### `tests/` - Test Suite
Complete test coverage for all module components:

#### Test Files
- `test_main_workflow.py` - Main workflow testing
- `test_github_file_updater.py` - GitHub operations testing
- `test_user_file_processor.py` - User file processing testing
- `test_file_converter.py` - Format conversion testing
- `test_file_validator.py` - File validation testing
- `test_obo_parser.py` - OBO parsing testing
- `test_change_logger.py` - Change logging testing
- `test_config.py` - Configuration testing
- `test_utils.py` - Utility functions testing

## Module Components

### Core Classes
- **`SBOWorkflowManager`** (main_workflow.py) - Main workflow orchestrator that coordinates the entire SBO file processing pipeline
- **`GitHubFileUpdater`** (github_file_updater.py) - Manages GitHub file operations including downloading, updating, and version comparison
- **`UserFileProcessor`** (user_file_processor.py) - Processes user uploaded files with validation and format conversion
- **`Config`** (config.py) - Configuration management system that loads and provides access to system settings

### File Processing Classes
- **`FileDownloader`** (file_downloader.py) - Handles downloading files from GitHub API with error handling and retry logic
- **`FileConverter`** (file_converter.py) - Converts between OBO and JSON formats while preserving data structure
- **`FileValidator`** (file_validator.py) - Validates file structure and content for both OBO and JSON formats
- **`FileComparator`** (file_comparator.py) - Compares different versions of files to detect changes
- **`OBOFileParser`** (obo_parser.py) - Parses OBO format files into structured data representations

### Utility Classes
- **`ChangeLogger`** (change_logger.py) - Tracks and logs changes between file versions with detailed analysis
- **`FileUtils`** (utils.py) - Provides static utility functions for file operations and directory management
- **`DirectoryManager`** (utils.py) - Manages directory structure and ensures proper file organization
- **`ValidationResult`** (utils.py) - Data structure for storing validation results and error information





## Testing

### Test Coverage
- **173 total tests** covering all modules
- **Unit tests** for individual components
- **Mock testing** for external dependencies

### Test Categories
- **Configuration**: Config loading and validation
- **File Operations**: Download, conversion, validation
- **Workflow**: End-to-end workflow testing
- **Error Handling**: Exception and error cases
- **User Interaction**: Input/output testing
### Running Tests
```bash
# Run all tests
python tests/run_tests.py

# Run specific test module
python tests/run_tests.py test_config

# Run with verbose output
python tests/run_tests.py -v

# Run specific test class
python -m pytest tests/test_main_workflow.py::TestSBOWorkflowManager -v
```

## Dependencies

### Core Dependencies
- **Python 3.8+** - Core language version
- **Standard Library**: `json`, `os`, `glob`, `shutil`, `datetime`, `urllib`
- **Git** - For advanced file comparison operations
- **requests** - For HTTP operations (fallback to urllib)

### Development Dependencies
- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **unittest** - Built-in testing (alternative)


## License

This module is part of the SBOannotator project and follows the same licensing terms.