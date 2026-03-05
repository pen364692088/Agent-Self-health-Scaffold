#!/usr/bin/env python3
"""
Fix multi-document YAML files by splitting them into separate files
"""
import yaml
import os
import sys

def split_yaml_file(input_file, output_dir):
    """Split a multi-document YAML file into separate files"""
    
    try:
        with open(input_file, 'r') as f:
            content = f.read()
        
        # Split documents
        documents = content.split('---')
        
        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)
        
        # Process each document
        for i, doc in enumerate(documents):
            doc = doc.strip()
            if not doc:
                continue
                
            try:
                parsed = yaml.safe_load(doc)
                
                # Generate filename based on kind
                kind = parsed.get('kind', 'resource').lower()
                name = parsed.get('metadata', {}).get('name', f'resource-{i}')
                
                filename = f"{name}.yaml"
                output_path = os.path.join(output_dir, filename)
                
                # Write single document
                with open(output_path, 'w') as f:
                    f.write(f"# Auto-generated from {os.path.basename(input_file)}\n")
                    f.write(f"# Document {i+1}: {parsed.get('kind', 'Unknown')}\n\n")
                    f.write(doc)
                    f.write('\n')
                    
                print(f"✅ Created: {output_path}")
                
            except Exception as e:
                print(f"❌ Error processing document {i}: {str(e)}")
                
    except Exception as e:
        print(f"❌ Error reading {input_file}: {str(e)}")
        return False
        
    return True

def fix_values_syntax(file_path):
    """Fix YAML syntax issues in values files"""
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Fix common syntax issues
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Check for malformed boolean values
            if 'allowPrivilegeEscalation: false' in line:
                line = line.replace('allowPrivilegeEscalation: false', 'allowPrivilegeEscalation: false')
            
            # Ensure proper indentation
            if line.strip() and not line.startswith(' ') and ':' in line and not line.startswith('#'):
                # This might be a top-level key with incorrect indentation
                if not line.startswith('apiVersion') and not line.startswith('kind'):
                    # Likely needs proper indentation
                    line = '  ' + line
            
            fixed_lines.append(line)
        
        # Write fixed content
        with open(file_path, 'w') as f:
            f.write('\n'.join(fixed_lines))
            
        print(f"✅ Fixed syntax in: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {str(e)}")
        return False

def main():
    """Main fix function"""
    deployment_dir = "/home/moonlight/.openclaw/workspace/emotiond-api/deploy"
    fixed_dir = "/home/moonlight/.openclaw/workspace/emotiond-api/deploy/fixed"
    
    print("=== Fixing Deployment Files ===\n")
    
    # Fix values file first
    values_file = os.path.join(deployment_dir, "production-values.yaml")
    if os.path.exists(values_file):
        fix_values_syntax(values_file)
    
    # Split multi-document files
    multi_files = ["production-deployment.yaml", "production-secrets.yaml"]
    
    for filename in multi_files:
        input_path = os.path.join(deployment_dir, filename)
        if os.path.exists(input_path):
            print(f"\nProcessing {filename}...")
            if split_yaml_file(input_path, fixed_dir):
                print(f"✅ Split {filename} into separate files")
            else:
                print(f"❌ Failed to split {filename}")
    
    print(f"\n=== Fixed Files Location ===")
    print(f"Fixed deployment files: {fixed_dir}")
    print(f"Original files preserved in: {deployment_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())