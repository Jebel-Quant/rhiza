import json
import sys
import os
import ast
import subprocess
from pathlib import Path

def get_function_source(file_path, node):
    """Extracts the source code of the function from the file."""
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
        # lineno is 1-based, list index is 0-based
        return "".join(lines[node.lineno - 1 : node.end_lineno])
    except Exception:
        return None

def find_function_node(file_path, line_number):
    """Finds the function node containing the given line number."""
    try:
        with open(file_path, "r") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except Exception:
        return None

    target_node = None
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                if node.lineno <= line_number <= node.end_lineno:
                    target_node = node
    
    return target_node

def trigger_gh_agent(prompt):
    """Triggers the GitHub Agent Task."""
    print("🤖 Triggering GitHub Agent Task...")
    try:
        # We use the custom agent defined in .github/agents/coverage-agent.md
        # We pass the prompt via stdin
        process = subprocess.Popen(
            ["gh", "agent-task", "create", "--custom-agent", "coverage-agent", "-F", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=prompt)
        
        if process.returncode != 0:
            if "specified custom agent not found" in stderr:
                print(f"❌ Failed to trigger agent: Custom agent 'coverage-agent' not found.")
                print("👉 Please ensure you have pushed the file '.github/agents/coverage-agent.md' to your remote repository.")
                print("   GitHub Agent Tasks require the agent definition to be present on GitHub.")
            else:
                print(f"❌ Failed to trigger agent: {stderr}")
        else:
            print(f"✅ Agent task started successfully!\n{stdout}")
            
    except FileNotFoundError:
        print("❌ 'gh' CLI not found. Ensure GitHub CLI is installed and available in PATH.")

def main():
    # Search for coverage.json in common locations
    possible_paths = [
        Path("coverage.json"),
        Path("_tests/coverage.json"),
        Path("tests/coverage.json"),
        Path(".coverage.json")
    ]
    
    coverage_file = None
    for path in possible_paths:
        if path.exists():
            coverage_file = path
            break
            
    if not coverage_file:
        # Fallback: try to find it anywhere
        try:
            found = list(Path(".").rglob("coverage.json"))
            if found:
                coverage_file = found[0]
        except Exception:
            pass

    if not coverage_file or not coverage_file.exists():
        print("❌ No coverage data found.")
        return

    print(f"📂 Using coverage file: {coverage_file}")

    try:
        with open(coverage_file, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("❌ Invalid coverage JSON.")
        return

    totals = data.get("totals", {})
    covered_lines = totals.get("covered_lines", 0)
    num_statements = totals.get("num_statements", 0)
    
    if num_statements == 0:
        percent_covered = 100.0
    else:
        percent_covered = (covered_lines / num_statements) * 100

    print(f"📊 Total Coverage: {percent_covered:.2f}%")

    if percent_covered >= 100:
        print("✅ Coverage is 100%. Great job!")
        sys.exit(0)

    # Prepare prompt for the agent
    agent_prompt = []
    agent_prompt.append(f"The current code coverage is {percent_covered:.2f}%, which is below the target of 100%.")
    agent_prompt.append("Please write pytest tests to cover the following missing lines:\n")

    files = data.get("files", {})
    has_missing = False
    
    for filename, file_data in files.items():
        missing_lines = file_data.get("missing_lines", [])
        if not missing_lines:
            continue
        
        has_missing = True
        agent_prompt.append(f"File: {filename}")
        agent_prompt.append(f"Missing lines: {', '.join(map(str, missing_lines))}")
        
        # Provide context about the functions
        if os.path.exists(filename):
            functions_to_test = {}
            for line in missing_lines:
                node = find_function_node(filename, line)
                if node and node.name not in functions_to_test:
                    functions_to_test[node.name] = get_function_source(filename, node)
            
            if functions_to_test:
                agent_prompt.append("Relevant functions source code:")
                for func_name, func_source in functions_to_test.items():
                    agent_prompt.append(f"```python\n# Function: {func_name}\n{func_source}\n```")
        
        agent_prompt.append("-" * 20)

    if has_missing:
        full_prompt = "\n".join(agent_prompt)
        # Trigger the agent
        trigger_gh_agent(full_prompt)
        
        # Fail the build so the user knows coverage is low (and agent is working on it)
        sys.exit(1)

if __name__ == "__main__":
    main()
