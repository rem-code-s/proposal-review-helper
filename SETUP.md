# Proposal Reviewer Setup

## Overview

The Proposal Reviewer tools provide a streamlined system for reviewing code changes across commit ranges with beautiful HTML and markdown reports.

## Directory Structure

```
proposal-reviewer/
├── Makefile                    # Main makefile with review commands
├── generate-review.py          # Markdown report generator
├── generate-html-review.py     # HTML report generator
├── requirements.txt            # Python dependencies
├── .review-config             # Persistent configuration (auto-generated)
├── .repo-cache/               # Cached repositories (auto-created)
├── generated/                 # All generated reports (auto-created)
└── REVIEW_README.md           # Complete documentation
```

## Quick Setup

1. **Create virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Test the setup:**
   ```bash
   make help
   ```

## Usage Examples

### Basic Usage

```bash
# Generate reports for a specific proposal
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS="rs/sns/governance"

# Multiple paths
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS="rs/nns/governance rs/sns/init"

# External repository
make review REPO=https://github.com/dfinity/cycles-ledger.git ID=2323 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS="cycles-ledger"

# Open reports
make open-html      # Open latest HTML report
make open-markdown  # Open latest markdown report
```

## Key Features

✅ **HTML Reports** - Beautiful, interactive code review interface  
✅ **Markdown Reports** - Static, shareable documentation format  
✅ **Configurable Commit Ranges** - Review any commit range  
✅ **Multiple Paths** - Review changes across different areas  
✅ **Repository Caching** - Fast subsequent runs  
✅ **Auto-Naming** - Organized output by proposal ID and date

## Benefits

1. **Repository Caching** - Fast subsequent runs with automatic updates
2. **Flexibility** - Review any commit range and paths
3. **Beautiful Reports** - Professional HTML and Markdown output
4. **Efficiency** - Streamlined workflow with persistent configuration
5. **Maintainability** - Easy to use and extend

## Troubleshooting

### Virtual Environment Not Activated

```bash
source venv/bin/activate
```

### Permission Issues

```bash
chmod +x *.sh
```

### Invalid Commit Range

```bash
# Make sure commits exist in the repository
git log --oneline START_COMMIT..END_COMMIT
```

## Next Steps

1. **Read the full documentation:** `REVIEW_README.md`
2. **Try the examples:** Start with `make help`
3. **Generate your first review:** Use `make review` with your parameters

The tools are now ready for your code review workflow!
