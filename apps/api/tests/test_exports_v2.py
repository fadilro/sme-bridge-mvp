import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_utility_bill_repository, get_sme_repository
from app.db.in_memory import InMemoryUtilityBillRepository, InMemorySmeRepository
from app.domain.statuses import UtilityBillStatus
from app.domain.schemas import ValidatedBillResult

client = TestClient(app)

# Setup mock repositories
test_bill_repo = InMemoryUtilityBillRepository()
test_sme_repo = InMemorySmeRepository()

def get_test_bill_repo():
    return test_bill_repo

def get_test_sme_repo():
    return test_sme_repo

@pytest.fixture(autouse=True)
def setup_dependencies():
    app.dependency_overrides[get_utility_bill_repository] = get_test_bill_repo
    app.dependency_overrides[get_sme_repository] = get_test_sme_repo
    yield
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def setup_data():
    test_bill_repo.bills = {}
    test_sme_repo.smes = {}
    
    # Add SME
    test_sme_repo.add_sme("sme_123", "plc_1", "TechCorp SME")
    
    # Add a successful bill
    bill_id = test_bill_repo.create_pending_utility_bill("sme_123", "http://test.com/file.pdf", "invoice.pdf")
    test_bill_repo.update_bill_extraction_result(bill_id, ValidatedBillResult(
        status=UtilityBillStatus.success,
        extracted_provider="TNB",
        extracted_period="2024-01",
        extracted_usage=100.0,
        extracted_unit="kWh",
        confidence="high",
        calculated_co2e=58.0,
        emission_factor_used=0.58,
        validation_reasons=[]
    ))

def test_csv_export_format():
    response = client.get("/exports/csv?sme_id=sme_123")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    content = response.text
    lines = content.strip().split("\r\n")
    headers = lines[0].split(",")
    
    # Verify CSI columns
    assert "SME Name" in headers
    assert "Period" in headers
    assert "CO2e" in headers
    assert "S3 File Link" in headers
    
    # Verify data
    data = lines[1].split(",")
    assert "TechCorp SME" in data
    assert "2024-01" in data
    assert "58.0" in data

def test_xlsx_export_format():
    response = client.get("/exports/xlsx?sme_id=sme_123")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    # Verify it's a non-empty binary file
    assert len(response.content) > 100
    assert "xlsx" in response.headers["content-disposition"].lower()

def test_pdf_export_smoke():
    response = client.get("/exports/pdf?sme_id=sme_123")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
