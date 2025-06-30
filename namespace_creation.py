#!/usr/bin/env python3
import subprocess
import os
import yaml
import getpass
import json

# ─── Step 1: Prompt for Bitbucket credentials ──────────────────────────────────
print("🔐 Enter your Bitbucket credentials:")
username = input("Username: ").strip()
password = getpass.getpass("App Password (not your actual password): ").strip()

# ─── Step 2: Prompt for namespace details ─────────────────────────────────────
print("\n📦 Enter namespace configuration details:")
cluster_name = input("Enter cluster name (e.g. OCP_ECM_CLUSTER_SBX): ").strip()
size         = input("Enter size (e.g. km32xlarge): ").strip()
teamname     = input("Enter team name (e.g. ecm-cp4ba-eval): ").strip()
node_type    = input("Enter node type (e.g. single): ").strip()

# ─── Step 3: Git repository setup ─────────────────────────────────────────────
repo_url    = f"https://{username}:{password}@bitbucket.elevancehealth.com/scm/kyndrylocp/azure-ocp4-ipi-ns.git"
repo_folder = "azure-ocp4-ipi-ns"
branch_name = "azure-azurerm-caas01-ocp4-sbx-eastus"
file_path   = "group-labeling/group-label.yaml"

if not os.path.exists(repo_folder):
    subprocess.check_call(["git", "clone", repo_url])
os.chdir(repo_folder)
subprocess.check_call(["git", "fetch", "origin"])
subprocess.check_call(["git", "checkout", "-B", branch_name, f"origin/{branch_name}"])

# ─── Step 4: Load existing content ────────────────────────────────────────────
if not os.path.exists(file_path):
    raise FileNotFoundError(f"File not found: {file_path}")

with open(file_path, "r") as f:
    loaded = yaml.safe_load(f)

# Determine format
if isinstance(loaded, dict) and "data" in loaded and "group-labels.json" in loaded["data"]:
    # ─ Wrapped ConfigMap case ─
    is_wrapped    = True
    configmap     = loaded
    json_str      = configmap["data"]["group-labels.json"]
    labels_list   = json.loads(json_str)
elif isinstance(loaded, list):
    # ─ Bare list case ─
    is_wrapped  = False
    labels_list = loaded
else:
    raise ValueError("Unrecognized file format: expecting either a ConfigMap dict or a bare list")

# ─── Step 5: Append new entry ─────────────────────────────────────────────────
new_entry = {
    "name": cluster_name,
    "labels": [
        {"key": "size",     "value": size},
        {"key": "teamname", "value": teamname},
        {"key": "type",     "value": node_type}
    ]
}
labels_list.append(new_entry)

# ─── Step 6: Write back in original style ────────────────────────────────────
with open(file_path, "w") as f:
    if is_wrapped:
        # re-embed JSON string in the ConfigMap
        configmap["data"]["group-labels.json"] = json.dumps(labels_list, indent=4)
        yaml.dump(configmap, f, default_flow_style=False)
    else:
        # dump the bare list directly
        yaml.dump(labels_list, f, default_flow_style=False)

# ─── Step 7: Commit & Push ───────────────────────────────────────────────────
subprocess.check_call(["git", "add", file_path])
subprocess.check_call(["git", "commit", "-m", f"Added namespace config for {cluster_name}"])
subprocess.check_call(["git", "push", "origin", branch_name])

print(f"\n✅ Successfully appended '{cluster_name}' and pushed to {branch_name}!")
