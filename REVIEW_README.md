# Code Review System

A streamlined system for reviewing code changes across commit ranges with beautiful HTML and markdown reports.

## 🚀 Quick Start

```bash
# Generate reports (HTML and Markdown)
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS="rs/sns/governance"

# Multiple paths
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS="rs/nns/governance rs/sns/init"

# External repository
make review REPO=https://github.com/dfinity/cycles-ledger.git ID=2323 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS="cycles-ledger"

# Open reports
make open-html      # Opens latest HTML report in browser
make open-markdown  # Opens latest markdown report in editor
```

## 📋 Available Commands

### `make review`

Generates HTML and Markdown reports for the specified commit range and paths.

**Required Parameters:**

- `REPO` - Repository URL (e.g., https://github.com/dfinity/ic.git)
- `ID` - NNS proposal ID (for proper file naming and proposal links)
- `START_COMMIT` - Starting commit hash
- `END_COMMIT` - Ending commit hash
- `REVIEW_PATHS` - Space-separated paths to review

**Examples:**

```bash
# Single path (IC repository)
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS="rs/sns/governance"

# Multiple paths (IC repository)
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS="rs/nns/governance rs/sns/init"

# External repository
make review REPO=https://github.com/dfinity/cycles-ledger.git ID=2323 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS="cycles-ledger"

# All changes (no path restriction)
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS=""
```

### `make open-html`

Opens the latest HTML report in your default browser.

### `make open-markdown`

Opens the latest markdown report in your default editor.

### `make help`

Shows usage information and current configuration.

## 📁 Auto-Naming Feature

All generated files are automatically named with descriptive information:

**Format:** `generated/{proposal_id}-{repo}-{date}/{filename}.{ext}`

**Examples:**

- `generated/138584-ic-20250919/138584-ic-20250919.html`
- `generated/138584-ic-20250919/138584-ic-20250919.md`
- `generated/2323-cycles-ledger-20250919/2323-cycles-ledger-20250919.html`
- `generated/2323-cycles-ledger-20250919/2323-cycles-ledger-20250919.md`

## 📊 Report Types

### HTML Report (Recommended)

- **Best for**: Interactive code review, side-by-side diffs
- **Features**:
  - Dark theme optimized for developers
  - Side-by-side diff view
  - Clickable commit hashes (links to GitHub)
  - GitHub line links (🔗 icons on hover)
  - Commit type badges (feat, fix, chore, etc.)
  - Dense code display
  - Keyboard shortcuts (Ctrl+K for scroll to top)
  - Collapsible sections
- **Output**: `{proposal_id}-{repo}-{date}/{filename}.html`
- **Use when**: You want the best interactive review experience

### Markdown Report

- **Best for**: Static review, sharing, documentation
- **Features**: Clean markdown format, file statistics, commit summaries
- **Output**: `{proposal_id}-{repo}-{date}/{filename}.md`
- **Use when**: You need a static, shareable format

## 📝 Setup

### Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Repository Caching

The system uses intelligent repository caching to improve performance:

### How It Works

- **Persistent Storage**: Repositories are cached in `.repo-cache/` directory
- **Automatic Updates**: Runs `git pull` to update cached repositories
- **Smart Naming**: Each repository gets its own cache directory
- **Fast Subsequent Runs**: No need to clone repositories repeatedly

### Cache Management

```bash
# View cached repositories
ls -la .repo-cache/

# Clean repository cache (forces fresh clone on next run)
make clean-cache

# Clean all generated files and cache
make clean
```

### Cache Structure

```
.repo-cache/
├── cycles-ledger/          # Cached cycles-ledger repository
├── ic/                     # Cached IC repository (if used)
└── other-repos/            # Other cached repositories
```

## 🔧 Configuration

The system automatically stores your last used parameters in `.review-config`:

```bash
REPO := https://github.com/dfinity/ic.git
START_COMMIT := abc123...
END_COMMIT := def456...
REVIEW_PATHS := rs/sns/governance
ID := 138584
```

This allows you to:

- See current settings with `make help`
- Reuse the same parameters for multiple report generations
- Clear the config by deleting `.review-config`

## 🎯 Multiple Paths Support

The system automatically detects and handles multiple paths:

**Features:**

- **Multiple paths** - Specify multiple paths separated by spaces
- **All report types** - Works with HTML and Markdown reports
- **Flexible** - Can specify any number of paths

**Usage:**

```bash
# Multiple paths
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS="rs/nns/governance rs/sns/init"

# Many paths
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS="rs/nns/governance rs/sns/init rs/consensus"
```

## 🛠️ Technical Details

### Repository Structure

```
proposal-reviewer/
├── Makefile                    # Main makefile with simplified commands
├── generate-review.py          # Markdown report generator
├── generate-html-review.py     # HTML report generator
├── .review-config             # Persistent configuration (auto-generated)
├── generated/                 # All generated reports (auto-created)
│   └── {id}-{repo}-{date}/    # Report folders (one per review)
│       ├── *.html             # HTML report
│       └── *.md               # Markdown report
└── REVIEW_README.md           # This documentation
```

### Dependencies

- Python 3.x
- Git (for repository operations)
- Make (for running commands)
- Internet connection (for cloning external repositories)

### Repository Support

The system supports both local and external repositories:

- **External Repositories**: Specify any GitHub repository URL with the `REPO` parameter
- **Local Repositories**: Can be used as fallback (though external repos are recommended)
- **Repository Caching**: All repositories are cached locally for fast subsequent runs

## 🎨 HTML Report Features

### Developer-Focused Design

- **Dark theme** - Easy on the eyes for long review sessions
- **Monospace fonts** - Consistent code display
- **Dense layout** - More code visible at once
- **Professional styling** - Clean, modern interface

### Interactive Features

- **Clickable commit hashes** - Direct links to GitHub commit diffs
- **GitHub line links** - 🔗 icons appear on hover, link to exact lines
- **Commit type badges** - Visual indicators for feat/fix/chore/etc.
- **Collapsible sections** - Hide/show individual commits
- **Keyboard shortcuts** - Ctrl+K for scroll to top

### Navigation

- **Scroll to top button** - Quick navigation
- **Commit summary table** - Overview of all changes
- **File statistics** - Quick metrics about changes

## 📝 Examples

### Basic Workflow

```bash
# 1. Generate reports for SNS governance changes
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=0e4c8234 END_COMMIT=ca94383b REVIEW_PATHS="rs/sns/governance"

# 2. Open HTML report for interactive review
make open-html

# 3. Generate reports for multiple areas
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=0e4c8234 END_COMMIT=ca94383b REVIEW_PATHS="rs/nns/governance rs/sns/init"

# 4. Open markdown report for sharing
make open-markdown
```

### Advanced Usage

```bash
# Review all changes in a commit range
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS=""

# Review specific files across multiple directories
make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS="rs/consensus rs/crypto rs/types"

# Check current configuration
make help
```

## 🚨 Troubleshooting

### "No HTML/Markdown report found"

- Run `make review` first to generate reports
- Check that the commit range is valid
- Ensure the paths exist in the repository

### "Error: START_COMMIT, END_COMMIT, and REVIEW_PATHS are required"

- Provide all required parameters
- Use quotes around paths with spaces: `REVIEW_PATHS="path1 path2"`

### Reports not opening

- Check that you have a default browser/editor configured
- Try opening the files manually from the file system

## 📈 Benefits

- **Streamlined workflow** - Single command generates all report types
- **Persistent configuration** - No need to re-enter parameters
- **Smart naming** - Files organized by proposal ID, repository, and date
- **Repository caching** - Fast subsequent runs with automatic updates
- **External repository support** - Review any GitHub repository
- **Organized output** - All reports saved to `generated/` folder
- **Multiple path support** - Review changes across different areas
- **Developer-focused** - HTML reports optimized for code review
- **Flexible** - Works with any commit range and path combination
