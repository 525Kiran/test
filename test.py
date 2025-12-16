import subprocess
import sys
import os

try:
    from ruamel.yaml import YAML
except ImportError:
    print("❌ Missing required library: ruamel.yaml")
    print("👉 Please run: pip install ruamel.yaml")
    sys.exit(1)

# --- ⚙️ CONFIGURATION ---
REPO_CONFIG = {
    "KP": {
        "path": "C:/Users/test/OneDrive/Desktop/Git_Test/script_test_kp",  # <--- UPDATE THIS
        "base_branch": "master",
        "identifier": "account_name"
    },
    "KM": {
        "path": "C:/Users/test/OneDrive/Desktop/Git_Test/script_test", # <--- UPDATE THIS
        "base_branch": "main",
        "identifier": "account_number"
    }
}

IGNORED_FOLDERS = {'.github', '.git'}

def run_command(command, suppress_output=False):
    """Runs a shell command and checks for errors."""
    try:
        if suppress_output:
            subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError:
        print(f"\n❌ Error executing: {command}")
        sys.exit(1)

def get_yaml_instance():
    """Configures ruamel.yaml to preserve formatting/comments."""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml

def find_yaml_files():
    """Recursively finds .yml files but intelligently SKIPS ignored folders."""
    yaml_files = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in IGNORED_FOLDERS]
        for file in files:
            if file.endswith(".yml") or file.endswith(".yaml"):
                yaml_files.append(os.path.join(root, file))
    return yaml_files

def process_addition(target_id_list, role_list, email_list, id_key):
    """
    Adds MULTIPLE users to MULTIPLE roles in MULTIPLE Accounts.
    """
    yml_files = find_yaml_files()
    yaml = get_yaml_instance()
    modified_files = set() # Use a set to avoid duplicate file entries
    
    # Track which accounts we have successfully found and updated
    found_accounts = set()

    print(f"🔍 [ADD] Scanning for {len(target_id_list)} accounts...")

    for file_path in yml_files:
        with open(file_path, 'r') as f:
            try:
                data = yaml.load(f)
            except Exception:
                continue

        if not data or 'accounts' not in data:
            continue

        file_modified = False

        for account in data['accounts']:
            current_acc_id = str(account.get(id_key))
            
            # Check if this account is in our target list
            if current_acc_id in target_id_list:
                found_accounts.add(current_acc_id)
                
                # Iterate through every requested role
                for role_name in role_list:
                    role_name = role_name.strip()
                    if not role_name: continue

                    if 'roles' in account and role_name in account['roles']:
                        current_users = account['roles'][role_name]
                        
                        # Iterate through every requested email
                        for email in email_list:
                            email = email.strip()
                            if not email: continue

                            if email in current_users:
                                print(f"⚠️  User {email} exists in {role_name} @ {current_acc_id} (Skipping)")
                            else:
                                current_users.append(email)
                                file_modified = True
                                print(f"✅ Added {email} to {role_name} @ {current_acc_id}")
                    else:
                        print(f"❌ Role '{role_name}' does not exist in {current_acc_id}. Skipping.")

        if file_modified:
            with open(file_path, 'w') as f:
                yaml.dump(data, f)
            modified_files.add(file_path)

    # Final Report on missing accounts
    missing_accounts = set(target_id_list) - found_accounts
    if missing_accounts:
        print("\n⚠️  WARNING: The following accounts were NOT found in any YAML file:")
        for acc in missing_accounts:
            print(f"   - {acc}")

    return list(modified_files)

def process_global_removal(email_list):
    """
    Removes MULTIPLE users from ALL roles in ALL accounts across ALL files.
    """
    yml_files = find_yaml_files()
    yaml = get_yaml_instance()
    modified_files = set()
    
    print(f"🔍 [REMOVE] Searching globally for: {', '.join(email_list)}...")
    
    total_removed_count = 0

    for file_path in yml_files:
        with open(file_path, 'r') as f:
            try:
                data = yaml.load(f)
            except Exception:
                continue

        if not data or 'accounts' not in data:
            continue

        file_dirty = False

        for account in data['accounts']:
            if 'roles' not in account:
                continue
            
            for r_name, user_list in account['roles'].items():
                for email in email_list:
                    email = email.strip()
                    if email in user_list:
                        user_list.remove(email)
                        file_dirty = True
                        total_removed_count += 1
                        
                        acc_label = account.get('account_name') or account.get('account_number') or "Unknown"
                        print(f"   🗑️  Removed {email} | Account: {acc_label} | Role: {r_name}")

        if file_dirty:
            with open(file_path, 'w') as f:
                yaml.dump(data, f)
            modified_files.add(file_path)

    if total_removed_count == 0:
        print("⚠️ No matching users were found in any file.")

    return list(modified_files)

def main():
    print("--- 🔐 Multi-Repo Access Manager (Full Bulk Support) ---")

    # 1. Environment Selection
    env_choice = input("Select Environment (KP / KM): ").strip().upper()
    if env_choice not in REPO_CONFIG:
        print("❌ Invalid environment.")
        sys.exit(1)
    
    config = REPO_CONFIG[env_choice]
    
    if not os.path.exists(config["path"]):
        print(f"❌ Error: Path not found: {config['path']}")
        sys.exit(1)

    # 2. Determine Action
    action = input("Action (add/remove): ").strip().lower()
    if action not in ['add', 'remove']:
        print("❌ Invalid action.")
        sys.exit(1)

    # 3. Gather Inputs
    user_ref_input = input("Enter Reference ID (e.g. Ticket-123): ").strip()
    
    # Bulk Emails
    email_input_raw = input("User Emails (comma separated): ").strip()
    email_list = [e.strip() for e in email_input_raw.split(',') if e.strip()]
    
    target_id_list = []
    role_list = []

    if action == 'add':
        if env_choice == "KP":
            raw_accs = input("Target Account NAMES (comma separated): ").strip()
        else:
            raw_accs = input("Target Account NUMBERS (comma separated): ").strip()
        
        target_id_list = [a.strip() for a in raw_accs.split(',') if a.strip()]

        # Bulk Roles
        role_input_raw = input("Target Roles (comma separated): ").strip()
        role_list = [r.strip() for r in role_input_raw.split(',') if r.strip()]

    # 4. SWITCH REPO CONTEXT
    print(f"\n--- 📂 Switching to {env_choice} Repo ---")
    os.chdir(config["path"])

    # 5. Git Setup
    base_branch = config["base_branch"]
    print(f"\n--- 🔄 Preparing Git (Base: {base_branch}) ---")
    
    run_command(f"git checkout {base_branch}")
    run_command(f"git pull origin {base_branch}")

    # Branch & Commit Logic
    if action == 'add':
        branch_name = f"access/{user_ref_input}"
        commit_msg = f"add access: add user {user_ref_input}"
    else:
        branch_name = f"chore/{user_ref_input}"
        commit_msg = f"chore: remove user {user_ref_input}"

    try:
        run_command(f"git checkout -b {branch_name}", suppress_output=True)
    except SystemExit:
        print(f"ℹ️ Branch {branch_name} already exists. Switching to it.")
        run_command(f"git checkout {branch_name}")

    # 6. Process YAML
    print("\n--- 🛠 Processing Files ---")
    modified_files = []
    
    if action == 'add':
        modified_files = process_addition(target_id_list, role_list, email_list, config["identifier"])
    else:
        modified_files = process_global_removal(email_list)

    if not modified_files:
        print("✅ No changes were needed.")
        run_command(f"git checkout {base_branch}")
        run_command(f"git branch -d {branch_name}")
        sys.exit(0)

    # 7. Commit and Push
    print(f"\n--- 💾 Saving Changes ({len(modified_files)} files) ---")
    for f in modified_files:
        run_command(f"git add {f}")
    
    try:
        run_command(f'git commit -S -m "{commit_msg}"')
    except SystemExit:
         print("⚠️ GPG signing failed. Committing without signing...")
         run_command(f'git commit -m "{commit_msg}"')

    run_command(f"git push -u origin {branch_name}")

    # 8. Success Message
    print("\n" + "="*50)
    print("✅ SUCCESS! Changes pushed.")
    print(f"👉 Branch: {branch_name}")
    print(f"👉 Commit: {commit_msg}")
    print(f"👉 PR URL: .../{env_choice}-repo/pull/new/{branch_name}")
    print("="*50)

if __name__ == "__main__":
    main()
