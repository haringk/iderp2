import importlib.util
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1] / "__init__.py"
spec = importlib.util.spec_from_file_location("iderp_root", ROOT)
iderp_root = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iderp_root)

def test_get_version():
    assert iderp_root.get_version() == iderp_root.__version__

def test_check_installation():
    if hasattr(iderp_root, "check_installation"):
        result = iderp_root.check_installation()
        assert isinstance(result, dict)
        assert "installed" in result
    else:
        pytest.skip("check_installation() non disponibile")
