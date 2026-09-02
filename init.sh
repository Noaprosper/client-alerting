#!/bin/bash
# Script d'initialisation du projet Alert-client

set -e

echo "🚀 Initialisation du projet Scaleway Client Alerting Dashboard"
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier si PostgreSQL est installé
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL n'est pas installé. Veuillez l'installer manuellement.${NC}"
else
    echo -e "${BLUE}📦 Configuration de la base de données...${NC}"
    
    # Créer la base de données
    read -p "Nom de la base de données (alert_client): " DB_NAME
    DB_NAME=${DB_NAME:-alert_client}
    
    echo "Création de la base de données: $DB_NAME"
    createdb "$DB_NAME" 2>/dev/null || echo "La base existe déjà"
    
    # Exécuter le schéma
    echo "Exécution du schéma..."
    psql -d "$DB_NAME" -f database/schema.sql
    
    # Seeder les organisations
    echo "Seed des organisations..."
    psql -d "$DB_NAME" -f database/seed_organizations.sql
    
    echo -e "${GREEN}✅ Base de données configurée!${NC}"
fi

echo ""
echo -e "${BLUE}🐍 Installation des dépendances Python...${NC}"
cd cron-match-incidents
python3 -m venv venv 2>/dev/null || echo "venv existe déjà"
source venv/bin/activate
pip install -r requirements.txt
cd ..
echo -e "${GREEN}✅ Dépendances Python installées!${NC}"

echo ""
echo -e "${BLUE}⚛️  Installation du Dashboard Next.js...${NC}"
cd dashboard
npm install
cd ..
echo -e "${GREEN}✅ Dashboard installé!${NC}"

echo ""
echo -e "${YELLOW}📝 Configuration des variables d'environnement:${NC}"
echo "Copiez .env.example vers .env et remplissez les valeurs:"
echo "  cp .env.example cron-match-incidents/.env"
echo "  cp .env.example dashboard/.env"
echo ""
echo "Variables à configurer:"
echo "  - SCALEWAY_API_KEY (READ-ONLY uniquement!)"
echo "  - DATABASE_URL"
echo "  - INCIDENT_API_URL"
echo "  - CONSOLE_API_URL"

echo ""
echo -e "${GREEN}✅ Initialisation terminée!${NC}"
echo ""
echo "Prochaines étapes:"
echo "  1. Configurer les variables d'environnement"
echo "  2. Tester le cron job: cd cron-match-incidents && python main.py"
echo "  3. Lancer le dashboard: cd dashboard && npm run dev"
echo "  4. Ajouter au crontab: */15 * * * * cd /Users/cbenard/Desktop/Alert-client/cron-match-incidents && python main.py"