#!/usr/bin/env python3
"""
Generate beautiful HTML code review reports with side-by-side comparisons
"""

import subprocess
import sys
import os
import re
from datetime import datetime
import argparse
import html
import tempfile
import shutil

def clone_external_repo(repo_url):
    """Clone external repository to temporary directory"""
    temp_dir = tempfile.mkdtemp(prefix='html_review_')
    try:
        print(f"📥 Cloning repository: {repo_url}")
        result = subprocess.run(['git', 'clone', repo_url, temp_dir], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Repository cloned to: {temp_dir}")
        return temp_dir
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to clone repository: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None

def get_cached_repo(repo_url, cache_dir):
    """Get or clone repository to cache directory"""
    # Create a safe directory name from the repo URL
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    if not repo_name:
        repo_name = repo_url.split('/')[-2]
    
    cached_repo_path = os.path.join(cache_dir, repo_name)
    
    if os.path.exists(cached_repo_path):
        print(f"🔄 Using cached repository: {cached_repo_path}")
        print(f"📥 Updating repository...")
        try:
            # Update the cached repository
            subprocess.run(['git', 'pull'], cwd=cached_repo_path, 
                         capture_output=True, text=True, check=True)
            print(f"✅ Repository updated")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Failed to update repository: {e}")
            print(f"   Continuing with existing cache...")
    else:
        print(f"📥 Cloning repository to cache: {repo_url}")
        try:
            os.makedirs(cache_dir, exist_ok=True)
            subprocess.run(['git', 'clone', repo_url, cached_repo_path], 
                         capture_output=True, text=True, check=True)
            print(f"✅ Repository cached to: {cached_repo_path}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to clone repository: {e}")
            return None
    
    return cached_repo_path

def run_git_command(cmd, cwd=None):
    """Run a git command and return the output"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"Error: {result.stderr}")
            return ""
        return result.stdout.strip()
    except Exception as e:
        print(f"Exception running command: {cmd}")
        print(f"Exception: {e}")
        return ""

def get_commit_stats(start_commit, end_commit, paths=None, repo_dir=None):
    """Get statistics for the commit range"""
    # Build path filter for git commands
    if paths:
        if isinstance(paths, list):
            path_filter = " -- " + " ".join(paths)
        else:
            path_filter = f" -- {paths}"
    else:
        path_filter = ""
    
    # Count commits
    commit_count = run_git_command(f"git rev-list --count {start_commit}..{end_commit}{path_filter}", repo_dir)
    
    # Get file list
    files_output = run_git_command(f"git diff --name-only {start_commit}..{end_commit}{path_filter}", repo_dir)
    files = [f for f in files_output.split('\n') if f.strip()]
    file_count = len(files)
    
    # Get diff stats
    diff_stats = run_git_command(f"git diff --stat {start_commit}..{end_commit}{path_filter}", repo_dir)
    
    # Parse lines added/removed from the last line of diff --stat
    lines_added = 0
    lines_removed = 0
    if diff_stats:
        lines = diff_stats.split('\n')
        if lines:
            last_line = lines[-1]
            if '|' in last_line:
                parts = last_line.split('|')
                if len(parts) >= 2:
                    changes = parts[1].strip()
                    if '+' in changes and '-' in changes:
                        # Extract numbers from "X files changed, Y insertions(+), Z deletions(-)"
                        insertions = re.search(r'(\d+)\s*insertions?', changes)
                        deletions = re.search(r'(\d+)\s*deletions?', changes)
                        if insertions:
                            lines_added = int(insertions.group(1))
                        if deletions:
                            lines_removed = int(deletions.group(1))
    
    return {
        'commits': commit_count,
        'files': file_count,
        'lines_added': lines_added,
        'lines_removed': lines_removed,
        'file_list': files
    }

def get_commit_type(message):
    """Detect commit type from message"""
    message_lower = message.lower()
    if message_lower.startswith('feat'):
        return 'feat'
    elif message_lower.startswith('fix'):
        return 'fix'
    elif message_lower.startswith('chore'):
        return 'chore'
    elif message_lower.startswith('docs'):
        return 'docs'
    elif message_lower.startswith('refactor'):
        return 'refactor'
    elif message_lower.startswith('test'):
        return 'test'
    elif message_lower.startswith('style'):
        return 'style'
    else:
        return 'other'

def get_commits(start_commit, end_commit, paths=None, repo_dir=None):
    """Get list of commits in the range"""
    # Build path filter for git commands
    if paths:
        if isinstance(paths, list):
            path_filter = " -- " + " ".join(paths)
        else:
            path_filter = f" -- {paths}"
    else:
        path_filter = ""
    
    format_str = "%H|%s|%an|%ad"
    output = run_git_command(f"git log --format='{format_str}' --date=short {start_commit}..{end_commit}{path_filter}", repo_dir)
    commits = []
    for line in output.split('\n'):
        if line.strip():
            parts = line.split('|', 3)
            if len(parts) >= 4:
                commit_type = get_commit_type(parts[1])
                commits.append({
                    'hash': parts[0],
                    'message': parts[1],
                    'author': parts[2],
                    'date': parts[3],
                    'type': commit_type
                })
    return commits

def get_commit_details(commit_hash, paths=None, repo_dir=None):
    """Get detailed information about a specific commit"""
    # Build path filter for git commands
    if paths:
        if isinstance(paths, list):
            path_filter = " -- " + " ".join(paths)
        else:
            path_filter = f" -- {paths}"
    else:
        path_filter = ""
    
    # Get commit info
    author = run_git_command(f"git show --no-patch --format='%an <%ae>' {commit_hash}", repo_dir)
    date = run_git_command(f"git show --no-patch --format='%ad' --date=short {commit_hash}", repo_dir)
    message = run_git_command(f"git show --no-patch --format='%s' {commit_hash}", repo_dir)
    
    # Get files changed
    files = run_git_command(f"git show --name-only --format='' {commit_hash}{path_filter}", repo_dir)
    file_list = [f for f in files.split('\n') if f.strip()]
    
    # Get diff
    diff = run_git_command(f"git show {commit_hash}{path_filter}", repo_dir)
    
    return {
        'author': author,
        'date': date,
        'message': message,
        'files': file_list,
        'diff': diff
    }

def format_diff_as_html(diff_text, commit_hash, repo_url=None):
    """Convert git diff to HTML with syntax highlighting and GitHub links"""
    if not diff_text:
        return ""
    
    lines = diff_text.split('\n')
    html_lines = []
    current_file = None
    line_numbers = {'old': 0, 'new': 0}
    
    for line in lines:
        if line.startswith('+++') or line.startswith('---'):
            # File headers
            if line.startswith('+++'):
                current_file = line[4:].strip()
                if current_file == '/dev/null':
                    current_file = None
                # Remove the 'b/' prefix that git diff adds
                if current_file and current_file.startswith('b/'):
                    current_file = current_file[2:]
                # Also handle 'a/' prefix for removed files
                if current_file and current_file.startswith('a/'):
                    current_file = current_file[2:]
            html_lines.append(f'<div class="file-header">{html.escape(line)}</div>')
        elif line.startswith('@@'):
            # Hunk headers - parse line numbers
            import re
            match = re.search(r'@@ -(\d+),?\d* \+(\d+),?\d* @@', line)
            if match:
                line_numbers['old'] = int(match.group(1)) - 1
                line_numbers['new'] = int(match.group(2)) - 1
            html_lines.append(f'<div class="hunk-header">{html.escape(line)}</div>')
        elif line.startswith('+'):
            # Added lines
            line_numbers['new'] += 1
            github_link = ""
            if current_file and line_numbers['new'] > 0:
                github_url = f"{repo_url}/blob/{commit_hash}/{current_file}#L{line_numbers['new']}"
                github_link = f'<a href="{github_url}" class="github-link" target="_blank">🔗</a>'
            html_lines.append(f'<div class="line added"><span class="line-number">+{line_numbers["new"]}</span><span class="line-content">{html.escape(line[1:])}{github_link}</span></div>')
        elif line.startswith('-'):
            # Removed lines
            line_numbers['old'] += 1
            github_link = ""
            if current_file and line_numbers['old'] > 0:
                github_url = f"{repo_url}/blob/{commit_hash}~1/{current_file}#L{line_numbers['old']}"
                github_link = f'<a href="{github_url}" class="github-link" target="_blank">🔗</a>'
            html_lines.append(f'<div class="line removed"><span class="line-number">-{line_numbers["old"]}</span><span class="line-content">{html.escape(line[1:])}{github_link}</span></div>')
        else:
            # Context lines
            line_numbers['old'] += 1
            line_numbers['new'] += 1
            github_link = ""
            if current_file and line_numbers['new'] > 0:
                github_url = f"{repo_url}/blob/{commit_hash}/{current_file}#L{line_numbers['new']}"
                github_link = f'<a href="{github_url}" class="github-link" target="_blank">🔗</a>'
            html_lines.append(f'<div class="line context"><span class="line-number">{line_numbers["new"]}</span><span class="line-content">{html.escape(line)}{github_link}</span></div>')
    
    return '\n'.join(html_lines)

def generate_html_report(start_commit, end_commit, paths=None, output_file=None, repo_url=None, proposal_id=None, repo_dir=None):
    """Generate a comprehensive HTML review report with side-by-side view"""
    
    if output_file is None:
        # Generate filename with proposal ID and date (if available from config)
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        proposal_id = None
        
        # Try to read proposal ID from config file
        config_file = '.review-config'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_content = f.read()
                id_match = re.search(r'ID := (\d+)', config_content)
                if id_match:
                    proposal_id = id_match.group(1)
        
        if proposal_id:
            # Extract repo name from repo_url or use default
            if repo_url and repo_url != 'https://github.com/dfinity/ic':
                repo_name = repo_url.split('/')[-1].replace('.git', '')
                if not repo_name:
                    repo_name = repo_url.split('/')[-2]
            else:
                repo_name = 'ic'
            folder_name = f"{proposal_id}-{repo_name}-{date_str}"
        else:
            # Fallback to old format if no proposal ID
            if paths:
                if isinstance(paths, list):
                    path_short = '-'.join([p.replace('/', '-').replace('rs-', '').replace('sns-governance', 'sns-gov').replace('nns-governance', 'nns-gov') for p in paths])
                else:
                    path_short = paths.replace('/', '-').replace('rs-', '').replace('sns-governance', 'sns-gov').replace('nns-governance', 'nns-gov')
            else:
                path_short = 'all-changes'
            commit_short = f"{start_commit[:8]}-{end_commit[:8]}"
            folder_name = f"{date_str}-review-{path_short}-{commit_short}"
        os.makedirs(f"generated/{folder_name}", exist_ok=True)
        output_file = f"generated/{folder_name}/{folder_name}.html"
    
    print(f"Generating HTML report for {start_commit}..{end_commit}")
    
    # Get statistics
    stats = get_commit_stats(start_commit, end_commit, paths, repo_dir)
    commits = get_commits(start_commit, end_commit, paths, repo_dir)
    
    with open(output_file, 'w') as f:
        # HTML header with CSS
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Review Report</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Source Code Pro', monospace;
            line-height: 1.5;
            margin: 0;
            padding: 0;
            background-color: #0d1117;
            color: #e6edf3;
            font-size: 14px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: #161b22;
            min-height: 100vh;
        }
        .header {
            background: #21262d;
            border-bottom: 1px solid #30363d;
            padding: 20px 30px;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .header h1 {
            margin: 0;
            font-size: 1.8em;
            font-weight: 600;
            color: #f0f6fc;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .header .meta {
            margin-top: 10px;
            color: #8b949e;
            font-size: 0.9em;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .meta-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .content {
            padding: 30px;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #21262d;
            border: 1px solid #30363d;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        .stat-number {
            font-size: 1.8em;
            font-weight: 600;
            color: #58a6ff;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #8b949e;
            font-size: 0.8em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section h2 {
            color: #f0f6fc;
            border-bottom: 1px solid #30363d;
            padding-bottom: 8px;
            margin-bottom: 15px;
            font-size: 1.2em;
            font-weight: 600;
        }
        .commits-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            overflow: hidden;
        }
        .commits-table th,
        .commits-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #21262d;
        }
        .commits-table th {
            background-color: #161b22;
            font-weight: 600;
            color: #f0f6fc;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .commits-table tr:hover {
            background-color: #21262d;
        }
        .commits-table tr:last-child td {
            border-bottom: none;
        }
        .commit-hash {
            font-family: 'SF Mono', 'Monaco', monospace;
            background: #21262d;
            color: #58a6ff;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            border: 1px solid #30363d;
            text-decoration: none;
            transition: all 0.2s;
        }
        .commit-hash:hover {
            background: #30363d;
            color: #79c0ff;
            border-color: #58a6ff;
            text-decoration: none;
        }
        .commit-message {
            color: #e6edf3;
            max-width: 400px;
        }
        .commit-author {
            color: #8b949e;
            font-size: 0.9em;
        }
        .commit-date {
            color: #8b949e;
            font-size: 0.85em;
        }
        .files-list {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .files-list ul {
            margin: 0;
            padding-left: 0;
            list-style: none;
        }
        .files-list li {
            margin-bottom: 3px;
            font-family: 'SF Mono', 'Monaco', monospace;
            font-size: 0.9em;
            color: #8b949e;
            padding: 2px 0;
        }
        .files-list li:before {
            content: "📄 ";
            margin-right: 8px;
        }
        .commit-detail {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        .commit-header {
            background: #161b22;
            padding: 15px 20px;
            border-bottom: 1px solid #30363d;
        }
        .commit-title {
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 8px;
            color: #f0f6fc;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .commit-hash-large {
            font-family: 'SF Mono', 'Monaco', monospace;
            background: #21262d;
            color: #58a6ff;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.9em;
            border: 1px solid #30363d;
            text-decoration: none;
            transition: all 0.2s;
        }
        .commit-hash-large:hover {
            background: #30363d;
            color: #79c0ff;
            border-color: #58a6ff;
            text-decoration: none;
        }
        .commit-meta {
            color: #8b949e;
            font-size: 0.85em;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .commit-meta span {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .diff-container {
            background: #0d1117;
            overflow-x: auto;
            font-size: 12px;
            max-height: 600px;
            overflow-y: auto;
        }
        .file-header {
            background: #21262d;
            padding: 8px 15px;
            font-family: 'SF Mono', 'Monaco', monospace;
            font-size: 0.85em;
            border-bottom: 1px solid #30363d;
            color: #f0f6fc;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .file-icon {
            color: #58a6ff;
        }
        .hunk-header {
            background: #161b22;
            padding: 6px 15px;
            font-family: 'SF Mono', 'Monaco', monospace;
            font-size: 0.8em;
            color: #8b949e;
            border-bottom: 1px solid #21262d;
        }
        .line {
            display: flex;
            font-family: 'SF Mono', 'Monaco', monospace;
            font-size: 12px;
            line-height: 1.2;
            border-bottom: 1px solid #21262d;
            min-height: 18px;
        }
        .line:last-child {
            border-bottom: none;
        }
        .line-number {
            width: 40px;
            padding: 1px 6px;
            text-align: right;
            background: #161b22;
            border-right: 1px solid #30363d;
            color: #8b949e;
            user-select: none;
            font-size: 0.75em;
            min-width: 40px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
        }
        .line-content {
            flex: 1;
            padding: 1px 8px;
            white-space: pre-wrap;
            word-break: break-all;
            display: flex;
            align-items: center;
        }
        .github-link {
            margin-left: 8px;
            opacity: 0;
            transition: opacity 0.2s;
            color: #58a6ff;
            text-decoration: none;
            font-size: 0.8em;
            position: relative;
        }
        .line:hover .github-link {
            opacity: 1;
        }
        .github-link:hover {
            color: #79c0ff;
            text-decoration: underline;
        }
        .github-link::after {
            content: attr(href);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #21262d;
            color: #e6edf3;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.7em;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s;
            z-index: 1000;
            border: 1px solid #30363d;
        }
        .github-link:hover::after {
            opacity: 1;
        }
        .line.added {
            background: #0d4429;
        }
        .line.added .line-number {
            background: #1a472a;
            color: #3fb950;
        }
        .line.added .line-content {
            color: #a2d2a2;
        }
        .line.removed {
            background: #490202;
        }
        .line.removed .line-number {
            background: #5d1a1a;
            color: #f85149;
        }
        .line.removed .line-content {
            color: #ffa198;
        }
        .line.context .line-number {
            color: #6e7681;
        }
        .line.context .line-content {
            color: #e6edf3;
        }
        .toggle-button {
            background: #238636;
            color: #ffffff;
            border: 1px solid #2ea043;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8em;
            margin: 8px 0;
            font-family: inherit;
            transition: all 0.2s;
        }
        .toggle-button:hover {
            background: #2ea043;
            border-color: #3fb950;
        }
        .toggle-button.secondary {
            background: #21262d;
            border-color: #30363d;
            color: #8b949e;
        }
        .toggle-button.secondary:hover {
            background: #30363d;
            color: #e6edf3;
        }
        .collapsible {
            display: none;
        }
        .collapsible.show {
            display: block;
        }
        .commit-actions {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge.feat {
            background: #1a472a;
            color: #3fb950;
        }
        .badge.fix {
            background: #490202;
            color: #f85149;
        }
        .badge.chore {
            background: #21262d;
            color: #8b949e;
        }
        .badge.docs {
            background: #1c2128;
            color: #58a6ff;
        }
        .badge.refactor {
            background: #2d1b69;
            color: #a5a3ff;
        }
        .scroll-to-top {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #238636;
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            cursor: pointer;
            font-size: 18px;
            display: none;
            z-index: 1000;
        }
        .scroll-to-top:hover {
            background: #2ea043;
        }
        .scroll-to-top.show {
            display: block;
        }
        @media (max-width: 768px) {
            .content {
                padding: 15px;
            }
            .header {
                padding: 15px 20px;
            }
            .header .meta {
                flex-direction: column;
                gap: 5px;
            }
            .commits-table {
                font-size: 0.8em;
            }
            .commits-table th,
            .commits-table td {
                padding: 8px 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Code Review</h1>
            <div class="meta">
                <div class="meta-item">
                    <span>📊</span>
                    <span><strong>Range:</strong> <code>""")
        
        f.write(f"{start_commit[:8]}</code> → <code>{end_commit[:8]}</code>")
        
        f.write("""</span>
                </div>
                <div class="meta-item">
                    <span>📁</span>
                    <span><strong>Path:</strong> <code>""")
        
        if paths:
            if isinstance(paths, list):
                f.write(f"{', '.join(paths)}")
            else:
                f.write(f"{paths}")
        else:
            f.write("all changes")
        
        f.write("""</code></span>
                </div>
                <div class="meta-item">
                    <span>⏰</span>
                    <span><strong>Generated:</strong> """)
        
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        f.write("""</span>
                </div>
            </div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📊 Summary</h2>
                <div class="summary">
                    <div class="stat-card">
                        <div class="stat-number">""")
        
        f.write(f"{stats['commits']}")
        f.write("""</div>
                        <div class="stat-label">Commits</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">""")
        
        f.write(f"{stats['files']}")
        f.write("""</div>
                        <div class="stat-label">Files Changed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">""")
        
        f.write(f"{stats['lines_added']}")
        f.write("""</div>
                        <div class="stat-label">Lines Added</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">""")
        
        f.write(f"{stats['lines_removed']}")
        f.write("""</div>
                        <div class="stat-label">Lines Removed</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📝 Commits</h2>
                <table class="commits-table">
                    <thead>
                        <tr>
                            <th>Hash</th>
                            <th>Message</th>
                            <th>Author</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>""")
        
        for commit in commits:
            badge_class = commit['type'] if commit['type'] in ['feat', 'fix', 'chore', 'docs', 'refactor'] else 'chore'
            commit_url = f"{repo_url}/commit/{commit['hash']}"
            f.write(f"""
                        <tr>
                            <td><a href="{commit_url}" class="commit-hash" target="_blank">{commit['hash']}</a></td>
                            <td>
                                <span class="badge {badge_class}">{commit['type']}</span>
                                <span class="commit-message">{html.escape(commit['message'])}</span>
                            </td>
                            <td><span class="commit-author">{html.escape(commit['author'])}</span></td>
                            <td><span class="commit-date">{commit['date']}</span></td>
                        </tr>""")
        
        f.write("""
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>📁 Files Changed</h2>
                <div class="files-list">
                    <ul>""")
        
        for file in stats['file_list']:
            f.write(f"<li><code>{html.escape(file)}</code></li>")
        
        f.write("""
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h2>🔍 Detailed Changes</h2>""")
        
        for i, commit in enumerate(commits):
            details = get_commit_details(commit['hash'], paths, repo_dir)
            badge_class = commit['type'] if commit['type'] in ['feat', 'fix', 'chore', 'docs', 'refactor'] else 'chore'
            
            f.write(f"""
                <div class="commit-detail">
                    <div class="commit-header">
                        <div class="commit-title">
                            <a href="{repo_url}/commit/{commit['hash']}" class="commit-hash-large" target="_blank">{commit['hash']}</a>
                            <span class="badge {badge_class}">{commit['type']}</span>
                        </div>
                        <div class="commit-meta">
                            <span>👤 {html.escape(details['author'])}</span>
                            <span>📅 {details['date']}</span>
                            <span>📁 {len(details['files'])} files</span>
                        </div>
                        <div style="margin-top: 8px; color: #e6edf3; font-size: 0.9em;">
                            {html.escape(details['message'])}
                        </div>
                        <div class="commit-actions">
                            <button class="toggle-button secondary" onclick="toggleFiles('files-{i}')">📁 Files ({len(details['files'])})</button>
                            <button class="toggle-button" onclick="toggleDiff('diff-{i}')">🔍 Code Changes</button>
                        </div>""")
            
            if details['files']:
                f.write(f"""
                        <div id="files-{i}" class="collapsible">
                            <div class="files-list">
                                <ul>""")
                for file in details['files']:
                    f.write(f"<li>{html.escape(file)}</li>")
                f.write("</ul></div></div>")
            
            if details['diff']:
                f.write(f"""
                        <div id="diff-{i}" class="collapsible">
                            <div class="diff-container">
                                {format_diff_as_html(details['diff'], commit['hash'], repo_url)}
                            </div>
                        </div>""")
            
            f.write("""
                    </div>
                </div>""")
        
        f.write("""
            </div>
        </div>
    </div>
    
    <button class="scroll-to-top" onclick="scrollToTop()" id="scrollBtn">↑</button>
    
    <script>
        function toggleFiles(id) {
            const element = document.getElementById(id);
            element.classList.toggle('show');
        }
        
        function toggleDiff(id) {
            const element = document.getElementById(id);
            element.classList.toggle('show');
        }
        
        
        function scrollToTop() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
        
        // Show/hide scroll to top button
        window.addEventListener('scroll', function() {
            const scrollBtn = document.getElementById('scrollBtn');
            if (window.pageYOffset > 300) {
                scrollBtn.classList.add('show');
            } else {
                scrollBtn.classList.remove('show');
            }
        });
        
        // Auto-expand first commit for better UX
        document.addEventListener('DOMContentLoaded', function() {
            const firstDiff = document.getElementById('diff-0');
            if (firstDiff) {
                firstDiff.classList.add('show');
            }
            
            // Add keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                if (e.ctrlKey || e.metaKey) {
                    switch(e.key) {
                        case 'k':
                            e.preventDefault();
                            scrollToTop();
                            break;
                        case 'j':
                            e.preventDefault();
                            // Toggle first diff
                            const firstDiff = document.getElementById('diff-0');
                            if (firstDiff) {
                                firstDiff.classList.toggle('show');
                            }
                            break;
                    }
                }
            });
        });
    </script>
</body>
</html>""")
    
    print(f"✓ HTML report generated: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Generate HTML code review reports')
    parser.add_argument('--start', required=True, help='Start commit hash')
    parser.add_argument('--end', required=True, help='End commit hash (use HEAD for latest)')
    parser.add_argument('--path', nargs='*', help='Path(s) to review (optional - if not provided, shows all changes). Can specify multiple paths.')
    parser.add_argument('--output', help='Output file name')
    parser.add_argument('--repo-url', default='https://github.com/dfinity/ic', help='Repository URL for GitHub links')
    parser.add_argument('--repo', required=True, help='Repository URL (e.g., https://github.com/dfinity/ic.git)')
    parser.add_argument('--proposal-id', help='NNS proposal ID to include in the review')
    parser.add_argument('--cache-dir', default='.repo-cache', help='Directory to cache cloned repositories')
    
    args = parser.parse_args()
    
    # Handle external repository (required)
    if not args.repo:
        print("❌ Error: Repository URL is required. Use --repo parameter.")
        sys.exit(1)
    
    print(f"🔍 Using external repository: {args.repo}")
    repo_dir = get_cached_repo(args.repo, args.cache_dir)
    if not repo_dir:
        print("❌ Failed to get cached repository")
        sys.exit(1)
    
    output_file = args.output  # Let the function generate the name if not provided
    generate_html_report(args.start, args.end, args.path, output_file, args.repo_url, args.proposal_id, repo_dir)

if __name__ == '__main__':
    main()
