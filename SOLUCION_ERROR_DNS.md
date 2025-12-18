# Solución al Error: "[Errno -2] Name or service not known"

## 🔍 ¿Qué significa este error?

El error `[Errno -2] Name or service not known` es un **error de resolución DNS**. Significa que Python no puede convertir el nombre del servidor (hostname) en una dirección IP.

En tu caso, esto ocurre cuando intenta conectarse a Supabase en la línea:
```python
sb_client.sign_in_with_password(email, password)
```

## 🎯 Posibles Causas

### 1. **URL de Supabase incorrecta o mal formateada**
   - Verifica que la URL en `config/settings.py` sea exactamente:
     ```
     https://kxieicvtrimhozgrykex.supabase.co
     ```
   - **NO debe tener:**
     - Espacios al inicio o final
     - Caracteres especiales extraños
     - `http://` en lugar de `https://`
     - Barras al final (`/`)

### 2. **Problemas de conexión a Internet**
   - Verifica que tengas conexión a internet activa
   - Prueba abrir `https://kxieicvtrimhozgrykex.supabase.co` en tu navegador
   - Si no carga, el problema es de conectividad

### 3. **Problemas de DNS del sistema**
   - Tu sistema no puede resolver el nombre `kxieicvtrimhozgrykex.supabase.co`
   - Puede ser un problema temporal del DNS

### 4. **Firewall o Proxy bloqueando la conexión**
   - Algunos firewalls corporativos bloquean conexiones externas
   - Verifica si estás detrás de un proxy corporativo

### 5. **URL del proyecto incorrecta**
   - Verifica en el dashboard de Supabase que la URL sea correcta
   - A veces los proyectos cambian de URL

## ✅ Soluciones Paso a Paso

### Solución 1: Verificar la URL de Supabase

1. Ve a tu dashboard de Supabase: https://supabase.com/dashboard
2. Selecciona tu proyecto
3. Ve a **Settings > API**
4. Copia la **Project URL** exactamente como aparece
5. Actualiza `config/settings.py` con esa URL

### Solución 2: Probar la conexión manualmente

Abre una terminal y ejecuta:

```bash
# En Windows (PowerShell)
Test-NetConnection -ComputerName kxieicvtrimhozgrykex.supabase.co -Port 443

# O prueba con ping
ping kxieicvtrimhozgrykex.supabase.co
```

Si estos comandos fallan, el problema es de red/DNS.

### Solución 3: Verificar que la URL sea accesible

Abre tu navegador y ve a:
```
https://kxieicvtrimhozgrykex.supabase.co
```

Deberías ver una respuesta JSON o una página de Supabase. Si no carga, el problema es de conectividad.

### Solución 4: Cambiar el DNS temporalmente

Si el problema es de DNS, puedes probar cambiar a DNS públicos:

**Windows:**
1. Ve a Configuración de Red
2. Cambia el DNS a:
   - DNS primario: `8.8.8.8` (Google)
   - DNS secundario: `1.1.1.1` (Cloudflare)

### Solución 5: Verificar el formato de la URL en el código

Asegúrate de que en `config/settings.py` la URL esté exactamente así:

```python
SUPABASE_URL = "https://kxieicvtrimhozgrykex.supabase.co"
```

**NO debe tener:**
- Espacios: `" https://..."` ❌
- Barras finales: `"https://.../"` ❌
- Comillas incorrectas: `'https://...'` (esto está bien, pero mejor usar dobles)

## 🔧 Mejora del Código para Mejor Diagnóstico

He mejorado el manejo de errores para que sea más claro qué está fallando. El código ahora mostrará mensajes más descriptivos.

## 📝 Checklist de Verificación

- [ ] La URL en `config/settings.py` es exactamente `https://kxieicvtrimhozgrykex.supabase.co`
- [ ] La URL no tiene espacios ni caracteres extraños
- [ ] Puedes acceder a la URL en tu navegador
- [ ] Tienes conexión a internet activa
- [ ] No estás detrás de un firewall que bloquee Supabase
- [ ] La clave `SUPABASE_KEY` es correcta y corresponde al mismo proyecto

## 🆘 Si el problema persiste

1. **Verifica en Supabase Dashboard:**
   - Ve a Settings > API
   - Confirma que la Project URL y anon key sean correctas
   - Verifica que el proyecto esté activo

2. **Prueba con otro proyecto de Supabase:**
   - Crea un proyecto de prueba
   - Usa esas credenciales temporalmente para verificar que el código funciona

3. **Revisa los logs de Streamlit:**
   - Los errores completos pueden estar en la consola donde ejecutas `streamlit run app.py`

4. **Verifica la versión de la librería supabase:**
   ```bash
   pip show supabase
   ```
   Asegúrate de tener una versión reciente (>=2.0.0)


