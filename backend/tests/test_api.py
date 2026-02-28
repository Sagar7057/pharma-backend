"""
Comprehensive test suite for PharmaPricing MVP
Tests for all endpoints and functionality
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
import json

class TestAuthentication:
    """Test authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_user_signup_success(self, client: AsyncClient):
        """Test successful user signup"""
        response = await client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "Test@1234",
                "full_name": "Test User",
                "company_name": "Test Company",
                "phone": "9876543210",
                "city": "Mumbai",
                "state": "Maharashtra"
            }
        )
        assert response.status_code == 201
        assert response.json()["success"] == True
        assert "user_id" in response.json()["data"]
    
    @pytest.mark.asyncio
    async def test_user_login_success(self, client: AsyncClient):
        """Test successful user login"""
        # First signup
        await client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "Test@1234",
                "full_name": "Test User",
                "company_name": "Test Company"
            }
        )
        
        # Then login
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test@1234"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()["data"]
    
    @pytest.mark.asyncio
    async def test_invalid_email_signup(self, client: AsyncClient):
        """Test signup with invalid email"""
        response = await client.post(
            "/api/auth/signup",
            json={
                "email": "invalid-email",
                "password": "Test@1234",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 400


class TestBrands:
    """Test brand management endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_brand_success(self, client: AsyncClient, auth_token: str):
        """Test successful brand creation"""
        response = await client.post(
            "/api/brands",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "brand_name": "Aspirin 75mg",
                "manufacturer": "Bayer",
                "mrp": 15.00,
                "cost_price": 13.00,
                "default_margin": 15,
                "strength": "75mg"
            }
        )
        assert response.status_code == 201
        assert response.json()["success"] == True
    
    @pytest.mark.asyncio
    async def test_list_brands(self, client: AsyncClient, auth_token: str):
        """Test listing brands"""
        response = await client.get(
            "/api/brands",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "brands" in response.json()["data"]
    
    @pytest.mark.asyncio
    async def test_search_brands(self, client: AsyncClient, auth_token: str):
        """Test searching brands"""
        response = await client.get(
            "/api/brands?search=aspirin",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "brands" in response.json()["data"]


class TestPricing:
    """Test pricing engine"""
    
    @pytest.mark.asyncio
    async def test_calculate_price(self, client: AsyncClient, auth_token: str):
        """Test price calculation"""
        response = await client.post(
            "/api/pricing/calculate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "brand_id": 1,
                "customer_type_id": 1,
                "quantity": 100
            }
        )
        assert response.status_code == 200
        assert "unit_price" in response.json()["data"]
        assert "margin_percentage" in response.json()["data"]
    
    @pytest.mark.asyncio
    async def test_nppa_compliance_check(self, client: AsyncClient, auth_token: str):
        """Test NPPA compliance check"""
        response = await client.post(
            "/api/pricing/check-nppa",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "brand_id": 1,
                "proposed_price": 35.00
            }
        )
        assert response.status_code == 200
        assert "is_compliant" in response.json()["data"]


class TestQuotes:
    """Test quote management"""
    
    @pytest.mark.asyncio
    async def test_create_quote(self, client: AsyncClient, auth_token: str):
        """Test quote creation"""
        response = await client.post(
            "/api/quotes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "customer_name": "ABC Hospital",
                "customer_email": "abc@hospital.com",
                "customer_phone": "9876543210",
                "customer_type_id": 1,
                "validity_days": 7,
                "line_items": [
                    {
                        "brand_id": 1,
                        "quantity": 100,
                        "margin_percentage": 15
                    }
                ]
            }
        )
        assert response.status_code == 201
        assert "quote_number" in response.json()["data"]
    
    @pytest.mark.asyncio
    async def test_list_quotes(self, client: AsyncClient, auth_token: str):
        """Test listing quotes"""
        response = await client.get(
            "/api/quotes",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "quotes" in response.json()["data"]


class TestAnalytics:
    """Test analytics dashboard"""
    
    @pytest.mark.asyncio
    async def test_get_dashboard(self, client: AsyncClient, auth_token: str):
        """Test dashboard metrics"""
        response = await client.get(
            "/api/analytics/dashboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "total_revenue" in response.json()["data"]
        assert "total_quotes" in response.json()["data"]
    
    @pytest.mark.asyncio
    async def test_revenue_trend(self, client: AsyncClient, auth_token: str):
        """Test revenue trend"""
        response = await client.get(
            "/api/analytics/revenue-trend?range_type=month",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "data_points" in response.json()["data"]


class TestExport:
    """Test export functionality"""
    
    @pytest.mark.asyncio
    async def test_export_quote_pdf(self, client: AsyncClient, auth_token: str):
        """Test PDF export"""
        response = await client.post(
            "/api/quotes/1/export-pdf",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "include_terms": True,
                "include_notes": True
            }
        )
        assert response.status_code == 200
        assert "pdf_base64" in response.json()["data"]
    
    @pytest.mark.asyncio
    async def test_send_quote_email(self, client: AsyncClient, auth_token: str):
        """Test email sending"""
        response = await client.post(
            "/api/quotes/1/send-email",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "recipient_email": "test@example.com",
                "subject": "Your Quote",
                "message": "Please find your quote attached"
            }
        )
        assert response.status_code == 200


class TestSecurity:
    """Test security features"""
    
    @pytest.mark.asyncio
    async def test_missing_auth_token(self, client: AsyncClient):
        """Test missing authentication token"""
        response = await client.get("/api/brands")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_invalid_auth_token(self, client: AsyncClient):
        """Test invalid authentication token"""
        response = await client.get(
            "/api/brands",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, client: AsyncClient, auth_token: str):
        """Test SQL injection prevention"""
        response = await client.get(
            "/api/brands?search='; DROP TABLE brands; --",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200  # Should sanitize
    
    @pytest.mark.asyncio
    async def test_invalid_password_signup(self, client: AsyncClient):
        """Test weak password rejection"""
        response = await client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "weak",  # Too weak
                "full_name": "Test User"
            }
        )
        assert response.status_code == 400


class TestPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_response_time_under_200ms(self, client: AsyncClient, auth_token: str):
        """Test response time is acceptable"""
        import time
        start = time.time()
        response = await client.get(
            "/api/brands",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        elapsed = time.time() - start
        assert elapsed < 0.2  # 200ms
    
    @pytest.mark.asyncio
    async def test_pagination_performance(self, client: AsyncClient, auth_token: str):
        """Test pagination works efficiently"""
        response = await client.get(
            "/api/brands?limit=50&offset=0",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()["data"]["brands"]) <= 50


# Conftest fixtures

@pytest.fixture
async def client():
    """Create test client"""
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def auth_token(client: AsyncClient):
    """Create authenticated token"""
    signup_response = await client.post(
        "/api/auth/signup",
        json={
            "email": f"test{datetime.now().timestamp()}@example.com",
            "password": "Test@1234",
            "full_name": "Test User",
            "company_name": "Test Company"
        }
    )
    
    login_response = await client.post(
        "/api/auth/login",
        json={
            "email": signup_response.json()["data"]["email"],
            "password": "Test@1234"
        }
    )
    
    return login_response.json()["data"]["access_token"]
