"""
Database Schemas for Startup Lawyer App

Each Pydantic model corresponds to a MongoDB collection. The collection name is the lowercase of the class name.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, EmailStr
from datetime import date

class Client(BaseModel):
    name: str = Field(..., description="Client or company name")
    email: Optional[EmailStr] = Field(None, description="Primary contact email")
    phone: Optional[str] = Field(None, description="Primary contact phone")
    company_type: Optional[str] = Field(None, description="LLC, C-Corp, S-Corp, etc.")
    jurisdiction: Optional[str] = Field(None, description="State or country of formation")
    founders: Optional[List[Dict]] = Field(default_factory=list, description="List of founders with roles and ownership")

class Matter(BaseModel):
    client_id: str = Field(..., description="Associated client id")
    title: str = Field(..., description="Matter title, e.g., Incorporation, Fundraise, IP Assignment")
    status: str = Field("open", description="open, in_progress, closed")
    description: Optional[str] = Field(None, description="Matter description")
    tags: Optional[List[str]] = Field(default_factory=list)

class DocumentTemplate(BaseModel):
    name: str = Field(..., description="Template name, e.g., Mutual NDA")
    category: str = Field("contract", description="contract, corporate, hr, privacy, etc.")
    variables: List[str] = Field(default_factory=list, description="List of variable placeholders used in template body")
    body: str = Field(..., description="Template body text with {placeholders}")

class Document(BaseModel):
    client_id: Optional[str] = Field(None, description="Client id if applicable")
    matter_id: Optional[str] = Field(None, description="Matter id if applicable")
    title: str = Field(..., description="Document title")
    category: str = Field("contract")
    content: str = Field(..., description="Generated document text/content")
    template_id: Optional[str] = Field(None, description="Source template id")
    variables: Optional[Dict[str, str]] = Field(default_factory=dict, description="Variables used for generation")

class Task(BaseModel):
    client_id: Optional[str] = None
    matter_id: Optional[str] = None
    title: str
    status: str = Field("todo", description="todo, in_progress, done")
    due_date: Optional[date] = None
    assignee: Optional[str] = None
    notes: Optional[str] = None
