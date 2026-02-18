# Guide de Déploiement MoneyBridge

## 🎯 Vue d'ensemble de l'architecture

```
┌─────────────────┐
│   Mobile Apps   │  (React Native / Flutter)
│   (Frontend)    │
└────────┬────────┘
         │
         │ HTTPS/REST API
         │
┌────────▼────────┐
│   Django API    │  (Backend - Ce projet)
│   + Celery      │
└────────┬────────┘
         │
         ├──────────────┐
         │              │
┌────────▼────────┐ ┌──▼────────┐
│   PostgreSQL    │ │   Redis    │
└─────────────────┘ └────────────┘
         │
         │
┌────────▼────────────────────────┐
│    Intégrations Externes        │
├─────────────────────────────────┤
│ • Wave API                      │
│ • Orange Money API              │
│ • MTN Mobile Money API          │
│ • Stripe (SEPA Instant)         │
│ • Exchange Rate API             │
└─────────────────────────────────┘
```

## 📦 Installation Locale (Développement)

### 1. Prérequis

```bash
# Installer PostgreSQL
# Mac:
brew install postgresql@14
brew services start postgresql@14

# Ubuntu/Debian:
sudo apt update
sudo apt install postgresql-14 postgresql-contrib

# Windows:
# Téléchargez l'installeur depuis postgresql.org
```

```bash
# Installer Redis
# Mac:
brew install redis
brew services start redis

# Ubuntu/Debian:
sudo apt install redis-server
sudo systemctl start redis-server

# Windows:
# Téléchargez depuis redis.io ou utilisez WSL
```

### 2. Configuration de la base de données

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Dans psql:
CREATE DATABASE moneybridge;
CREATE USER moneybridge_user WITH PASSWORD 'votre_mot_de_passe_fort';
ALTER ROLE moneybridge_user SET client_encoding TO 'utf8';
ALTER ROLE moneybridge_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE moneybridge_user SET timezone TO 'Europe/Paris';
GRANT ALL PRIVILEGES ON DATABASE moneybridge TO moneybridge_user;
\q
```

### 3. Installation du projet

```bash
# Rendre le script setup.sh exécutable
chmod +x setup.sh

# Exécuter le script
./setup.sh

# OU installation manuelle:
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configuration (.env)

Éditez le fichier `.env` avec vos vraies valeurs:

```env
# Django
SECRET_KEY=votre-cle-secrete-generee
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=moneybridge
DB_USER=moneybridge_user
DB_PASSWORD=votre_mot_de_passe_fort
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Wave API (à obtenir de Wave)
WAVE_API_KEY=votre_wave_api_key
WAVE_API_SECRET=votre_wave_api_secret
WAVE_BASE_URL=https://api.wave.com/v1

# Stripe (pour SEPA)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### 5. Migrations et données initiales

```bash
# Appliquer les migrations
python manage.py migrate

# Créer un super utilisateur
python manage.py createsuperuser

# (Optionnel) Charger des données de test
python manage.py loaddata initial_data.json
```

### 6. Lancer le serveur

Terminal 1 - Django:
```bash
python manage.py runserver
```

Terminal 2 - Celery Worker:
```bash
celery -A moneybridge worker -l info
```

Terminal 3 - Celery Beat (tâches périodiques):
```bash
celery -A moneybridge beat -l info
```

## 🌐 Déploiement en Production

### Option 1: Déploiement sur VPS (OVH, Scaleway, DigitalOcean)

#### 1. Préparer le serveur

```bash
# Se connecter au serveur
ssh root@votre-ip-serveur

# Mettre à jour le système
apt update && apt upgrade -y

# Installer les dépendances
apt install -y python3.11 python3.11-venv python3-pip postgresql-14 redis-server nginx supervisor git
```

#### 2. Configurer PostgreSQL

```bash
sudo -u postgres psql

CREATE DATABASE moneybridge;
CREATE USER moneybridge_user WITH PASSWORD 'mot_de_passe_production_fort';
GRANT ALL PRIVILEGES ON DATABASE moneybridge TO moneybridge_user;
\q
```

#### 3. Déployer l'application

```bash
# Créer un utilisateur pour l'app
useradd -m -s /bin/bash moneybridge
su - moneybridge

# Cloner le dépôt
git clone https://github.com/votre-compte/moneybridge-backend.git
cd moneybridge-backend

# Installer les dépendances
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Configurer .env pour la production
cp .env.example .env
nano .env  # Éditer avec les vraies valeurs
```

#### 4. Configurer Gunicorn

Créer `/home/moneybridge/gunicorn_config.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
accesslog = "/var/log/moneybridge/access.log"
errorlog = "/var/log/moneybridge/error.log"
loglevel = "info"
```

#### 5. Configurer Supervisor

Créer `/etc/supervisor/conf.d/moneybridge.conf`:

```ini
[program:moneybridge]
command=/home/moneybridge/moneybridge-backend/venv/bin/gunicorn moneybridge.wsgi:application -c /home/moneybridge/gunicorn_config.py
directory=/home/moneybridge/moneybridge-backend
user=moneybridge
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/moneybridge/gunicorn.log

[program:moneybridge_celery]
command=/home/moneybridge/moneybridge-backend/venv/bin/celery -A moneybridge worker -l info
directory=/home/moneybridge/moneybridge-backend
user=moneybridge
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/moneybridge/celery.log

[program:moneybridge_celery_beat]
command=/home/moneybridge/moneybridge-backend/venv/bin/celery -A moneybridge beat -l info
directory=/home/moneybridge/moneybridge-backend
user=moneybridge
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/moneybridge/celery_beat.log
```

```bash
# Créer les répertoires de logs
mkdir -p /var/log/moneybridge
chown -R moneybridge:moneybridge /var/log/moneybridge

# Recharger supervisor
supervisorctl reread
supervisorctl update
supervisorctl start all
```

#### 6. Configurer Nginx

Créer `/etc/nginx/sites-available/moneybridge`:

```nginx
server {
    listen 80;
    server_name api.moneybridge.com;

    client_max_body_size 10M;

    location /static/ {
        alias /home/moneybridge/moneybridge-backend/staticfiles/;
    }

    location /media/ {
        alias /home/moneybridge/moneybridge-backend/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Activer le site
ln -s /etc/nginx/sites-available/moneybridge /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Installer SSL avec Let's Encrypt
apt install certbot python3-certbot-nginx
certbot --nginx -d api.moneybridge.com
```

### Option 2: Déploiement sur AWS/GCP/Azure

Utilisez des services managés:
- **Base de données**: RDS (AWS) / Cloud SQL (GCP) / Azure Database
- **Cache**: ElastiCache (AWS) / Memorystore (GCP) / Azure Cache
- **Application**: ECS/EKS (AWS) / Cloud Run (GCP) / App Service (Azure)
- **Files d'attente**: SQS (AWS) / Cloud Tasks (GCP) / Service Bus (Azure)

## 🔒 Sécurité en Production

### 1. Variables d'environnement

```bash
# NE JAMAIS commiter .env dans Git
echo ".env" >> .gitignore

# Utiliser des secrets managers en production
# AWS Secrets Manager, GCP Secret Manager, Azure Key Vault
```

### 2. Settings Django pour production

Dans `settings.py`:

```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
```

### 3. Firewall

```bash
# Configurer UFW
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

## 📊 Monitoring

### 1. Logs

```bash
# Voir les logs en temps réel
tail -f /var/log/moneybridge/*.log

# Rotation des logs (logrotate)
# Créer /etc/logrotate.d/moneybridge
```

### 2. Monitoring avec Sentry

```bash
pip install sentry-sdk

# Dans settings.py
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

## 🔄 Backups

```bash
# Backup PostgreSQL quotidien
crontab -e

# Ajouter:
0 2 * * * pg_dump -U moneybridge_user moneybridge > /backups/moneybridge_$(date +\%Y\%m\%d).sql
```

## 📝 Checklist de déploiement

- [ ] Base de données configurée
- [ ] Redis installé et configuré
- [ ] Variables d'environnement configurées
- [ ] Migrations appliquées
- [ ] SSL/TLS configuré
- [ ] Firewall configuré
- [ ] Monitoring mis en place
- [ ] Backups automatiques configurés
- [ ] Tests de charge effectués
- [ ] Documentation API publiée
- [ ] Webhooks configurés pour Wave/Orange Money/Stripe
- [ ] Conformité RGPD vérifiée
- [ ] Licences réglementaires obtenues
