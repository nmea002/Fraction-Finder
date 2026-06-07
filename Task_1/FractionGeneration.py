from itertools import combinations
import pandas as pd
from Task_1 import Fraction as fr

UPPER_LIMIT = 10
LOWER_LIMIT = 1

INTENT_COLUMN_MAP = {
    # Unit
    'Both_Unit':                    ('Unit',              'Both_Unit'),
    'Includes_Unit':                ('Unit',              'Includes_Unit'),
    'Excludes_Unit':                ('Unit',              'Excludes_Unit'),
    # Benchmark
    'Both_Benchmark':               ('Benchmark',         'Both_Benchmark'),
    'Includes_Benchmark':           ('Benchmark',         'Includes_Benchmark'),
    'Excludes_Benchmark':           ('Benchmark',         'Excludes_Benchmark'),
    # Relation to half
    'Both_Above_Half':              ('Relation_To_Half',  'Both_Above_Half'),
    'Both_Below_Half':              ('Relation_To_Half',  'Both_Below_Half'),
    'Crosses':                      ('Relation_To_Half',  'Crosses'),
    'Both_Half':                    ('Relation_To_Half',  'Both_Half'),
    # Compatibility
    'Compatible':                   ('Compatibility',     'Compatible'),
    'Misleading':                   ('Compatibility',     'Misleading'),
    # Digit labels
    'Both_Only_Double_Digit':       ('Digit_Label_Pair',  'Both_Only_Double_Digit'),
    'Both_Only_Single_Digit':       ('Digit_Label_Pair',  'Both_Only_Single_Digit'),
    'Both_Mixed_Digits':            ('Digit_Label_Pair',  'Both_Mixed_Digits'),
    'Different_Digit_Labels':       ('Digit_Label_Pair',  'Different_Digit_Labels'),
    # Common components
    'Common_Numerator':             ('Common_Components', 'Common_Numerator'),
    'Common_Denominator':           ('Common_Components', 'Common_Denominator'),
    'No_Common_Components':         ('Common_Components', 'No_Common_Components'),
    # Component type
    'Common_Components':            ('Component_Type',    'Common_Components'),
    'Without_Common_Components':    ('Component_Type',    'Without_Common_Components'),
    # Gap type
    'Gap_Compatible':               ('Gap_Type',          'Gap_Compatible'),
    'Gap_Incompatible':             ('Gap_Type',          'Gap_Incompatible'),
    'Gap_Neutral':                  ('Gap_Type',          'Gap_Neutral'),
    # Pair order
    'Left_Larger':                  ('Pair_Order',        'Left_Larger'),
    'Right_Larger':                 ('Pair_Order',        'Right_Larger'),
    'Equal':                        ('Pair_Order',        'Equal'),
}

#----------------------
# Fraction Generation
#----------------------
def getProperFractions(lower=LOWER_LIMIT, upper=UPPER_LIMIT):
    lst = []
    for i in range(lower, upper + 1):
        for j in range(lower, upper + 1):
            f = fr.Fraction(numerator=i, denominator=j)
            if i < j:
                lst.append(f)
    return lst

def getFractions(lower=LOWER_LIMIT, upper=UPPER_LIMIT):
    lst = []
    for i in range(lower, upper + 1):
        for j in range(lower, upper + 1):
            f = fr.Fraction(numerator=i, denominator=j)
            lst.append(f)
    return lst

#----------------------
# Pair Generation
#----------------------
def getPairs(default="Proper", lower=LOWER_LIMIT, upper=UPPER_LIMIT):
    fracs = getProperFractions(lower, upper) if default == "Proper" else getFractions(lower, upper)
    pairs = []
    for a, b in combinations(fracs, 2):
        pairs.append((a, b))
        pairs.append((b, a))
    return pairs

#----------------------
# DataFrame Build (run once, cache as parquet)
#----------------------
def buildPairsDF(pairs: list) -> pd.DataFrame:
    """Compute all attributes in a single pass over pairs."""
    rows = []
    for f1, f2 in pairs:
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
    return pd.DataFrame(rows)

#----------------------
# Intent Filtering
#----------------------
def applyIntents(df: pd.DataFrame, intents: list) -> pd.DataFrame:
    if not intents:
        return df

    mask = pd.Series(True, index=df.index)
    for intent in intents:
        if intent not in INTENT_COLUMN_MAP:
            raise ValueError(f"Unknown intent: '{intent}'. Valid intents: {list(INTENT_COLUMN_MAP.keys())}")
        col, val = INTENT_COLUMN_MAP[intent]
        mask &= (df[col] == val)
        print(f"[DEBUG] After '{intent}': {mask.sum()} pairs remaining")

    return df[mask].copy()

#----------------------
# Main Entry Point
#----------------------
def getFilteredPairs(intents: list, lower=LOWER_LIMIT, upper=UPPER_LIMIT):
    pairs = getPairs(lower=lower, upper=upper)
    df = buildPairsDF(pairs)
    filtered = applyIntents(df, intents)
    print(f"[DONE] {len(filtered)} pairs after filtering")
    return filtered

def _build_filename(sub_filters: list) -> str:
    abbrev = {
        "Compatible": "compat", "Misleading": "misl",
        "Includes_Unit": "u+", "Excludes_Unit": "u-", "Both_Unit": "uu",
        "Includes_Benchmark": "b+", "Excludes_Benchmark": "b-", "Both_Benchmark": "bothB",
        "Both_Above_Half": "both>half", "Both_Below_Half": "both<half", "Crosses": "cross", "Both_Half": "half",
        "Left_Larger": "L>R", "Right_Larger": "R>L", "Equal": "eq",
        "Common_Numerator": "cn", "Common_Denominator": "cd", "No_Common_Components": "ncc",
        "Gap_Compatible": "gapCom", "Gap_Incompatible": "gapInc", "Gap_Neutral": "gapNeu",
    }
    parts = [abbrev.get(f, f.lower()[:4]) for f in sub_filters]
    name = "_".join(parts) if parts else "all"
    return f"stimuli_{name}.csv"