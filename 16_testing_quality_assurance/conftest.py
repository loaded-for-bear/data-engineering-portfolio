import pytest
import pandas as pd

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "order_id": ["ORD-00000001"],
        "product_id":["PROD-A001"],
        "category": ["Electronics"],
        "quantity":[2],
        "unit_price":[29800.00],
        "order_date":["2024-01-15"],
        "customer_id":["CUST-001"]
    })

@pytest.fixture
def empty_df():
    # 空リスト [] は pandas が float64 に推論するため dtype を明示する
    return pd.DataFrame({
        "order_id": pd.Series([], dtype=str),
        "product_id": pd.Series([], dtype=str),
        "category": pd.Series([], dtype=str),
        "quantity": pd.Series([], dtype=float),
        "unit_price": pd.Series([], dtype=float),
        "order_date": pd.Series([], dtype=str),
        "customer_id": pd.Series([], dtype=str),
    })

@pytest.fixture
def tmp_output_dir(tmp_path):
    return tmp_path