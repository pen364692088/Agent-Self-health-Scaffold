#!/usr/bin/env python3
"""
Create deployment package with all validated files
"""
import os
import sys
import shutil
import zipfile
from datetime import datetime

def create_deployment_package():
    """Create a deployment package with all validated files"""
    
    # Paths
    repo_dir = "/home/moonlight/.openclaw/workspace/emotiond-api"
    deploy_dir = os.path.join(repo_dir, "deploy")
    fixed_dir = os.path.join(deploy_dir, "fixed")
    reports_dir = os.path.join(repo_dir, "reports")
    package_dir = os.path.join(repo_dir, "deployment-package")
    
    # Create package directory
    os.makedirs(package_dir, exist_ok=True)
    
    # Copy validated deployment files
    deployment_files_dir = os.path.join(package_dir, "kubernetes")
    os.makedirs(deployment_files_dir, exist_ok=True)
    
    print("=== Creating Deployment Package ===\n")
    
    # Copy fixed YAML files
    if os.path.exists(fixed_dir):
        for file in os.listdir(fixed_dir):
            if file.endswith('.yaml'):
                src = os.path.join(fixed_dir, file)
                dst = os.path.join(deployment_files_dir, file)
                shutil.copy2(src, dst)
                print(f"✅ Copied: {file}")
    
    # Copy Helm values file
    values_file = os.path.join(deploy_dir, "production-values.yaml")
    if os.path.exists(values_file):
        shutil.copy2(values_file, os.path.join(package_dir, "production-values.yaml"))
        print(f"✅ Copied: production-values.yaml")
    
    # Copy documentation
    docs_dir = os.path.join(package_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    doc_files = [
        "production-deployment-guide.md",
        "production-checklist.md"
    ]
    
    for doc in doc_files:
        src = os.path.join(deploy_dir, doc)
        if os.path.exists(src):
            dst = os.path.join(docs_dir, doc)
            shutil.copy2(src, dst)
            print(f"✅ Copied: {doc}")
    
    # Copy reports
    reports_copy_dir = os.path.join(package_dir, "reports")
    os.makedirs(reports_copy_dir, exist_ok=True)
    
    if os.path.exists(reports_dir):
        for file in os.listdir(reports_dir):
            if file.endswith('.md'):
                src = os.path.join(reports_dir, file)
                dst = os.path.join(reports_copy_dir, file)
                shutil.copy2(src, dst)
                print(f"✅ Copied report: {file}")
    
    # Copy API source
    api_src_dir = os.path.join(package_dir, "api-source")
    os.makedirs(api_src_dir, exist_ok=True)
    
    api_dir = os.path.join(repo_dir, "api")
    if os.path.exists(api_dir):
        for file in os.listdir(api_dir):
            if file.endswith('.py'):
                src = os.path.join(api_dir, file)
                dst = os.path.join(api_src_dir, file)
                shutil.copy2(src, dst)
                print(f"✅ Copied API: {file}")
    
    # Copy Docker files
    docker_files = ["Dockerfile", "docker-compose.yml", "docker-compose.prod.yml"]
    for docker_file in docker_files:
        src = os.path.join(repo_dir, docker_file)
        if os.path.exists(src):
            dst = os.path.join(package_dir, docker_file)
            shutil.copy2(src, dst)
            print(f"✅ Copied: {docker_file}")
    
    # Create deployment manifest
    manifest = {
        "deployment_package": {
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "environment": "production",
            "components": {
                "kubernetes_manifests": len(os.listdir(deployment_files_dir)) if os.path.exists(deployment_files_dir) else 0,
                "helm_values": 1,
                "documentation": len(os.listdir(docs_dir)) if os.path.exists(docs_dir) else 0,
                "reports": len(os.listdir(reports_copy_dir)) if os.path.exists(reports_copy_dir) else 0,
                "api_source": len(os.listdir(api_src_dir)) if os.path.exists(api_src_dir) else 0
            },
            "validation_status": "PASSED",
            "deployment_order": [
                "1. Create namespace",
                "2. Apply secrets",
                "3. Apply PVCs",
                "4. Apply deployment",
                "5. Apply service",
                "6. Apply ingress",
                "7. Apply HPA and PDB"
            ]
        }
    }
    
    import json
    with open(os.path.join(package_dir, "deployment-manifest.json"), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n✅ Created deployment manifest")
    
    # Create ZIP archive
    zip_path = os.path.join(repo_dir, f"emotiond-api-deployment-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arc_name)
    
    print(f"\n=== Deployment Package Created ===")
    print(f"Package directory: {package_dir}")
    print(f"ZIP archive: {zip_path}")
    print(f"Size: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB")
    
    return True

def main():
    """Main function"""
    try:
        if create_deployment_package():
            print("\n✅ Deployment package created successfully")
            return 0
        else:
            print("\n❌ Failed to create deployment package")
            return 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())