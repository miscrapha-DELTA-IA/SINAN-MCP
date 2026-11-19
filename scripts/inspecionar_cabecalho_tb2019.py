"""Inspect private TUBE/2019 four-field DBF header, without row reads."""
import json
from sinan_mcp.tb2019_dbf_header import inspect_header

if __name__ == "__main__":
    print(json.dumps(inspect_header(), ensure_ascii=False, indent=2))
