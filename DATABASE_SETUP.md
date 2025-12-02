# Configuración de Base de Datos - Santos Tutor

Este documento explica cómo restaurar la estructura completa de la base de datos después de haberla borrado por error.

## 📋 Archivos Incluidos

1. **`database_schema.sql`** - Script completo con todas las tablas, índices, triggers y políticas RLS
2. **`database_seeds.sql`** - Datos iniciales (materias/subjects)
3. **`database_sync_auth.sql`** - Sincronización automática de usuarios de Supabase Auth con la tabla `users`

## 🚀 Pasos para Restaurar la Base de Datos

### Opción 1: Usando el SQL Editor de Supabase (Recomendado)

1. **Accede a tu proyecto en Supabase**
   - Ve a https://supabase.com/dashboard
   - Selecciona tu proyecto

2. **Abre el SQL Editor**
   - En el menú lateral, haz clic en "SQL Editor"
   - Haz clic en "New query"

3. **Ejecuta el schema**
   - Copia y pega el contenido de `database_schema.sql`
   - Haz clic en "Run" o presiona `Ctrl+Enter` (Windows) / `Cmd+Enter` (Mac)
   - Verifica que no haya errores

4. **Ejecuta los seeds**
   - Abre una nueva query
   - Copia y pega el contenido de `database_seeds.sql`
   - Haz clic en "Run"
   - Verifica que se hayan insertado las materias

5. **Sincroniza usuarios de Auth (Opcional pero recomendado)**
   - Abre una nueva query
   - Copia y pega el contenido de `database_sync_auth.sql`
   - Haz clic en "Run"
   - Esto creará triggers para sincronizar automáticamente usuarios nuevos y existentes

### Opción 2: Usando psql (Línea de comandos)

```bash
# Conectarte a tu base de datos de Supabase
psql "postgresql://postgres:[TU_PASSWORD]@db.[TU_PROYECTO].supabase.co:5432/postgres"

# Ejecutar el schema
\i database_schema.sql

# Ejecutar los seeds
\i database_seeds.sql
```

### Opción 3: Usando la CLI de Supabase

```bash
# Si tienes la CLI de Supabase instalada
supabase db reset
supabase db push
```

## 📊 Estructura de la Base de Datos

### Tablas Principales

1. **`users`** - Usuarios del sistema (se sincroniza con Supabase Auth)
2. **`subjects`** - Materias/cursos disponibles
3. **`user_subscriptions`** - Suscripciones de usuarios a materias
4. **`chat_sessions`** - Sesiones de chat
5. **`chat_messages`** - Mensajes dentro de las sesiones
6. **`difficulty_tracking`** - Seguimiento de dificultades por tema
7. **`generated_exercises`** - Ejercicios generados para usuarios
8. **`payments`** - Registro de pagos

### Características Implementadas

✅ **Triggers automáticos** para `updated_at`  
✅ **Índices optimizados** para mejor performance  
✅ **Row Level Security (RLS)** configurado para Supabase  
✅ **Foreign keys** con CASCADE para integridad referencial  
✅ **Constraints** para validación de datos  

## 🔒 Seguridad (RLS)

El schema incluye políticas de Row Level Security configuradas para que:

- Los usuarios solo puedan ver y modificar sus propios datos
- Las materias activas sean visibles para todos
- Los mensajes de chat solo sean accesibles por el dueño de la sesión
- Los ejercicios y estadísticas sean privados por usuario

## 📝 Notas Importantes

### Sincronización con Supabase Auth

- Los usuarios se crean automáticamente cuando se registran a través de Supabase Auth
- El campo `id` en la tabla `users` debe coincidir con el `id` del usuario en `auth.users`
- **Ejecuta `database_sync_auth.sql`** para configurar la sincronización automática
- Este script:
  - Crea triggers que sincronizan automáticamente usuarios nuevos
  - Sincroniza usuarios existentes de `auth.users` a `public.users`
  - Actualiza usuarios cuando cambian su información en Auth

### Datos Iniciales

El archivo `database_seeds.sql` incluye 8 materias iniciales:
- Matemáticas
- Física
- Química
- Biología
- Programación
- Historia
- Literatura
- Inglés

Puedes modificar o agregar más materias según tus necesidades.

## 🔍 Verificación

Después de ejecutar los scripts, verifica que todo esté correcto:

```sql
-- Verificar que las tablas existen
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Verificar que las materias se insertaron
SELECT id, name, price, is_active 
FROM subjects 
ORDER BY name;

-- Verificar que RLS está habilitado
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

## 🐛 Solución de Problemas

### Error: "relation already exists"
- Algunas tablas ya existen. Puedes eliminarlas primero o usar `CREATE TABLE IF NOT EXISTS` (ya incluido en el script)

### Error: "permission denied"
- Asegúrate de estar usando una conexión con permisos de administrador
- En Supabase, usa el SQL Editor que tiene permisos completos

### Error: "function already exists"
- El script usa `CREATE OR REPLACE FUNCTION`, así que debería actualizar la función automáticamente

### RLS bloqueando consultas
- Verifica que el usuario esté autenticado
- Revisa las políticas RLS en el SQL Editor de Supabase

## 📚 Recursos Adicionales

- [Documentación de Supabase](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)

## ✅ Checklist de Restauración

- [ ] Ejecutar `database_schema.sql` sin errores
- [ ] Ejecutar `database_seeds.sql` sin errores
- [ ] Ejecutar `database_sync_auth.sql` para sincronización de usuarios
- [ ] Verificar que las 8 materias estén creadas
- [ ] Verificar que RLS esté habilitado en todas las tablas
- [ ] Verificar que los usuarios de Auth estén sincronizados
- [ ] Probar login en la aplicación
- [ ] Verificar que se puedan crear sesiones de chat
- [ ] Verificar que se puedan generar ejercicios

---

**Última actualización:** 2024

