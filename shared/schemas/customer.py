# -*- coding: utf-8 -*-
"""
shared/schemas/customer.py
Pydantic-compatible data schemas for Customer entity.
Shared between backend API and frontend validation.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class CustomerSchema:
    """Schema cho hồ sơ khách hàng mới."""
    full_name:    str
    phone_number: str
    id_number:    str
    segment:      str = "MASS"          # MASS | PRIME | DIAMOND
    gender:       str = "M"             # M | F
    date_of_birth: str = "1995-01-01"
    address:      str = "Hà Nội"
    occupation:   str = "Nhân viên văn phòng"
    income_range: str = "20-40tr"
    marital_status: str = "Độc thân"
    casa_balance: float = 1_000_000.0
    branch_code:  str = "CN001"
    email:        Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class TransactionSchema:
    """Schema cho giao dịch mới tại quầy."""
    cif_number:    str
    service_name:  str
    amount:        float
    channel:       str = "QUẦY"         # QUẦY | VPBANK NEO | POS/ATM
    service_group: str = "Dịch vụ ngân hàng"
    branch_code:   str = "CN001"
    teller_id:     str = "GDV001"
    notes:         str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class ProductSchema:
    """Schema cho sản phẩm tài chính mới."""
    Ten_san_pham:   str
    Nhom:           str                  # Tiết kiệm | Thẻ | Vay | Bảo hiểm | Đầu tư | Ngoại tệ
    Gia_tri_cot_loi: str
    Ma_SP:          str = ""             # Auto-generated if empty
    Phan_khuc:      str = "ALL"          # MASS | PRIME | DIAMOND | ALL
    So_tien_toi_thieu: float = 0.0
    Lai_suat_Phi:   str = "Theo biểu phí chuẩn"
    Uu_tien:        int = 5

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class ConsultationLogSchema:
    """Schema cho nhật ký tư vấn & chốt đơn."""
    cif_number:    str
    customer_name: str
    product_name:  str
    status:        str                   # CHỐT THÀNH CÔNG | ĐANG CÂN NHẮC | TỪ CHỐI
    category:      str = "Tài chính"
    deal_amount:   str = "0 VND"
    notes:         str = ""
    teller_name:   str = "Giao dịch viên"
    teller_code:   str = "GDV001"

    def to_dict(self) -> dict:
        return self.__dict__.copy()
