import camelot as cm
import pandas as pd
from openpyxl import Workbook
from Task_1 import Fraction as fr

def _find_frac_cols(df):
    """Scan first data row for valid 'num/denom' fractions, return col indices."""
    frac_cols = []
    for i, val in enumerate(df.iloc[0]):
        val = str(val).replace(" ", "").lstrip("'")
        parts = val.split('/')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            frac_cols.append(i)
    return frac_cols


def _prep_subset(df, frac_cols):
    """Slice frac cols, clean, drop empty rows."""
    subset = df.iloc[:, frac_cols].copy()
    subset.columns = ["Left_Fraction", "Right_Fraction"]
    subset = subset.replace(r'^\s*$', pd.NA, regex=True)
    subset = subset.dropna(how="all").reset_index(drop=True)
    return subset


def _build_rows(subset):
    """Iterate pair by pair and return list of annotated dicts."""
    rows = []
    for _, row in subset.iterrows():
        r1 = str(row['Left_Fraction']).lstrip("'").split('/')
        r2 = str(row['Right_Fraction']).lstrip("'").split('/')
        f1 = fr.Fraction(int(r1[0]), int(r1[1]))
        f2 = fr.Fraction(int(r2[0]), int(r2[1]))
        rows.append({
            'Fraction_Pair':        f"{f1}_{f2}",
            'Left_Fraction':        f"'{str(f1)}",
            'Right_Fraction':       f"'{str(f2)}",
            'Compatibility':        f1.compatibility(f2),
            'Unit':                 f1.unit(f2),
            'Benchmark':            f1.benchmark(f2),
            'Relation_To_Half':     f1.relationToHalf(f2),
            'Left_Digit_Label':     f1.digitLabel(),
            'Right_Digit_Label':    f2.digitLabel(),
            'Digit_Label_Pair':     f1.digitLabelPair(f2),
            'Decimal_Distance':     f"{f1.decimalDistance(f2):.2f}",
            'Numerator_Distance':   f"{f1.numDistance(f2)}",
            'Denominator_Distance': f"{f1.denomDistance(f2)}",
            'Common_Components':    f1.commonComponents(f2),
            'Component_Type':       f1.componentType(f2),
            'Pair_Order':           f1.pairOrder(f2),
            'Left_Gap':             f1.gap(),
            'Right_Gap':            f2.gap(),
            'Pair_Gap_Distance':    abs(f1.gap() - f2.gap()),
            'Gap_Type':             f1.gapType(f2),
        })
    return rows


def _save_xlsx(result, output_file):
    """Write DataFrame to xlsx, forcing fraction cols to text format with '@'."""
    wb = Workbook()
    ws = wb.active

    ws.append(list(result.columns))

    frac_indices = [result.columns.get_loc('Left_Fraction') + 1,
                    result.columns.get_loc('Right_Fraction') + 1]

    for row_idx, row in enumerate(result.itertuples(index=False), start=2):
        for col_idx, val in enumerate(row, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=str(val))
            if col_idx in frac_indices:
                cell.number_format = '@'

    wb.save(output_file)


def stimuli_analysis(file_name):
    file_name = file_name.lower()
    wordList  = ['pairs', 'fraction pairs']
    leftList  = ['left fraction', 'fraction 1', 'f1', 'fraction_1', 'left_fraction']
    rightList = ['right fraction', 'fraction 2', 'f2', 'fraction_2', 'right_fraction']

    # ---------------------------
    # PDF
    # ---------------------------
    if file_name.endswith(".pdf"):
        actualTable = None
        tables = cm.read_pdf(file_name, pages="all", flavor="network")
        for table in tables:
            df = table.df
            header_row = df.iloc[0].str.lower()
            if any(word.lower() in cell for word in wordList for cell in header_row):
                actualTable = df
                break

        df = actualTable
        df.columns = df.iloc[0]
        df = df.iloc[1:].reset_index(drop=True)

        frac_cols = _find_frac_cols(df)
        subset = _prep_subset(df, frac_cols)
        result = pd.DataFrame(_build_rows(subset))

        output_file = file_name.replace(".pdf", "_annotated.csv")
        result.to_csv(output_file, index=False)
        return result

    # ---------------------------
    # CSV
    # ---------------------------
    elif file_name.endswith(".csv"):
        df = pd.read_csv(file_name, dtype=str)

        headers   = [c.lower().strip() for c in df.columns]
        left_col  = next((df.columns[i] for i, h in enumerate(headers) if h in [x.lower() for x in leftList]), None)
        right_col = next((df.columns[i] for i, h in enumerate(headers) if h in [x.lower() for x in rightList]), None)

        if left_col and right_col:
            subset = df[[left_col, right_col]].copy()
            subset.columns = ["Left_Fraction", "Right_Fraction"]
            subset = subset.replace(r'^\s*$', pd.NA, regex=True)
            subset = subset.dropna(how="all").reset_index(drop=True)
        else:
            frac_cols = _find_frac_cols(df)
            subset = _prep_subset(df, frac_cols)

        result = pd.DataFrame(_build_rows(subset))
        output_file = file_name.replace(".csv", "_annotated.csv")
        result.to_csv(output_file, index=False)
        return result

    # ---------------------------
    # XLSX
    # ---------------------------
    elif file_name.endswith(".xlsx"):
        df = pd.read_excel(file_name, dtype=str)

        headers   = [c.lower().strip() for c in df.columns]
        left_col  = next((df.columns[i] for i, h in enumerate(headers) if h in [x.lower() for x in leftList]), None)
        right_col = next((df.columns[i] for i, h in enumerate(headers) if h in [x.lower() for x in rightList]), None)

        if left_col and right_col:
            subset = df[[left_col, right_col]].copy()
            subset.columns = ["Left_Fraction", "Right_Fraction"]
            subset = subset.replace(r'^\s*$', pd.NA, regex=True)
            subset = subset.dropna(how="all").reset_index(drop=True)
        else:
            frac_cols = _find_frac_cols(df)
            subset = _prep_subset(df, frac_cols)

        result = pd.DataFrame(_build_rows(subset))
        result.attrs["output_name"] = file_name.replace(".xlsx", "_annotated.csv")
        return result

    else:
        return None
