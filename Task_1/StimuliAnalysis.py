import camelot as cm
import pandas as pd
from Task_1 import Fraction as fr

def stimuli_analysis (file_name):
    file_name = file_name.lower()

    if file_name.endswith(".pdf"):
        wordList = ['pairs', 'fraction pairs', 'left fraction', 'fraction 1', 'f1']
        actualTable = None

        # ---------------------------
        # Scraping
        # ---------------------------
        tables = cm.read_pdf(file_name, pages="all", flavor="network")
        for table in tables:
            df = table.df
            header_row = df.iloc[0].str.lower()

            if any(word.lower() in cell for word in wordList for cell in header_row):
                actualTable = df
                break
        # print(actualTable.head()) # debug row

        df = actualTable
        df.columns = df.iloc[0]     # promote header row
        df = df.iloc[1:]            # drop header row
        df = df.reset_index(drop=True)
        # print(df.head()) # debug row

        counter = 0
        fracCols = []
        for val in df.iloc[0]:
            val = str(val).replace(" ", "")
            # val = val.replace(r'^\s*$', pd.NA, regex=True)
            # ight so the above code is commented out if i decide to implement the following:
            # In case the first row has NAs and the fraction cols have not been found, I should check the next row. 
            # That would force me to implement a nested loop where i check through all the rows and then each val in each row 
            # but im just gonna leave this until i find any issues with the current system.
            spli = val.split('/')

            if len(spli) == 2 and spli[0].isdigit() and spli[1].isdigit():
                # print("valid fraction:", val,)
                fracCols.append(counter)
            counter += 1
        # print(fracCols) # debug row

        subset = df.iloc[:, fracCols]
        subset.columns = ["Fraction_1", "Fraction_2"]
        subset = subset.replace(r'^\s*$', pd.NA, regex=True)
        subset = subset.dropna(how="all").reset_index(drop=True)
        # print(subset.head()) # debug row

        # ---------------------------
        # Analysis
        # ---------------------------
        subset.insert(loc=len(subset.columns),column='pair', value=None)
        subset.insert(loc=len(subset.columns),column='Unit', value=None)
        subset.insert(loc=len(subset.columns),column='Benchmark', value=None)
        subset.insert(loc=len(subset.columns),column='Compatibility', value=None)
        subset.insert(loc=len(subset.columns),column='Relation_To_Half', value=None)


        for index, row in subset.iterrows():
            #making them fraction objects
            r1 = row['Fraction_1'].split('/')
            f1 = fr.Fraction(numerator=int(r1[0]), denominator=int(r1[1]))
            r2 = row['Fraction_2'].split('/')
            f2 = fr.Fraction(numerator=int(r2[0]), denominator=int(r2[1]))

            subset.at[index, 'pair'] = f"{str(f1)}_{str(f2)}"
            subset.at[index, 'Unit'] = f1.unit(f2)
            subset.at[index, 'Benchmark'] = f1.benchmark(f2)
            subset.at[index, 'Compatibility'] = f1.compatibility(f2)
            subset.at[index, 'Relation_To_Half'] = f1.relationToHalf(f2)

        # ---------------------------
        # Writing to csv
        # ---------------------------
        cols = ["Fraction_1", "Fraction_2"]
        subset[cols] = subset[cols].astype(str).map(lambda x: "'" + x)
        output_file = "stimuli_output.csv"
        subset.to_csv(output_file, index=False)
        return output_file
    
    elif file_name.endswith(".csv"):
        pass

    else:
        return None