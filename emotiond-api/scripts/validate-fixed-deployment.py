#!/usr/bin/env python3
"""
Validate fixed deployment files
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
            parsed = yaml.safe_load(content)
            
            # Validate required fields based on kind
            if parsed:
                kind = parsed.get('kind', '').lower()
                
                if kind == 'deployment':
                    if 'spec' not in parsed:
                        issues.append("Missing 'spec' in Deployment")
                    elif 'template' not in parsed.get('spec', {}):
                        issues.append("Missing 'template' in Deployment spec")
                        
                elif kind == 'service':
                    if 'spec' not in parsed:
                        issues.append("Missing 'spec' in Service")
                        
                elif kind == 'ingress':
                    if 'spec' not in parsed:
                        issues.append("Missing 'spec' in Ingress")
                        
                elif kind == 'secret':
                    if 'data' not in parsed and 'stringData' not in parsed:
                        issues.append("Missing 'data' or 'stringData' in Secret")
                        
        except yaml.YAMLError as e:
            issues.append(f"YAML parsing error: {str(e)}")
            
    except Exception as e:
        issues.append(f"File read error: {str(e)}")
        
    return issues

def main():
    """Main validation function"""
    fixed_dir = "/home/moonlight/.openclaw/workspace/emotiond-api/deploy/fixed"
    
    print("=== Fixed Deployment Files Validation ===\n")
    
    if not os.path.exists(fixed_dir):
        print(f"❌ Directory not found: {fixed_dir}")
        return 1
    
    yaml_files = [f for f in os.listdir(fixed_dir) if f.endswith(('.yaml', '.yml'))]
    
    if not yaml_files:
        print(f"❌ No YAML files found in {fixed_dir}")
        return 1
    
    all_valid = True
    for yaml_file in sorted(yaml_files):
        file_path = os.path.join(fixed_dir, yaml_file)
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
        print("✅ All fixed deployment files are valid")
    else:
        print("❌ Some fixed deployment files have issues")
        
    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())