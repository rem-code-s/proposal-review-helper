# Code Review Makefile
# Provides reproducible commands for reviewing code changes

# Configuration file for persistent settings
CONFIG_FILE := .review-config
REPO_CACHE_DIR := .repo-cache

# Load persistent settings if config file exists
ifneq (,$(wildcard $(CONFIG_FILE)))
    include $(CONFIG_FILE)
endif

# Default variables (can be overridden)
START_COMMIT ?= 
END_COMMIT ?= 
REVIEW_PATHS ?= 

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help review open-html open-markdown clean clean-cache

# Default target
help: ## Show this help message
	@echo "$(BLUE)Code Review Makefile$(NC)"
	@echo "$(BLUE)===================$(NC)"
	@echo ""
	@echo "$(GREEN)Usage:$(NC)"
	@echo "  make review REPO=<repo_url> ID=<proposal_id> START_COMMIT=<hash> END_COMMIT=<hash> REVIEW_PATHS='path1 path2'"
	@echo "  Note: Use END_COMMIT=HEAD to review up to the latest commit"
	@echo ""
	@echo "$(GREEN)Examples:$(NC)"
	@echo "  make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=HEAD REVIEW_PATHS='rs/sns/governance'"
	@echo "  make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS='rs/sns/governance'"
	@echo "  make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=HEAD REVIEW_PATHS='rs/nns/governance rs/sns/init'"
	@echo "  make review REPO=https://github.com/dfinity/cycles-ledger.git ID=2323 START_COMMIT=abc123 END_COMMIT=def456"
	@echo "  make open-html    # Open latest HTML report"
	@echo "  make open-markdown # Open latest markdown report"
	@echo "  make clean        # Clean up generated files and config"
	@echo "  make clean-cache  # Clean up repository cache"
	@echo ""
	@echo "$(GREEN)Current settings:$(NC)"
	@if [ -n "$(START_COMMIT)" ]; then \
		echo "  START_COMMIT: $(START_COMMIT)"; \
	else \
		echo "  START_COMMIT: $(YELLOW)(not set)$(NC)"; \
	fi
	@if [ -n "$(END_COMMIT)" ]; then \
		echo "  END_COMMIT: $(END_COMMIT)"; \
	else \
		echo "  END_COMMIT: $(YELLOW)(not set)$(NC)"; \
	fi
	@if [ -n "$(REVIEW_PATHS)" ]; then \
		echo "  REVIEW_PATHS: $(REVIEW_PATHS)"; \
	else \
		echo "  REVIEW_PATHS: $(YELLOW)(not set)$(NC)"; \
	fi

review: $(REPO_CACHE_DIR) ## Generate HTML and markdown reports for the specified commit range and paths (requires REPO)
	@if [ -z "$(REPO)" ] || [ -z "$(START_COMMIT)" ] || [ -z "$(END_COMMIT)" ] || [ -z "$(REVIEW_PATHS)" ]; then \
		echo "$(RED)Error: REPO, START_COMMIT, END_COMMIT, and REVIEW_PATHS are required$(NC)"; \
		echo "Usage: make review REPO=<repo_url> ID=<proposal_id> START_COMMIT=<hash> END_COMMIT=<hash> REVIEW_PATHS='path1 path2'"; \
		echo "Note: Use END_COMMIT=HEAD to review up to the latest commit"; \
		echo "Example: make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=HEAD REVIEW_PATHS='rs/sns/governance'"; \
		echo "Example: make review REPO=https://github.com/dfinity/ic.git ID=138584 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS='rs/sns/governance'"; \
		echo "Example: make review REPO=https://github.com/dfinity/cycles-ledger.git ID=2323 START_COMMIT=abc123 END_COMMIT=def456 REVIEW_PATHS='cycles-ledger'"; \
		exit 1; \
	fi
	@echo "$(BLUE)=== Generating Review Reports ===$(NC)"
	@echo "$(YELLOW)Repository: $(REPO)$(NC)"
	@echo "$(YELLOW)Commit range: $(START_COMMIT)..$(END_COMMIT)$(NC)"
	@echo "$(YELLOW)Paths: $(REVIEW_PATHS)$(NC)"
	@echo ""
	@echo "$(YELLOW)Storing configuration...$(NC)"
	@echo "REPO := $(REPO)" > $(CONFIG_FILE)
	@echo "START_COMMIT := $(START_COMMIT)" >> $(CONFIG_FILE)
	@echo "END_COMMIT := $(END_COMMIT)" >> $(CONFIG_FILE)
	@echo "REVIEW_PATHS := $(REVIEW_PATHS)" >> $(CONFIG_FILE)
	@if [ -n "$(ID)" ]; then \
		echo "ID := $(ID)" >> $(CONFIG_FILE); \
		echo "$(GREEN)✓ Configuration stored (with Proposal ID: $(ID))$(NC)"; \
	else \
		echo "$(GREEN)✓ Configuration stored$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)Generating HTML report...$(NC)"
	@source venv/bin/activate && python3 generate-html-review.py --start $(START_COMMIT) --end $(END_COMMIT) --path $(REVIEW_PATHS) --repo "$(REPO)" --repo-url "$(shell echo '$(REPO)' | sed 's/\.git$$//')" --proposal-id $(ID) --cache-dir "$(REPO_CACHE_DIR)"
	@echo "$(GREEN)✓ HTML report generated$(NC)"
	@echo ""
	@echo "$(YELLOW)Generating Markdown report...$(NC)"
	@source venv/bin/activate && python3 generate-review.py --start $(START_COMMIT) --end $(END_COMMIT) --path $(REVIEW_PATHS) --type full --repo "$(REPO)" --proposal-id $(ID) --cache-dir "$(REPO_CACHE_DIR)" --repo-url "$(shell echo '$(REPO)' | sed 's/\.git$$//')"
	@echo "$(GREEN)✓ Markdown report generated$(NC)"
	@echo ""
	@echo "$(GREEN)✓ Reports generated with auto-naming$(NC)"
	@echo "$(YELLOW)Use 'make open-html' or 'make open-markdown' to view them$(NC)"

# Ensure repository cache directory exists
$(REPO_CACHE_DIR):
	@mkdir -p $(REPO_CACHE_DIR)

open-html: ## Open the latest HTML report in your default browser
	@LATEST_FOLDER=$$(ls -td generated/* 2>/dev/null | head -1); \
	if [ -z "$$LATEST_FOLDER" ]; then \
		echo "$(RED)Error: No HTML review report found$(NC)"; \
		echo "Run 'make review' first to generate reports"; \
		exit 1; \
	fi; \
	LATEST_HTML=$$(ls "$$LATEST_FOLDER"/*.html 2>/dev/null | head -1); \
	if [ -z "$$LATEST_HTML" ]; then \
		echo "$(RED)Error: No HTML file found in latest folder$(NC)"; \
		exit 1; \
	fi; \
	echo "$(BLUE)Opening HTML report: $$LATEST_HTML$(NC)"; \
	open "$$LATEST_HTML"

open-markdown: ## Open the latest markdown report in your default editor
	@LATEST_FOLDER=$$(ls -td generated/* 2>/dev/null | head -1); \
	if [ -z "$$LATEST_FOLDER" ]; then \
		echo "$(RED)Error: No markdown review report found$(NC)"; \
		echo "Run 'make review' first to generate reports"; \
		exit 1; \
	fi; \
	LATEST_MD=$$(ls "$$LATEST_FOLDER"/*.md 2>/dev/null | head -1); \
	if [ -z "$$LATEST_MD" ]; then \
		echo "$(RED)Error: No markdown file found in latest folder$(NC)"; \
		exit 1; \
	fi; \
	echo "$(BLUE)Opening markdown report: $$LATEST_MD$(NC)"; \
	open "$$LATEST_MD"

clean: ## Clean up generated files and temporary data
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@rm -rf generated/
	@rm -f $(CONFIG_FILE)
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-cache: ## Clean up repository cache
	@echo "$(YELLOW)Cleaning up repository cache...$(NC)"
	@rm -rf $(REPO_CACHE_DIR)
	@echo "$(GREEN)✓ Repository cache cleaned$(NC)"