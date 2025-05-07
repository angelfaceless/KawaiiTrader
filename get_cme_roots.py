import databento as db
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv() # Load .env file if present

def get_all_cme_futures_roots():
    API_KEY = os.getenv("DATABENTO_API_KEY")
    if not API_KEY:
        print("Error: DATABENTO_API_KEY environment variable not set.")
        print("Please ensure a .env file with DATABENTO_API_KEY=\"your_key\" exists in the same directory as the script, or that the environment variable is set globally.")
        return None

    client = db.Historical(key=API_KEY)

    start_date_query = "2024-01-01"
    end_date_query = "2024-01-02"  # <--- CORRECTED: End date must be after start date

    print(f"Requesting all instrument definitions for GLBX.MDP3 from {start_date_query} to {end_date_query}...")

    try:
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            schema="definition",
            symbols="ALL_SYMBOLS",
            start=start_date_query,
            end=end_date_query
        )
        df = data.to_df()
    except Exception as e:
        print(f"Error fetching instrument definitions: {e}")
        return None

    if df.empty:
        print("No instrument definitions returned.")
        return None

    print(f"Successfully fetched {len(df)} instrument definitions.")

    if "security_type" not in df.columns:
        print("Error: 'security_type' column not found in definitions. Cannot filter for futures.")
        print("Available columns:", df.columns.tolist())
        return None
        
    futures_df = df[df["security_type"] == "FUT"].copy()

    if futures_df.empty:
        print("No futures contracts (security_type=\"FUT\") found in the definitions.")
        return None

    print(f"Found {len(futures_df)} futures contract definitions.")

    potential_roots = set()
    if 'asset' in futures_df.columns:
        print("Using 'asset' column for roots.")
        potential_roots.update(futures_df['asset'].dropna().astype(str).tolist())
    elif 'raw_symbol' in futures_df.columns:
        print("Using 'raw_symbol' column and parsing for roots.")
        def extract_root_from_raw(raw_sym):
            if not isinstance(raw_sym, str):
                return None
            match = []
            for char in raw_sym:
                if char.isalpha():
                    match.append(char)
                else:
                    break
            root = "".join(match)
            if 2 <= len(root) <= 4:
                return root.upper()
            return None

        futures_df['extracted_root'] = futures_df['raw_symbol'].apply(extract_root_from_raw)
        potential_roots.update(futures_df['extracted_root'].dropna().tolist())
    else:
        print("Error: Neither 'asset' nor 'raw_symbol' column found for root extraction.")
        return None

    cleaned_futures_roots = sorted(list(set(
        r for r in potential_roots 
        if r and isinstance(r, str) and 1 < len(r) <= 4 and r.isalpha() and r.isupper()
    )))
    
    print("\nDiscovered and Filtered CME Futures Roots:")
    if cleaned_futures_roots:
        print(f"Total unique roots found: {len(cleaned_futures_roots)}")
        return cleaned_futures_roots
    else:
        print("No roots found after filtering.")
        print("Potential roots before final filter:", sorted(list(potential_roots)))
        return None

if __name__ == "__main__":
    roots = get_all_cme_futures_roots()
    if roots:
        # On your local machine, this will save to the directory where you run the script.
        output_file_path = "cme_futures_roots.txt" 
        with open(output_file_path, "w") as f:
            for root in roots:
                f.write(root + "\n")
        print(f"Saved {len(roots)} roots to {output_file_path}")
        if len(roots) > 100:
            print("First 100 roots:", roots[:100])
        else:
            print("All roots:", roots)
    else:
        print("Failed to retrieve or process futures roots.")

