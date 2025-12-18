"""
Script de prueba para verificar la conexión a Supabase.
Ejecuta este script para diagnosticar problemas de conexión.
"""

import sys
from config.settings import SUPABASE_URL, SUPABASE_KEY

def test_dns_resolution():
    """Prueba si se puede resolver el nombre del servidor."""
    import socket
    from urllib.parse import urlparse
    
    print("=" * 60)
    print("PRUEBA 1: Resolución DNS")
    print("=" * 60)
    
    try:
        parsed = urlparse(SUPABASE_URL)
        hostname = parsed.hostname
        
        if not hostname:
            print(f"❌ ERROR: No se pudo extraer el hostname de la URL: {SUPABASE_URL}")
            return False
        
        print(f"Intentando resolver: {hostname}")
        ip_address = socket.gethostbyname(hostname)
        print(f"✅ ÉXITO: {hostname} resuelve a {ip_address}")
        return True
    except socket.gaierror as e:
        print(f"❌ ERROR DNS: No se pudo resolver el nombre del servidor")
        print(f"   Error: {e}")
        print(f"   URL: {SUPABASE_URL}")
        print(f"   Hostname: {hostname if 'hostname' in locals() else 'N/A'}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_http_connection():
    """Prueba si se puede establecer una conexión HTTP."""
    import requests
    
    print("\n" + "=" * 60)
    print("PRUEBA 2: Conexión HTTP")
    print("=" * 60)
    
    try:
        print(f"Intentando conectar a: {SUPABASE_URL}")
        response = requests.get(SUPABASE_URL, timeout=10)
        print(f"✅ ÉXITO: Conexión establecida")
        print(f"   Status Code: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError as e:
        print(f"❌ ERROR: No se pudo conectar al servidor")
        print(f"   Error: {e}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ ERROR: Timeout - El servidor no respondió a tiempo")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_supabase_client():
    """Prueba si se puede crear el cliente de Supabase."""
    import supabase
    
    print("\n" + "=" * 60)
    print("PRUEBA 3: Cliente de Supabase")
    print("=" * 60)
    
    try:
        print(f"URL: {SUPABASE_URL}")
        print(f"Key: {SUPABASE_KEY[:20]}... (primeros 20 caracteres)")
        
        client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ ÉXITO: Cliente de Supabase creado correctamente")
        return True
    except Exception as e:
        print(f"❌ ERROR: No se pudo crear el cliente de Supabase")
        print(f"   Error: {e}")
        error_str = str(e)
        if "Name or service not known" in error_str or "Errno -2" in error_str:
            print("\n💡 SUGERENCIA: Este es un error de DNS.")
            print("   Verifica que:")
            print("   1. Tengas conexión a internet")
            print("   2. La URL de Supabase sea correcta")
            print("   3. No haya firewall bloqueando la conexión")
        return False


def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO DE CONEXIÓN A SUPABASE")
    print("=" * 60)
    print(f"\nConfiguración actual:")
    print(f"  SUPABASE_URL: {SUPABASE_URL}")
    print(f"  SUPABASE_KEY: {'✅ Configurada' if SUPABASE_KEY else '❌ Vacía'}")
    
    if not SUPABASE_URL:
        print("\n❌ ERROR CRÍTICO: SUPABASE_URL está vacía")
        print("   Configura la URL en config/settings.py")
        sys.exit(1)
    
    if not SUPABASE_KEY:
        print("\n❌ ERROR CRÍTICO: SUPABASE_KEY está vacía")
        print("   Configura la clave en config/settings.py")
        sys.exit(1)
    
    results = []
    results.append(("DNS", test_dns_resolution()))
    results.append(("HTTP", test_http_connection()))
    results.append(("Cliente", test_supabase_client()))
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"  {test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✅ Todas las pruebas pasaron. La conexión está funcionando correctamente.")
    else:
        print("\n❌ Algunas pruebas fallaron. Revisa los errores arriba.")
        print("\n💡 Consulta el archivo SOLUCION_ERROR_DNS.md para más ayuda.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())


