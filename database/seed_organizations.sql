-- Seed organizations from CSV
-- Les organisations sont importées depuis un fichier CSV
-- Fichier: database/organizations.csv
-- Format: org_id,name

-- Cette table sera remplie via le script import_csv.py
-- Usage: cd database && python import_csv.py organizations.csv

-- Pour tester manuellement, voici quelques exemples (à remplacer par vos vrais org_ids)
INSERT INTO organizations (org_id, name)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'Organisation Test 1'),
    ('00000000-0000-0000-0000-000000000002', 'Organisation Test 2')
ON CONFLICT (org_id) DO NOTHING;

-- Pour importer votre CSV, utilisez le script Python:
-- cd database
-- python import_csv.py organizations.csv

-- Ou via commande SQL COPY (chemin absolu requis):
-- COPY organizations(org_id, name) FROM '/Users/cbenard/Desktop/Alert-client/database/organizations.csv' CSV HEADER;
