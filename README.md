# Proposal Reviewer

A powerful code review system that generates beautiful HTML and Markdown reports for analyzing commit ranges in any Git repository. Perfect for reviewing NNS proposals and code changes.

## 📋 Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [How It Works](#how-it-works)
- [Usage](#usage)
- [Examples](#examples)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- **📊 Beautiful HTML Reports** - Interactive, dark-themed code review interface with:

  - Side-by-side diff view
  - Clickable commit hashes linking to GitHub
  - Hover-to-reveal line links
  - Commit type badges (feat, fix, chore, etc.)
  - Collapsible sections for easy navigation
  - Keyboard shortcuts (Ctrl+K to scroll to top)

- **📝 Markdown Reports** - Clean, shareable documentation format with:

  - Commit summaries and statistics
  - File change details
  - Easy to share and version control

- **🚀 Smart Caching** - Repository caching for blazing-fast subsequent runs
- **🎯 Multi-Path Support** - Review changes across multiple directories at once
- **🔧 Persistent Configuration** - Remembers your last settings
- **🌐 Any Repository** - Works with any GitHub repository, not just IC

## 📦 Requirements

- **Python 3.7+** - For running the report generators
- **Git** - For repository operations
- **Make** - For simplified command execution (comes with macOS/Linux)
- **Internet connection** - For cloning/updating repositories

### Python Dependencies

- `requests>=2.25.0` - For HTTP operations

## 🚀 Installation

### 1. Clone or Download

If you haven't already, get the proposal-reviewer directory.

### 2. Create Virtual Environment

```bash
cd proposal-reviewer
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
make help
```

You should see the help menu with all available commands.

## 🔍 How It Works

### Architecture

```
┌─────────────────┐
│   make review   │
│  (User Input)   │
└────────┬────────┘
         │
         ├──────────────────────────────────┐
         │                                  │
         v                                  v
┌────────────────────┐           ┌──────────────────────┐
│  Repository Cache  │           │  Commit Range Query  │
│   (.repo-cache/)   │           │   (git log)          │
└────────┬───────────┘           └──────────┬───────────┘
         │                                  │
         v                                  v
┌────────────────────┐           ┌──────────────────────┐
│   Clone or Pull    │──────────>│  Extract Changes     │
│   Repository       │           │  (git diff)          │
└────────────────────┘           └──────────┬───────────┘
                                            │
                    ┌───────────────────────┴─────────────────┐
                    │                                         │
                    v                                         v
         ┌──────────────────────┐                ┌─────────────────────┐
         │  HTML Generator      │                │  Markdown Generator │
         │  (generate-html-     │                │  (generate-review-  │
         │   review.py)         │                │   .py)              │
         └──────────┬───────────┘                └──────────┬──────────┘
                    │                                       │
                    v                                       v
         ┌──────────────────────┐                ┌─────────────────────┐
         │  Beautiful HTML      │                │  Clean Markdown     │
         │  Report              │                │  Report             │
         └──────────────────────┘                └─────────────────────┘
```

### Process Flow

1. **Input**: You provide a repository URL, commit range, and paths to review
2. **Caching**: The system checks if the repository is cached in `.repo-cache/`
   - If cached: runs `git pull` to update
   - If not: clones the repository
3. **Analysis**: Extracts commit information and diffs using `git log` and `git diff`
4. **Generation**: Creates both HTML and Markdown reports with:
   - Commit metadata (author, date, message)
   - File changes with line-by-line diffs
   - Statistics and summaries
5. **Output**: Saves reports to `generated/{proposal-id}-{repo}-{date}/`

### Repository Caching

The system uses intelligent caching to avoid re-cloning repositories:

- **First run**: Clones repository to `.repo-cache/{repo-name}/`
- **Subsequent runs**: Updates existing cache with `git pull`
- **Multiple repos**: Each repository gets its own cache directory
- **Manual cleanup**: Use `make clean-cache` to remove cached repositories

## 📖 Usage

### Basic Command Structure

```bash
make review REPO=<repo_url> ID=<proposal_id> START_COMMIT=<hash> END_COMMIT=<hash> REVIEW_PATHS='<paths>'
```

### Parameters

| Parameter      | Description                       | Required | Example                             |
| -------------- | --------------------------------- | -------- | ----------------------------------- |
| `REPO`         | Repository URL                    | ✅ Yes   | `https://github.com/dfinity/ic.git` |
| `ID`           | Proposal ID for naming            | ✅ Yes   | `138584`                            |
| `START_COMMIT` | Starting commit hash              | ✅ Yes   | `abc123def`                         |
| `END_COMMIT`   | Ending commit hash or HEAD        | ✅ Yes   | `def456abc` or `HEAD`               |
| `REVIEW_PATHS` | Paths to review (space-separated) | ✅ Yes   | `"rs/sns/governance"`               |

### Available Commands

| Command              | Description                           |
| -------------------- | ------------------------------------- |
| `make help`          | Show help and current configuration   |
| `make review`        | Generate HTML and Markdown reports    |
| `make open-html`     | Open latest HTML report in browser    |
| `make open-markdown` | Open latest Markdown report in editor |
| `make clean`         | Remove generated files and config     |
| `make clean-cache`   | Remove cached repositories            |

## 💡 Examples

### Example 1: Review IC Repository Changes

```bash
# Review SNS governance changes for proposal 138584
make review \
  REPO=https://github.com/dfinity/ic.git \
  ID=138584 \
  START_COMMIT=0e4c8234a9e0508ae30c5b8a7498406294c25e95 \
  END_COMMIT=62b938b04d78fabc2bcef6404e2c40c06b88addd \
  REVIEW_PATHS="rs/sns/governance"

# Open the HTML report
make open-html
```

### Example 2: Review Multiple Paths

```bash
# Review changes across NNS and SNS governance
make review \
  REPO=https://github.com/dfinity/ic.git \
  ID=138584 \
  START_COMMIT=abc123 \
  END_COMMIT=def456 \
  REVIEW_PATHS="rs/nns/governance rs/sns/init rs/sns/governance"
```

### Example 3: Review External Repository

```bash
# Review cycles-ledger repository
make review \
  REPO=https://github.com/dfinity/cycles-ledger.git \
  ID=2323 \
  START_COMMIT=abc123 \
  END_COMMIT=def456 \
  REVIEW_PATHS="cycles-ledger"
```

### Example 4: Review Up to Latest Commit

```bash
# Use HEAD as the end commit to review up to the latest
make review \
  REPO=https://github.com/dfinity/ic.git \
  ID=138584 \
  START_COMMIT=abc123 \
  END_COMMIT=HEAD \
  REVIEW_PATHS="rs/registry/canister"
```

### Example 5: Review All Changes (No Path Filter)

```bash
# Review all changes in the commit range
make review \
  REPO=https://github.com/dfinity/ic.git \
  ID=138584 \
  START_COMMIT=abc123 \
  END_COMMIT=def456 \
  REVIEW_PATHS=""
```

## ⚙️ Configuration

### Persistent Settings

The system saves your last-used parameters in `.review-config`:

```makefile
REPO := https://github.com/dfinity/ic.git
START_COMMIT := abc123...
END_COMMIT := def456...
REVIEW_PATHS := rs/sns/governance
ID := 138584
```

**View current config:**

```bash
make help
```

**Clear config:**

```bash
rm .review-config
```

### Directory Structure

After running reviews, your directory will look like:

```
proposal-reviewer/
├── .repo-cache/                    # Cached repositories
│   ├── ic/                        # Cached IC repository
│   └── cycles-ledger/             # Cached cycles-ledger
├── generated/                      # Generated reports
│   ├── 138584-ic-20251021/        # Reports for proposal 138584
│   │   ├── 138584-ic-20251021.html
│   │   └── 138584-ic-20251021.md
│   └── 2323-cycles-ledger-20251021/
│       ├── 2323-cycles-ledger-20251021.html
│       └── 2323-cycles-ledger-20251021.md
├── generate-html-review.py        # HTML generator
├── generate-review.py             # Markdown generator
├── Makefile                       # Main commands
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

### Output File Naming

Files are automatically named with the pattern:

```
{proposal-id}-{repository}-{date}
```

Examples:

- `138584-ic-20251021` - IC repository, proposal 138584, Oct 21, 2025
- `2323-cycles-ledger-20251021` - Cycles Ledger, proposal 2323, Oct 21, 2025

## 🔧 Troubleshooting

### Virtual Environment Not Activated

**Error:** `python3: command not found` or `Module not found`

**Solution:**

```bash
source venv/bin/activate
```

### Repository Cache Issues

**Error:** `Repository not found` or `Failed to update`

**Solution:**

```bash
# Clear cache and try again
make clean-cache
make review REPO=... ID=... START_COMMIT=... END_COMMIT=... REVIEW_PATHS=...
```

### Invalid Commit Range

**Error:** `Invalid commit range`

**Solution:**

```bash
# Verify commits exist in the repository
git clone <REPO> temp-check
cd temp-check
git log --oneline START_COMMIT..END_COMMIT
cd ..
rm -rf temp-check
```

### No Reports Generated

**Error:** `No HTML/Markdown report found`

**Solution:**

1. Check that all required parameters are provided
2. Verify the commit range is valid
3. Ensure the paths exist in the repository
4. Check terminal output for error messages

### Permission Denied

**Error:** `Permission denied` when running scripts

**Solution:**

```bash
chmod +x *.sh
```

### Reports Won't Open

**Error:** `open: command not found` (Linux)

**Solution:**

```bash
# Linux: use xdg-open instead
xdg-open generated/*/latest.html

# Or find the file manually
ls -la generated/*/
```

## 🎯 Best Practices

1. **Use HEAD for Latest**: Use `END_COMMIT=HEAD` when reviewing up to the latest commit
2. **Specific Paths**: Specify paths to focus on relevant changes only
3. **Cache Management**: Clean cache occasionally to save disk space: `make clean-cache`
4. **HTML for Review**: Use HTML reports for interactive review
5. **Markdown for Sharing**: Use Markdown reports for documentation and sharing
6. **Save Config**: Let the system remember your settings for quick re-runs

## 📚 Additional Resources

- **Full Documentation**: See `REVIEW_README.md` for detailed feature documentation
- **Setup Guide**: See `SETUP.md` for setup instructions
- **Makefile**: Check the `Makefile` for all available commands

## 🤝 Contributing

Contributions to improve this tool are more than welcome! Whether you want to:

- 🐛 Fix bugs or issues
- ✨ Add new features
- 📝 Improve documentation
- 🎨 Enhance the UI/UX of reports
- ⚡ Optimize performance
- 🧪 Add tests

Feel free to:

- Open an issue to discuss ideas
- Submit pull requests with improvements
- Fork and adapt for your specific needs
- Share feedback and suggestions

All contributions, big or small, are appreciated!

## 📄 License

This project is provided as-is for code review purposes.

---

**Happy Reviewing! 🎉**

For questions or issues, please check the troubleshooting section above or review the generated output for error messages.
