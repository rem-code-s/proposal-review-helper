#!/usr/bin/env python3
"""
Generate beautiful markdown code review reports with side-by-side comparisons
"""

import subprocess
import sys
import os
import re
from datetime import datetime
import argparse
import tempfile
import shutil

def clone_external_repo(repo_url):
    """Clone external repository to temporary directory"""
    temp_dir = tempfile.mkdtemp(prefix='markdown_review_')
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
                        import re
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
                commits.append({
                    'hash': parts[0],
                    'message': parts[1],
                    'author': parts[2],
                    'date': parts[3]
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

def generate_markdown_report(start_commit, end_commit, paths=None, output_file=None, proposal_id=None, repo_dir=None, repo_url=None):
    """Generate a comprehensive markdown review report"""
    
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
        output_file = f"generated/{folder_name}/{folder_name}.md"
    
    print(f"Generating markdown report for {start_commit}..{end_commit}")
    
    # Get statistics
    stats = get_commit_stats(start_commit, end_commit, paths, repo_dir)
    commits = get_commits(start_commit, end_commit, paths, repo_dir)
    
    with open(output_file, 'w') as f:
        # Header
        f.write("# 📋 Code Review Report\n\n")
        f.write(f"**Commit Range:** `{start_commit}` → `{end_commit}`\n")
        if paths:
            if isinstance(paths, list):
                f.write(f"**Paths:** `{'`, `'.join(paths)}`\n")
            else:
                f.write(f"**Path:** `{paths}`\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary
        f.write("## 📊 Summary\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| **Total Commits** | {stats['commits']} |\n")
        f.write(f"| **Files Changed** | {stats['files']} |\n")
        f.write(f"| **Lines Added** | {stats['lines_added']} |\n")
        f.write(f"| **Lines Removed** | {stats['lines_removed']} |\n\n")
        
        # Commits table
        f.write("## 📝 Commits\n\n")
        f.write("| Hash | Message | Author | Date |\n")
        f.write("|------|---------|--------|------|\n")
        for commit in commits:
            f.write(f"| `{commit['hash']}` | {commit['message']} | {commit['author']} | {commit['date']} |\n")
        f.write("\n")
        
        # Files changed
        f.write("## 📁 Files Changed\n\n")
        for file in stats['file_list']:
            f.write(f"- `{file}`\n")
        f.write("\n")
        
        # Detailed changes
        f.write("## 🔍 Detailed Changes\n\n")
        for commit in commits:
            details = get_commit_details(commit['hash'], paths, repo_dir)
            
            f.write(f"### Commit `{commit['hash']}`\n\n")
            f.write(f"**Author:** {details['author']}  \n")
            f.write(f"**Date:** {details['date']}  \n")
            f.write(f"**Message:** {details['message']}\n\n")
            
            if details['files']:
                f.write("**Files Changed:**\n")
                for file in details['files']:
                    f.write(f"- `{file}`\n")
                f.write("\n")
            
            if details['diff']:
                f.write("**Code Changes:**\n\n")
                f.write("```diff\n")
                f.write(details['diff'])
                f.write("\n```\n\n")
            
            f.write("---\n\n")
    
    print(f"✓ Markdown report generated: {output_file}")
    return output_file

def generate_summary_report(start_commit, end_commit, paths=None, output_file=None):
    """Generate a concise summary report"""
    
    if output_file is None:
        # Generate filename with shorthand and date
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        if paths:
            if isinstance(paths, list):
                path_short = '-'.join([p.replace('/', '-').replace('rs-', '').replace('sns-governance', 'sns-gov').replace('nns-governance', 'nns-gov') for p in paths])
            else:
                path_short = paths.replace('/', '-').replace('rs-', '').replace('sns-governance', 'sns-gov').replace('nns-governance', 'nns-gov')
        else:
            path_short = 'all-changes'
        commit_short = f"{start_commit[:8]}-{end_commit[:8]}"
        output_file = f"generated/{date_str}-summary-{path_short}-{commit_short}.md"
    
    print(f"Generating summary report for {start_commit}..{end_commit}")
    
    stats = get_commit_stats(start_commit, end_commit, paths, repo_dir)
    commits = get_commits(start_commit, end_commit, paths, repo_dir)
    
    with open(output_file, 'w') as f:
        f.write("# 📊 Code Review Summary\n\n")
        f.write(f"**Range:** `{start_commit}` → `{end_commit}`\n")
        if paths:
            if isinstance(paths, list):
                f.write(f"**Paths:** `{'`, `'.join(paths)}`\n")
            else:
                f.write(f"**Path:** `{paths}`\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 📈 Overview\n\n")
        f.write("| Metric | Count |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Commits | {stats['commits']} |\n")
        f.write(f"| Files | {stats['files']} |\n")
        f.write(f"| Lines Added | {stats['lines_added']} |\n")
        f.write(f"| Lines Removed | {stats['lines_removed']} |\n\n")
        
        f.write("## 📝 Commits\n\n")
        for commit in commits:
            f.write(f"- `{commit['hash']}` **{commit['message']}** _({commit['author']}, {commit['date']})_\n")
        f.write("\n")
        
        f.write("## 📁 Files Changed\n\n")
        for file in stats['file_list']:
            f.write(f"- `{file}`\n")
        f.write("\n")
        
        # Get overall diff stats
        if paths:
            if isinstance(paths, list):
                path_filter = " -- " + " ".join(paths)
            else:
                path_filter = f" -- {paths}"
        else:
            path_filter = ""
        diff_stats = run_git_command(f"git diff --stat {start_commit}..{end_commit}{path_filter}", repo_dir)
        if diff_stats:
            f.write("## 🔍 Change Statistics\n\n")
            f.write("```\n")
            f.write(diff_stats)
            f.write("\n```\n")
    
    print(f"✓ Summary report generated: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Generate markdown code review reports')
    parser.add_argument('--start', required=True, help='Start commit hash')
    parser.add_argument('--end', required=True, help='End commit hash (use HEAD for latest)')
    parser.add_argument('--path', nargs='*', help='Path(s) to review (optional - if not provided, shows all changes). Can specify multiple paths.')
    parser.add_argument('--type', choices=['full', 'summary'], default='full', help='Report type')
    parser.add_argument('--output', help='Output file name')
    parser.add_argument('--repo', required=True, help='Repository URL (e.g., https://github.com/dfinity/ic.git)')
    parser.add_argument('--proposal-id', help='NNS proposal ID to include in the review')
    parser.add_argument('--cache-dir', default='.repo-cache', help='Directory to cache cloned repositories')
    parser.add_argument('--repo-url', default='https://github.com/dfinity/ic', help='Repository URL for GitHub links')
    
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
    if args.type == 'full':
        generate_markdown_report(args.start, args.end, args.path, output_file, args.proposal_id, repo_dir, args.repo_url)
    else:
        generate_summary_report(args.start, args.end, args.path, output_file, repo_dir)

if __name__ == '__main__':
    main()
