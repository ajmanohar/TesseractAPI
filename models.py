# models.py
"""
Pydantic data models and schemas defining request/response structures
for identity extraction, validation, and Form-C data contracts.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class HealthStatusResponse(BaseModel):
    """
    Response schema for system health probes.
    """
    status: str = Field(..., description="Overall status indicator")
    tesseract_detected: bool = Field(..., description="Indicates if Tesseract binary is accessible")
    tesseract_path: str = Field(..., description="Active path to the Tesseract engine")


class PassportDataResponse(BaseModel):
    """
    Standardized payload returning parsed MRZ fields matching
    the Bureau of Immigration Form-C fields (Doc 9303 standard).
    """
    valid_mrz: bool = Field(..., description="True if cryptographic checksum passes")
    document_type: Optional[str] = Field(None, description="Document identifier (e.g., P)")
    country: Optional[str] = Field(None, description="Issuing country code (e.g., GBR, USA)")
    surname: Optional[str] = Field(None, description="Guest's family name / surname")
    names: Optional[str] = Field(None, description="Guest's given names")
    passport_number: Optional[str] = Field(None, description="Official passport/travel document number")
    nationality: Optional[str] = Field(None, description="3-letter nationality code")
    date_of_birth: Optional[str] = Field(None, description="DOB in YYMMDD format")
    sex: Optional[str] = Field(None, description="Gender (M, F, or X)")
    expiration_date: Optional[str] = Field(None, description="Document expiry date in YYMMDD format")
    raw_mrz_text: Optional[str] = Field(None, description="Raw OCR-B text lines recognized by engine")
    warnings: List[str] = Field(default_factory=list, description="List of parsing or checksum warnings")