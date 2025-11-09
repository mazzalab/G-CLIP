from tools.emedgene_csv_converter_core import normalize_hpo_field, load_hpo_list
from tools.emedgene_csv_converter_core import resource_path
import os


def test_normalize_hpo_field():
    text = "HP:0001250 and also HP:0012345 but malformed HP:A99"
    result = normalize_hpo_field(text)
    assert result == ["HP:0001250", "HP:0012345"]


def test_load_hpo_list_has_codes():
    hpo_path = resource_path(os.path.join("assets", "hp.obo"))
    codes = load_hpo_list(hpo_path)
    assert isinstance(codes, set)
    assert "HP:0000001" in codes  # root term in HPO
