-- ============================================================================
-- SINCRONIZACIÓN DE USUARIOS DE SUPABASE AUTH CON TABLA USERS
-- Ejecutar después de database_schema.sql
-- ============================================================================

-- ============================================================================
-- FUNCIÓN PARA SINCRONIZAR USUARIOS NUEVOS
-- ============================================================================
-- Esta función se ejecuta automáticamente cuando se crea un nuevo usuario
-- en Supabase Auth y lo sincroniza con la tabla public.users

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, name, created_at, updated_at)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(
      NEW.raw_user_meta_data->>'name',
      NEW.raw_user_meta_data->>'full_name',
      SPLIT_PART(NEW.email, '@', 1)
    ),
    NOW(),
    NOW()
  )
  ON CONFLICT (id) DO UPDATE
  SET 
    email = EXCLUDED.email,
    name = COALESCE(EXCLUDED.name, users.name),
    updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- TRIGGER PARA EJECUTAR LA FUNCIÓN AL CREAR USUARIO
-- ============================================================================
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- FUNCIÓN PARA ACTUALIZAR USUARIOS EXISTENTES
-- ============================================================================
-- Esta función se ejecuta cuando se actualiza un usuario en Supabase Auth

CREATE OR REPLACE FUNCTION public.handle_user_update()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE public.users
  SET 
    email = NEW.email,
    name = COALESCE(
      NEW.raw_user_meta_data->>'name',
      NEW.raw_user_meta_data->>'full_name',
      users.name
    ),
    updated_at = NOW()
  WHERE id = NEW.id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- TRIGGER PARA EJECUTAR LA FUNCIÓN AL ACTUALIZAR USUARIO
-- ============================================================================
DROP TRIGGER IF EXISTS on_auth_user_updated ON auth.users;
CREATE TRIGGER on_auth_user_updated
  AFTER UPDATE ON auth.users
  FOR EACH ROW
  WHEN (OLD.email IS DISTINCT FROM NEW.email OR OLD.raw_user_meta_data IS DISTINCT FROM NEW.raw_user_meta_data)
  EXECUTE FUNCTION public.handle_user_update();

-- ============================================================================
-- SINCRONIZAR USUARIOS EXISTENTES (OPCIONAL)
-- ============================================================================
-- Si ya tienes usuarios en Supabase Auth, ejecuta esto para sincronizarlos
-- con la tabla public.users

INSERT INTO public.users (id, email, name, created_at, updated_at)
SELECT 
  id,
  email,
  COALESCE(
    raw_user_meta_data->>'name',
    raw_user_meta_data->>'full_name',
    SPLIT_PART(email, '@', 1)
  ) as name,
  created_at,
  updated_at
FROM auth.users
ON CONFLICT (id) DO UPDATE
SET 
  email = EXCLUDED.email,
  name = COALESCE(EXCLUDED.name, users.name),
  updated_at = NOW();

-- ============================================================================
-- VERIFICACIÓN
-- ============================================================================
-- Ejecutar para verificar que los usuarios se sincronizaron correctamente:
-- SELECT COUNT(*) FROM public.users;
-- SELECT COUNT(*) FROM auth.users;
-- Ambos deberían tener el mismo número (o public.users puede tener más si hay usuarios creados manualmente)

