from collections import defaultdict
import csv
from Task_1 import Fraction as fr
from Task_1 import FractionGeneration as fgr

#Fraction Getters 
def getFractions():
    lst = []
    for i in range(1,11):
        for j in range(1,11):
            if i == j:
                continue
            f = fr.Fraction(numerator=i,denominator=j)
            lst.append(f)
    return lst 

def getProperFractions():
    lst = []
    for i in range(1,11):
        for j in range(1,11):
            if i >= j:
                continue
            f = fr.Fraction(numerator=i,denominator=j)
            lst.append(f)
    return lst 

#Pair Getters
def getPairs():
    fracs = getProperFractions()
    # if intent == "Proper":
    #     fracs = Fraction.getProperFractions()
    # else:
    #     fracs = Fraction.getFractions()
        
    pairs_dict = defaultdict(list)
    pairs = []
    for frac1 in fracs:
        for frac2 in fracs:
            if frac1 == frac2:
                continue 
            
            if frac2 in pairs_dict and frac1 in pairs_dict[frac2]:
                continue 
            else:
                pairs.append((frac1, frac2))
                pairs_dict[frac1].append(frac2)
    return pairs 

def getFilteredPairs(intents):
    all_pairs = fgr.getPairs()
    print("Initial pairs:", len(all_pairs))
    for intent in intents:
        all_pairs = fgr.filtering(all_pairs, intent)
        print(f"After {intent}:", len(all_pairs))
        
    with open('all_pairs.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Distance', 'Fraction_Pair', 'Left_Fraction', 'Right_Fraction', 'Compatibility',
                            'Unit', 'Benchmark', 'Relation_To_Half'])

        for f1, f2 in all_pairs:
            comp1 = f1.compatibility(f2)
            unit1 = f1.unit(f2)
            benchmark1 = f1.benchmark(f2)
            rel1 = f1.relationToHalf(f2)
            writer.writerow([
                f"{f1.decimal - f2.decimal:.2f}",
                f"{f1}_{f2}",  
                f"'{f1}", 
                f"'{f2}",
                f"{comp1}",
                f"{unit1}",
                f"{benchmark1}",
                f"{rel1}"
            ])
    return 'all_pairs.csv'

#Intent Matching
def filtering (all_pairs, intent):
    for f1,f2 in all_pairs[:]:
        comp = f1.compatibility(f2)
        unit = f1.unit(f2)
        benchmark = f1.benchmark(f2)
        rel = f1.relationToHalf(f2)

        match intent:
            case 'Both_Unit':
                if unit != 'Both_Unit':
                    all_pairs.remove((f1,f2))
            case 'Includes_Unit':
                if unit != 'Includes_Unit':
                    all_pairs.remove((f1,f2))
            case 'Excludes_Unit': 
                if unit != 'Excludes_Unit':
                    all_pairs.remove((f1,f2))

            case 'Both_Benchmark':
                if benchmark != 'Both_Benchmark':
                    all_pairs.remove((f1,f2))
            case 'Includes_Benchmark':
                if benchmark != 'Includes_Benchmark':
                    all_pairs.remove((f1,f2))
            case 'Excludes_Benchmark':
                if benchmark != 'Excludes_Benchmark':
                    all_pairs.remove((f1,f2))

            case 'Both_Above_Half':
                if rel != 'Both_Above_Half':
                    all_pairs.remove((f1,f2))
            case 'Both_Below_Half':
                if rel != 'Both_Below_Half':
                    all_pairs.remove((f1,f2))  
            case 'Crosses':
                if rel != 'Crosses':
                    all_pairs.remove((f1,f2))     
            case 'Both_Half':  
                if rel != 'Both_Half':
                    all_pairs.remove((f1,f2)) 

            case 'Compatible':
                if comp != 'Compatible':
                    all_pairs.remove((f1,f2))  
            case 'Misleading':
                if comp != 'Misleading':
                    all_pairs.remove((f1,f2))  
    return all_pairs

