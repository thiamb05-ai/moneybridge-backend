#!/bin/bash

# MoneyBridge Backend Setup Script
echo "🚀 Configuration de MoneyBridge Backend..."
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Version Python détectée: $python_version"

# Create virtual environment
echo ""
echo "📦 Création de l'environnement virtuel..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activation de l'environnement virtuel..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Mise à jour de pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📥 Installation des dépendances..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Création du fichier .env..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Éditez le fichier .env avec vos vraies valeurs!"
fi

# Generate Django secret key
echo ""
echo "🔐 Génération de la clé secrète Django..."
secret_key=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/your-secret-key-here-change-in-production/$secret_key/" .env
else
    # Linux
    sed -i "s/your-secret-key-here-change-in-production/$secret_key/" .env
fi

echo ""
echo "✅ Installation terminée!"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Configurez PostgreSQL et créez la base de données 'moneybridge'"
echo "2. Éditez le fichier .env avec vos informations de base de données"
echo "3. Exécutez: python manage.py migrate"
echo "4. Créez un super utilisateur: python manage.py createsuperuser"
echo "5. Lancez le serveur: python manage.py runserver"
echo ""
echo "📚 Documentation complète dans README.md"
