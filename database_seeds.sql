-- ============================================================================
-- SEEDS - DATOS INICIALES PARA SANTOS TUTOR
-- Ejecutar después de database_schema.sql
-- ============================================================================

-- ============================================================================
-- MATERIAS/SUJETOS INICIALES
-- ============================================================================

-- Limpiar datos existentes (opcional, comentar si no se desea)
-- TRUNCATE TABLE subjects CASCADE;

-- Insertar materias iniciales
INSERT INTO subjects (id, name, description, price, is_active, created_at) VALUES
    (
        '550e8400-e29b-41d4-a716-446655440001',
        'Matemáticas',
        'Curso completo de matemáticas que incluye álgebra, geometría, cálculo y estadística. Ideal para estudiantes de secundaria y preparatoria.',
        299.99,
        TRUE,
        NOW()
    ),
    (
        '550e8400-e29b-41d4-a716-446655440002',
        'Física',
        'Fundamentos de física: mecánica, termodinámica, electromagnetismo y óptica. Con ejercicios prácticos y ejemplos del mundo real.',
        299.99,
        TRUE,
        NOW()
    ),
    (
        '550e8400-e29b-41d4-a716-446655440003',
        'Química',
        'Química general y orgánica. Estructura atómica, enlaces químicos, reacciones y compuestos orgánicos.',
        299.99,
        TRUE,
        NOW()
    ),
    (
        '550e8400-e29b-41d4-a716-446655440004',
        'Biología',
        'Biología celular, genética, ecología y anatomía. Perfecto para estudiantes de ciencias de la salud.',
        249.99,
        TRUE,
        NOW()
    ),
    (
        '550e8400-e29b-41d4-a716-446655440005',
        'Programación',
        'Fundamentos de programación, algoritmos, estructuras de datos y desarrollo web. Lenguajes: Python, JavaScript, Java.',
        349.99,
        TRUE,
        NOW()
    ),
    (
        '550e8400-e29b-41d4-a716-446655440006',
        'Historia',
        'Historia universal y de México. Desde la antigüedad hasta la época contemporánea.',
        199.99,
        TRUE,
        NOW()
    ),
    (
        '550e8400-e29b-41d4-a716-446655440007',
        'Literatura',
        'Análisis literario, géneros, movimientos literarios y redacción. Literatura española, latinoamericana y universal.',
        199.99,
        TRUE,
        NOW()
    ),
    (
        '550e8400-e29b-41d4-a716-446655440008',
        'Inglés',
        'Inglés desde básico hasta avanzado. Gramática, vocabulario, comprensión lectora y conversación.',
        249.99,
        TRUE,
        NOW()
    )
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- NOTAS IMPORTANTES
-- ============================================================================
-- 1. Los usuarios se crean automáticamente a través de Supabase Auth
--    No es necesario insertarlos manualmente aquí
--
-- 2. Las suscripciones (user_subscriptions) se crean cuando un usuario
--    compra una materia a través de la aplicación
--
-- 3. Las sesiones de chat, mensajes, ejercicios y estadísticas se generan
--    automáticamente cuando los usuarios interactúan con la aplicación
--
-- 4. Si necesitas crear usuarios de prueba, puedes hacerlo desde el
--    dashboard de Supabase Auth o usando la API de Supabase
--
-- 5. Para crear suscripciones de prueba, puedes usar:
--    INSERT INTO user_subscriptions (user_id, subject_id, is_active)
--    VALUES ('user-uuid-here', '550e8400-e29b-41d4-a716-446655440001', TRUE);

-- ============================================================================
-- VERIFICACIÓN DE DATOS INSERTADOS
-- ============================================================================
-- Ejecutar para verificar que los datos se insertaron correctamente:
-- SELECT id, name, price, is_active FROM subjects ORDER BY name;

