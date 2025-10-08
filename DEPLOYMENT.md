# 🚀 Configuración de Despliegue Automático

## 📋 Workflows creados:

### 1. **deploy.yml** - Despliegue principal
- **Trigger**: Push a `main` o ejecución manual
- **Función**: Construye imagen Docker y la sube a GitHub Container Registry
- **Resultado**: Imagen lista para desplegar

### 2. **test.yml** - Tests y validación
- **Trigger**: Push a `main`/`develop` o Pull Requests
- **Función**: Ejecuta tests, validaciones de seguridad y calidad de código
- **Resultado**: Verifica que el código funciona antes del despliegue

### 3. **server-deploy.yml** - Despliegue al servidor
- **Trigger**: Cuando `deploy.yml` se completa exitosamente
- **Función**: Despliega la imagen al servidor de producción
- **Resultado**: Servicio actualizado automáticamente

## 🔧 Configuración necesaria:

### Variables de entorno secretas (GitHub Secrets):
1. **`OPENAI_API_KEY`** - Tu clave de OpenAI
2. **`REDIS_URL`** - URL de Redis (si es externo)
3. **`DEPLOY_TOKEN`** - Token para desplegar en tu servidor
4. **`SERVER_HOST`** - IP/hostname de tu servidor
5. **`SERVER_USER`** - Usuario SSH del servidor
6. **`SERVER_PATH`** - Ruta donde está el proyecto en el servidor

### Configuración del servidor:
```bash
# En tu servidor, crear script de despliegue:
#!/bin/bash
cd /path/to/ChatbotUVO
git pull origin main
docker-compose down
docker-compose up --build -d
echo "✅ Deployment completed at $(date)"
```

## 🎯 Flujo de despliegue:

1. **Push a main** → Trigger automático
2. **Tests** → Validación del código
3. **Build** → Construcción de imagen Docker
4. **Deploy** → Despliegue al servidor
5. **Health Check** → Verificación de funcionamiento

## 📊 Beneficios:

- ✅ **Despliegue automático** en cada push
- ✅ **Tests automáticos** antes del despliegue
- ✅ **Rollback automático** si falla
- ✅ **Notificaciones** de estado
- ✅ **Historial** de despliegues
- ✅ **Imágenes Docker** versionadas

## 🔗 URLs útiles:

- **GitHub Actions**: `https://github.com/BelphSenpai/ChatbotUVO/actions`
- **Container Registry**: `https://github.com/BelphSenpai/ChatbotUVO/pkgs/container/chatbotuvo`
- **Secrets**: `https://github.com/BelphSenpai/ChatbotUVO/settings/secrets/actions`
