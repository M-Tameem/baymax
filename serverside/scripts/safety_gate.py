# safety_gate.py

import subprocess

MODEL_NAME = "phi"  # or mistral, llama3, etc.
TIMEOUT_SECONDS = 20

def run_ollama_model(prompt: str, model: str = MODEL_NAME, timeout: int = TIMEOUT_SECONDS) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout
        )
        return result.stdout.decode("utf-8").strip()
    except subprocess.TimeoutExpired:
        print("[SAFETY GATE] ❌ Timeout from model.")
        return ""
    except Exception as e:
        print(f"[SAFETY GATE] ❌ Unexpected error: {e}")
        return ""

def safety_check(drug_dosage: str, verbose: bool = False) -> bool:
    """
    Ask a local LLM if the dosage is safe for an average adult.
    Expect a strict binary answer: SAFE or UNSAFE.
    """
    prompt = (
        f"You are a clinical dosage verification system.\n\n"
        f"A clinician has entered the following medication order:\n"
        f"\"{drug_dosage.strip()}\"\n\n"
        f"Respond with only one word:\n"
        f"- SAFE (if the dosage is medically appropriate for an average adult)\n"
        f"- UNSAFE (if the dosage is clearly dangerous, excessive, or toxic)\n\n"
        f"Only return 'SAFE' or 'UNSAFE'. No extra text. No explanation."
    )

    response = run_ollama_model(prompt)
    answer = response.strip().splitlines()[0].strip().upper()

    if verbose:
        print(f"[SAFETY GATE RESPONSE]: {answer}")

    return answer == "SAFE"

# ---------------- TEST HARNESS ------------------

if __name__ == "__main__":
    test_cases = [
        "Ibuprofen 200mg",
        "Ibuprofen 4000mg",
        "Ibuprofen 3 grams",
        "Morphine 1000 mg",
        "Acetaminophen 5000 mg",
        "Metformin 1000mg BID",
        "Amoxicillin 250 mg",
        "Furosemide 20mg",
        "Aspirin 650 mg",
        "Tylenol 15000 mg",
    ]

    for case in test_cases:
        print(f"\n=== Testing: {case} ===")
        result = safety_check(case, verbose=True)
        print(f"Final verdict: {'✅ SAFE' if result else '⚠️ UNSAFE'}")
