import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_billing_case(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/billing-cases",
        headers=auth_headers,
        json={
            "patient_name": "John Doe",
            "payer_name": "UnitedHealthcare",
            "claim_number": "CLM-2024-001",
            "amount_billed": 1500.00,
            "denial_code": "CO-4",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["patient_name"] == "John Doe"
    assert data["claim_number"] == "CLM-2024-001"
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_list_billing_cases(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/billing-cases", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # API returns PaginatedResponse: { items: [...], total: int, skip: int, limit: int }
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_create_call_job(client: AsyncClient, auth_headers: dict):
    # Create billing case first
    case_resp = await client.post(
        "/api/v1/billing-cases",
        headers=auth_headers,
        json={
            "patient_name": "Jane Smith",
            "payer_name": "Aetna",
            "claim_number": "CLM-2024-002",
        },
    )
    case_id = case_resp.json()["id"]

    # Create call job
    response = await client.post(
        "/api/v1/call-jobs",
        headers=auth_headers,
        json={
            "billing_case_id": case_id,
            "phone_number": "+15551234567",
            "priority": 1,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["phone_number"] == "+15551234567"
    assert data["status"] == "pending"
    assert data["priority"] == 1


@pytest.mark.asyncio
async def test_list_call_jobs(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/call-jobs", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_ticket(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/tickets",
        headers=auth_headers,
        json={
            "title": "Follow up on denied claim",
            "description": "Need to submit appeal documents",
            "priority": "high",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Follow up on denied claim"
    assert data["status"] == "open"
    assert data["priority"] == "high"
