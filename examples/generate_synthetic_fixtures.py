from pathlib import Path

from acoustic_sandbox.synthetic import write_fixture_set

if __name__ == "__main__":
    output = Path(__file__).resolve().parents[1] / "generated-fixtures"
    for path in write_fixture_set(output):
        print(path)
