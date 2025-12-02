-- ============================================================================
-- SCHEMA COMPLETO DE BASE DE DATOS - SANTOS TUTOR
-- Compatible con Supabase (PostgreSQL)
-- ============================================================================

-- Habilitar extensión UUID si no está habilitada
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLA DE USUARIOS
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TABLA DE MATERIAS/SUJETOS
-- ============================================================================
CREATE TABLE IF NOT EXISTS subjects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TABLA DE SUSCRIPCIONES DE USUARIOS A MATERIAS
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    purchased_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, subject_id)
);

-- ============================================================================
-- TABLA DE SESIONES DE CHAT
-- ============================================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    session_title VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TABLA DE MENSAJES DEL CHAT
-- ============================================================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    message_type VARCHAR DEFAULT 'text' CHECK (message_type IN ('text', 'exercise', 'solution')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TABLA DE SEGUIMIENTO DE DIFICULTADES
-- ============================================================================
CREATE TABLE IF NOT EXISTS difficulty_tracking (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    topic VARCHAR NOT NULL,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    last_practiced TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TABLA DE EJERCICIOS GENERADOS
-- ============================================================================
CREATE TABLE IF NOT EXISTS generated_exercises (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    topic VARCHAR NOT NULL,
    exercise_text TEXT NOT NULL,
    solution TEXT,
    user_answer TEXT,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    completed BOOLEAN DEFAULT FALSE,
    time_spent INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TABLA DE PAGOS
-- ============================================================================
CREATE TABLE IF NOT EXISTS payments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    payment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    payment_status VARCHAR DEFAULT 'completed' CHECK (payment_status IN ('pending', 'completed', 'failed'))
);

-- ============================================================================
-- ÍNDICES PARA MEJOR PERFORMANCE
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_subject_id ON chat_sessions(subject_id);
CREATE INDEX IF NOT EXISTS idx_difficulty_user_subject ON difficulty_tracking(user_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_exercises_user_subject ON generated_exercises(user_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_active ON user_subscriptions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_subject_id ON user_subscriptions(subject_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_subject_id ON payments(subject_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================================================
-- FUNCIÓN PARA ACTUALIZAR updated_at AUTOMÁTICAMENTE
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS PARA ACTUALIZAR updated_at
-- ============================================================================
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions;
CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) PARA SUPABASE
-- ============================================================================

-- Habilitar RLS en todas las tablas
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE difficulty_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- POLÍTICAS RLS PARA USERS
-- ============================================================================
-- Los usuarios pueden ver su propia información
CREATE POLICY "Users can view own data" ON users
    FOR SELECT
    USING (auth.uid() = id);

-- Los usuarios pueden actualizar su propia información
CREATE POLICY "Users can update own data" ON users
    FOR UPDATE
    USING (auth.uid() = id);

-- ============================================================================
-- POLÍTICAS RLS PARA SUBJECTS
-- ============================================================================
-- Todos pueden ver materias activas
CREATE POLICY "Anyone can view active subjects" ON subjects
    FOR SELECT
    USING (is_active = TRUE);

-- ============================================================================
-- POLÍTICAS RLS PARA USER_SUBSCRIPTIONS
-- ============================================================================
-- Los usuarios pueden ver sus propias suscripciones
CREATE POLICY "Users can view own subscriptions" ON user_subscriptions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Los usuarios pueden insertar sus propias suscripciones
CREATE POLICY "Users can insert own subscriptions" ON user_subscriptions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Los usuarios pueden actualizar sus propias suscripciones
CREATE POLICY "Users can update own subscriptions" ON user_subscriptions
    FOR UPDATE
    USING (auth.uid() = user_id);

-- ============================================================================
-- POLÍTICAS RLS PARA CHAT_SESSIONS
-- ============================================================================
-- Los usuarios pueden ver sus propias sesiones
CREATE POLICY "Users can view own chat sessions" ON chat_sessions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Los usuarios pueden crear sus propias sesiones
CREATE POLICY "Users can create own chat sessions" ON chat_sessions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Los usuarios pueden actualizar sus propias sesiones
CREATE POLICY "Users can update own chat sessions" ON chat_sessions
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Los usuarios pueden eliminar sus propias sesiones
CREATE POLICY "Users can delete own chat sessions" ON chat_sessions
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- POLÍTICAS RLS PARA CHAT_MESSAGES
-- ============================================================================
-- Los usuarios pueden ver mensajes de sus propias sesiones
CREATE POLICY "Users can view own chat messages" ON chat_messages
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM chat_sessions
            WHERE chat_sessions.id = chat_messages.session_id
            AND chat_sessions.user_id = auth.uid()
        )
    );

-- Los usuarios pueden insertar mensajes en sus propias sesiones
CREATE POLICY "Users can insert own chat messages" ON chat_messages
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM chat_sessions
            WHERE chat_sessions.id = chat_messages.session_id
            AND chat_sessions.user_id = auth.uid()
        )
    );

-- ============================================================================
-- POLÍTICAS RLS PARA DIFFICULTY_TRACKING
-- ============================================================================
-- Los usuarios pueden ver su propio seguimiento de dificultades
CREATE POLICY "Users can view own difficulty tracking" ON difficulty_tracking
    FOR SELECT
    USING (auth.uid() = user_id);

-- Los usuarios pueden insertar su propio seguimiento
CREATE POLICY "Users can insert own difficulty tracking" ON difficulty_tracking
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Los usuarios pueden actualizar su propio seguimiento
CREATE POLICY "Users can update own difficulty tracking" ON difficulty_tracking
    FOR UPDATE
    USING (auth.uid() = user_id);

-- ============================================================================
-- POLÍTICAS RLS PARA GENERATED_EXERCISES
-- ============================================================================
-- Los usuarios pueden ver sus propios ejercicios
CREATE POLICY "Users can view own exercises" ON generated_exercises
    FOR SELECT
    USING (auth.uid() = user_id);

-- Los usuarios pueden insertar sus propios ejercicios
CREATE POLICY "Users can insert own exercises" ON generated_exercises
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Los usuarios pueden actualizar sus propios ejercicios
CREATE POLICY "Users can update own exercises" ON generated_exercises
    FOR UPDATE
    USING (auth.uid() = user_id);

-- ============================================================================
-- POLÍTICAS RLS PARA PAYMENTS
-- ============================================================================
-- Los usuarios pueden ver sus propios pagos
CREATE POLICY "Users can view own payments" ON payments
    FOR SELECT
    USING (auth.uid() = user_id);

-- Los usuarios pueden insertar sus propios pagos
CREATE POLICY "Users can insert own payments" ON payments
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- COMENTARIOS EN TABLAS Y COLUMNAS
-- ============================================================================
COMMENT ON TABLE users IS 'Tabla de usuarios del sistema';
COMMENT ON TABLE subjects IS 'Tabla de materias/sujetos disponibles';
COMMENT ON TABLE user_subscriptions IS 'Relación entre usuarios y suscripciones a materias';
COMMENT ON TABLE chat_sessions IS 'Sesiones de chat entre usuarios y tutores';
COMMENT ON TABLE chat_messages IS 'Mensajes dentro de las sesiones de chat';
COMMENT ON TABLE difficulty_tracking IS 'Seguimiento de dificultades por tema y usuario';
COMMENT ON TABLE generated_exercises IS 'Ejercicios generados para usuarios';
COMMENT ON TABLE payments IS 'Registro de pagos realizados por usuarios';

