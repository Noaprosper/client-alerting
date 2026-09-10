#!/usr/bin/env python3
"""
Validation script for Alert-Client project configuration.
Checks all configuration files and API endpoints.
"""

import os
import sys
import json

def check_file_exists(path, description):
    """Check if a file exists"""
    if os.path.exists(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description} MISSING: {path}")
        return False

def check_file_content(path, search_text, description):
    """Check if file contains specific text"""
    try:
        with open(path, 'r') as f:
            content = f.read()
            if search_text in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description} - Text not found in {path}")
                return False
    except Exception as e:
        print(f"❌ Error reading {path}: {e}")
        return False

def validate_env_file(path):
    """Validate .env file has correct configuration"""
    try:
        with open(path, 'r') as f:
            content = f.read()
            
        checks = {
            'CONSOLE_API_URL with /dashboard': '/dashboard' in content,
            'SCALEWAY_API_KEY defined': 'SCALEWAY_API_KEY=' in content and not content.split('SCALEWAY_API_KEY=')[1].split('\n')[0].strip().startswith('#'),
            'INCIDENT_API_URL defined': 'INCIDENT_API_URL=' in content,
            'DATABASE_URL defined': 'DATABASE_URL=' in content,
        }
        
        all_ok = True
        for check, result in checks.items():
            if result:
                print(f"  ✅ {check}")
            else:
                print(f"  ⚠️  {check} - Not configured or incorrect")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("=" * 80)
    print("Alert-Client Project - Configuration Validation")
    print("=" * 80)
    print()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check configuration files
    print("📁 Configuration Files:")
    print("-" * 80)
    check_file_exists(f"{base_dir}/.env", "Environment file")
    check_file_exists(f"{base_dir}/.env.example", "Environment example")
    print()
    
    # Check Python files
    print("🐍 Python Files:")
    print("-" * 80)
    check_file_exists(f"{base_dir}/cron-match-incidents/main.py", "Main cron script")
    check_file_exists(f"{base_dir}/cron-match-incidents/test_api.py", "API test script")
    check_file_exists(f"{base_dir}/database/import_csv.py", "CSV import script")
    print()
    
    # Check documentation
    print("📚 Documentation Files:")
    print("-" * 80)
    check_file_exists(f"{base_dir}/README.md", "README")
    check_file_exists(f"{base_dir}/INSTALL.md", "Installation guide")
    check_file_exists(f"{base_dir}/QUICKSTART.md", "Quick start guide")
    check_file_exists(f"{base_dir}/ARCHITECTURE.md", "Architecture doc")
    check_file_exists(f"{base_dir}/API_ENDPOINT_UPDATE.md", "API update log")
    check_file_exists(f"{base_dir}/CONFIGURATION_VERIFIED.md", "Configuration summary")
    print()
    
    # Check dashboard files
    print("🖥️  Dashboard Files:")
    print("-" * 80)
    check_file_exists(f"{base_dir}/dashboard/.env.local.example", "Dashboard env example")
    check_file_exists(f"{base_dir}/dashboard/package.json", "Dashboard package.json")
    check_file_exists(f"{base_dir}/dashboard/app/page.tsx", "Dashboard main page")
    print()
    
    # Check database files
    print("🗄️  Database Files:")
    print("-" * 80)
    check_file_exists(f"{base_dir}/database/schema.sql", "Database schema")
    check_file_exists(f"{base_dir}/database/seed_mappings.sql", "Seed mappings")
    print()
    
    # Validate .env file content
    print("🔍 Validating .env Configuration:")
    print("-" * 80)
    env_valid = validate_env_file(f"{base_dir}/.env")
    print()
    
    # Check main.py has correct endpoint
    print("🔍 Validating main.py API Endpoint:")
    print("-" * 80)
    check_file_content(
        f"{base_dir}/cron-match-incidents/main.py",
        "https://api.scaleway.com/resource-private/v1alpha1/dashboard",
        "main.py uses /dashboard endpoint"
    )
    print()
    
    # Check documentation consistency
    print("🔍 Validating Documentation Consistency:")
    print("-" * 80)
    docs_to_check = [
        f"{base_dir}/README.md",
        f"{base_dir}/INSTALL.md",
        f"{base_dir}/QUICKSTART.md",
        f"{base_dir}/ARCHITECTURE.md",
    ]
    
    all_docs_ok = True
    for doc_path in docs_to_check:
        if check_file_content(doc_path, "/dashboard", f"{os.path.basename(doc_path)} mentions /dashboard"):
            pass
        else:
            all_docs_ok = False
    print()
    
    # Summary
    print("=" * 80)
    print("Validation Summary")
    print("=" * 80)
    
    if env_valid and all_docs_ok:
        print("✅ All critical configurations are VALID")
        print("\nNext steps:")
        print("1. Edit .env file with your real SCALEWAY_API_KEY and DATABASE_URL")
        print("2. Edit database/organizations.csv with your organization IDs")
        print("3. Run: cd cron-match-incidents && python test_api.py YOUR_ORG_ID")
        print("4. Import organizations: python database/import_csv.py organizations.csv")
        print("5. Test cron job: python main.py")
        return 0
    else:
        print("⚠️  Some configurations need attention")
        print("\nPlease review the errors above and fix them.")
        return 1

if __name__ == '__main__':
    sys.exit(main())