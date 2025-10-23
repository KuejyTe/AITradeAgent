#!/usr/bin/env python3
"""
Quick verification script for OKX API integration
Verifies all modules import correctly and basic functionality works
"""

import asyncio
import sys


def test_imports():
    """Test that all modules import correctly"""
    print("Testing imports...")
    try:
        from app.services.okx import OKXClient, OKXMarket, OKXAccount, OKXTrade, OKXWebSocket
        from app.services.okx.auth import OKXAuth
        from app.services.okx.client import OKXError, OKXRateLimitError, OKXEnvironment
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_auth():
    """Test authentication module"""
    print("\nTesting authentication...")
    try:
        from app.services.okx.auth import OKXAuth
        
        auth = OKXAuth("test_key", "test_secret", "test_pass")
        timestamp = auth._get_timestamp()
        assert timestamp.endswith('Z')
        assert 'T' in timestamp
        
        signature = auth._create_signature(timestamp, "GET", "/api/v5/test")
        assert len(signature) > 0
        
        headers = auth.get_headers("GET", "/api/v5/test")
        assert "OK-ACCESS-KEY" in headers
        assert "OK-ACCESS-SIGN" in headers
        
        print("✅ Authentication tests passed")
        return True
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False


async def test_client_initialization():
    """Test client initialization"""
    print("\nTesting client initialization...")
    try:
        from app.services.okx import OKXClient, OKXMarket, OKXAccount, OKXTrade
        
        # Test without auth
        client = OKXClient()
        assert client.base_url == "https://www.okx.com"
        assert client.auth is None
        await client.close()
        
        # Test with auth
        client = OKXClient(
            api_key="test_key",
            secret_key="test_secret",
            passphrase="test_pass"
        )
        assert client.auth is not None
        await client.close()
        
        # Test with context manager
        async with OKXClient() as client:
            assert client is not None
        
        # Test service initialization
        async with OKXClient() as client:
            market = OKXMarket(client)
            account = OKXAccount(client)
            trade = OKXTrade(client)
            assert market.client == client
            assert account.client == client
            assert trade.client == client
        
        print("✅ Client initialization tests passed")
        return True
    except Exception as e:
        print(f"❌ Client initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_websocket_initialization():
    """Test WebSocket initialization"""
    print("\nTesting WebSocket initialization...")
    try:
        from app.services.okx import OKXWebSocket
        
        # Test without auth
        ws = OKXWebSocket()
        assert ws.url == "wss://ws.okx.com:8443/ws/v5/public"
        assert ws.auth is None
        
        # Test with auth
        ws = OKXWebSocket(
            api_key="test_key",
            secret_key="test_secret",
            passphrase="test_pass"
        )
        assert ws.auth is not None
        
        # Test custom URL
        custom_url = "wss://custom.okx.com/ws"
        ws = OKXWebSocket(url=custom_url)
        assert ws.url == custom_url
        
        print("✅ WebSocket initialization tests passed")
        return True
    except Exception as e:
        print(f"❌ WebSocket initialization test failed: {e}")
        return False


def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    try:
        from app.core.config import settings
        
        assert hasattr(settings, 'OKX_API_KEY')
        assert hasattr(settings, 'OKX_SECRET_KEY')
        assert hasattr(settings, 'OKX_PASSPHRASE')
        assert hasattr(settings, 'OKX_API_BASE_URL')
        assert hasattr(settings, 'OKX_WS_PUBLIC_URL')
        assert hasattr(settings, 'OKX_WS_PRIVATE_URL')
        
        assert settings.OKX_API_BASE_URL == "https://www.okx.com"
        assert settings.OKX_WS_PUBLIC_URL == "wss://ws.okx.com:8443/ws/v5/public"
        
        print("✅ Configuration tests passed")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def main():
    """Run all verification tests"""
    print("=" * 60)
    print("OKX API Integration Verification")
    print("=" * 60)
    
    results = []
    
    # Run synchronous tests
    results.append(test_imports())
    results.append(test_auth())
    results.append(test_websocket_initialization())
    results.append(test_configuration())
    
    # Run async tests
    results.append(await test_client_initialization())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All verification tests passed ({passed}/{total})")
        print("=" * 60)
        return 0
    else:
        print(f"❌ Some tests failed ({passed}/{total} passed)")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
