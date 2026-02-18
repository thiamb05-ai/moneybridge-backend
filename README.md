# MoneyBridge Backend API

API Django pour les transferts d'argent Afrique → Europe avec virements SEPA instantanés.

## 🚀 Fonctionnalités

- ✅ Gestion des utilisateurs avec KYC
- 💰 Réception depuis Wave, Orange Money, MTN Mobile Money
- 🏦 Virements SEPA instantanés vers comptes bancaires européens
- 💱 Conversion de devises en temps réel
- 📊 Système de ledger comptable
- 🔒 Sécurité et conformité réglementaire
- 📱 Webhooks pour notifications en temps réel

## 📋 Prérequis

- Python 3.11+
- PostgreSQL 14+
- Redis 7+ (pour Celery)

## 🛠️ Installation

### 1. Cloner le projet et créer un environnement virtuel

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
# Sur Mac/Linux:
source venv/bin/activate
# Sur Windows:
venv\Scripts\activate
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer la base de données PostgreSQL

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer la base de données
CREATE DATABASE moneybridge;
CREATE USER moneybridge_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE moneybridge TO moneybridge_user;
\q
```

### 4. Configurer les variables d'environnement

```bash
# Copier le fichier exemple
cp .env.example .env

# Éditer .env avec vos vraies valeurs
nano .env
```

### 5. Appliquer les migrations

```bash
python manage.py migrate
```

### 6. Créer un super utilisateur

```bash
python manage.py createsuperuser
```

### 7. Lancer le serveur de développement

```bash
python manage.py runserver
```

### 8. Lancer Celery (dans un autre terminal)

```bash
# Worker
celery -A moneybridge worker -l info

# Beat scheduler (pour les tâches périodiques)
celery -A moneybridge beat -l info
```

## 📚 API Documentation

Une fois le serveur lancé, accédez à :

- **API Docs (Swagger)**: http://localhost:8000/api/docs/
- **Admin Django**: http://localhost:8000/admin/

## 🏗️ Architecture

```
moneybridge-backend/
├── moneybridge/          # Configuration Django principale
├── accounts/             # Gestion utilisateurs & KYC
├── wallets/              # Portefeuilles et soldes
├── transactions/         # Transactions et ledger
├── payments/             # Intégrations paiements (Wave, Orange Money, etc.)
├── banking/              # Virements SEPA
└── exchange/             # Taux de change
```

## 🔐 Sécurité

- Authentification JWT
- Chiffrement des données sensibles
- Rate limiting
- Validation KYC obligatoire
- Audit trail complet

## 🧪 Tests

```bash
python manage.py test
```

## 📝 Notes importantes

### Conformité réglementaire

⚠️ **IMPORTANT**: Ce projet nécessite :
- Licence d'établissement de paiement (ACPR en France)
- Conformité KYC/AML stricte
- Agrément SEPA pour les virements
- Contrats avec opérateurs mobile money

### APIs Tierces requises

1. **Wave API**: Contactez Wave pour obtenir l'accès API
2. **Orange Money**: Programme Orange Developer
3. **MTN Mobile Money**: MTN MoMo API
4. **SEPA Instant**: Via Stripe Connect, Modulr ou directement via votre banque

## 📞 Support

Pour toute question sur l'implémentation, contactez votre équipe technique.
