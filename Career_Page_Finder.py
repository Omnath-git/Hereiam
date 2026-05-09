import pandas as pd
from googlesearch import search
import time
import os

# 1. अपनी फाइल का नाम सेट करें
input_file = 'NIFTY500.csv'

def get_career_page():
    if not os.path.exists(input_file):
        print(f"--- ERROR: {input_file} फ़ाइल नहीं मिली! ---")
        return

    print("--- प्रक्रिया शुरू: करियर पेज सर्च इंजन ---")

    while True:
        # CSV लोड करें
        df = pd.read_csv(input_file)

        if 'Career Page' not in df.columns:
            df['Career Page'] = ""
        
        # केवल खाली रिकॉर्ड्स को फिल्टर करें
        pending_rows = df[df['Career Page'].isna() | (df['Career Page'] == "") | (df['Career Page'] == "Not Found")]

        if pending_rows.empty:
            print("\n--- सभी रिकॉर्ड्स सफलतापूर्वक पूरे हो चुके हैं! ---")
            break

        current_index = pending_rows.index[0]
        company_name = df.at[current_index, 'Company Name']

        print(f"\n[खोज जारी] कंपनी: {company_name} (Row Index: {current_index})")

        # सर्च क्वेरी को थोड़ा सरल और प्रभावी बनाया गया है
        query = f"{company_name} careers"
        
        found_link = ""
        try:
            # pause=2 यहाँ Google को ब्लॉक करने से रोकता है
            search_results = search(query, num_results=1, lang="en")
            
            for link in search_results:
                found_link = link
                break 
            
            if found_link:
                df.at[current_index, 'Career Page'] = found_link
                # कंसोल में जानकारी दिखाएं
                print(f"SUCCESS: लिंक मिल गया! -> {found_link}")
            else:
                df.at[current_index, 'Career Page'] = "Not Found"
                print("FAILED: कोई लिंक नहीं मिला।")

            # CSV में तुरंत अपडेट करें
            df.to_csv(input_file, index=False)
            print(f"INFO: CSV फाइल में सेव कर दिया गया है।")

            # ब्लॉक होने से बचने के लिए 10-15 सेकंड का इंतजार
            print("अगली कंपनी के लिए 12 सेकंड का ब्रेक...")
            time.sleep(12)

        except Exception as e:
            error_msg = str(e)
            print(f"CRITICAL ERROR: {error_msg}")
            
            if "429" in error_msg:
                print("GOOGLE ALERT: बहुत अधिक रिक्वेस्ट! 10 मिनट का लंबा ब्रेक ले रहे हैं...")
                time.sleep(600) # 10 मिनट का ब्रेक
            else:
                time.sleep(30)
            continue

if __name__ == "__main__":
    get_career_page()