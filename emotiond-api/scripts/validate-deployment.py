#!/usr/bin/env python3
"""
Validate and fix deployment files
"""
import yaml
import os
import sys

def validate_yaml_file(file_path):
    """Validate a YAML file and return issues"""
    issues = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Check for multiple documents
        if content.count('---') > 1:
            issues.append("Multiple documents found - should be split into separate files")
            
        # Try to parse as single document
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            issues.append(f"YAML parsing error: {str(e)}")
            
    except Exception as e:
        issues.append(f"File read error: {str(e)}")
        
    return issues

def main():
    """Main validation function"""
    deployment_dir = "/home/moonlight/.openclaw/workspace/emotiond-api/deploy"
    
    print("=== Deployment Files Validation ===\n")
    
    yaml_files = [f for f in os.listdir(deployment_dir) if f.endswith(('.yaml', '.yml'))]
    
    all_valid = True
    for yaml_file in yaml_files:
        file_path = os.path.join(deployment_dir, yaml_file)
        issues = validate_yaml_file(file_path)
        
        if issues:
            print(f"❌ {yaml_file}:")
            for issue in issues:
                print(f"   - {issue}")
            all_valid = False
        else:
            print(f"✅ {yaml_file}: Valid")
    
    print(f"\n=== Summary ===")
    if all_valid:
        print("✅ All deployment files are valid")
    else:
        print("❌ Some deployment files have issues")
        print("\nRecommendation: Split multi-document YAML files into separate files")
        
    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())