#!/usr/bin/env python3
"""
Script pour importer les organisations depuis un fichier CSV
"""

import csv
import os
import psycopg2
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', '')

def import_organizations(csv_path='organizations.csv'):
    """Importer les organisations depuis un CSV vers la base de données"""
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL non configurée")
        return False
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Lire et importer le CSV
        print(f"📄 Lecture du fichier {csv_path}...")
        
        org_ids = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                org_id = row.get('org_id', '').strip()
                name = row.get('name', '').strip()
                
                if not org_id:
                    print(f"⚠️  Ligne ignorée (org_id vide): {row}")
                    continue
                
                org_ids.append(org_id)
                # Insérer ou mettre à jour
                cur.execute("""
                    INSERT INTO organizations (org_id, name)
                    VALUES (%s, %s)
                    ON CONFLICT (org_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        updated_at = CURRENT_TIMESTAMP
                """, (org_id, name))
                
                count += 1
                print(f"  ✅ {name} ({org_id})")
        
        # Synchronisation : supprimer les organisations qui ne sont plus dans le CSV.
        # ON DELETE CASCADE nettoie leurs alertes ; les alertes des organisations
        # conservées dans la liste sont préservées (pas de TRUNCATE).
        if org_ids:
            placeholders = ','.join(cur.mogrify('%s', (oid,)).decode() for oid in org_ids)
            cur.execute(f"DELETE FROM organizations WHERE org_id NOT IN ({placeholders})")
        
        conn.commit()
        print(f"\n✅ {count} organisations importées avec succès !")
        
        cur.close()
        conn.close()
        return True
        
    except FileNotFoundError:
        print(f"❌ Fichier CSV non trouvé: {csv_path}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == '__main__':
    import sys
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'organizations.csv'
    success = import_organizations(csv_file)
    sys.exit(0 if success else 1)