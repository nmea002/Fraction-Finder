class Fraction:
    #----------------------
    # Initialization 
    #----------------------
    def __init__ (self, numerator, denominator):
        self.numerator = numerator
        self.denominator = denominator
        self.decimal = numerator / denominator
    
    def __str__(self):
        return f'{self.numerator}/{self.denominator}'
    
    def __eq__(self, other):
        if isinstance(other, Fraction): 
            if (self.numerator == other.numerator) and (self.denominator == other.denominator):
                return True 
        return False 
    
    def __hash__(self):
        return hash((self.numerator, self.denominator))
    
    # ----------------------
    # Filter Labeling Functions
    # ----------------------           
    def unit(self, f2):
        if self.numerator == 1 and f2.numerator == 1:
            return 'Both_Unit'
        elif self.numerator == 1 or f2.numerator == 1:
            return 'Includes_Unit'
        else:
            return 'Excludes_Unit'
    
    def benchmark(self, f2):
        benchmarks = ['1/2', '1/3', '1/4', '3/4', '2/3']
        f1 = str(self)
        f2 = str(f2)
        if f1 in benchmarks and f2 in benchmarks:
            return 'Both_Benchmark'
        elif f1 in benchmarks or f2 in benchmarks:
            return 'Includes_Benchmark'
        else:
            return 'Excludes_Benchmark'

    def relationToHalf(self, f2):
        if self.decimal > 0.5 and f2.decimal > 0.5:
            return 'Both_Above_Half'
        elif self.decimal < 0.5 and f2.decimal < 0.5:
            return 'Both_Below_Half'
        elif self.decimal > 0.5 or f2.decimal > 0.5:
            return 'Crosses'
        else:
            return 'Both_Half'

    def compatibility(self, f2):
        if self.decimal > f2.decimal:
            if (self.numerator > f2.numerator) or (self.denominator > f2.denominator):
                #2/8_1/9
                return 'Compatible'
            else:
                #1/4_2/9
                return 'Misleading'
        elif self.decimal < f2.decimal:
            if (self.numerator < f2.numerator) or (self.denominator < f2.denominator):
                return 'Compatible'
            else:
                return 'Misleading'
        else:  
            return 'Unknown'
    
    def digitLabel(self):
        num_digits = len(str(self.numerator))
        denom_digits = len(str(self.denominator))
        if num_digits == 2 and denom_digits == 2:
            return "Only_Double_Digit"
        elif num_digits == 1 and denom_digits == 1:
            return "Only_Single_Digit"
        else:
            return "Mixed_Digits"
    
    def digitLabelPair(self, f2):
        f1_label = self.digitLabel()
        f2_label = f2.digitLabel()
        if f1_label == "Only_Double_Digit" and f2_label == "Only_Double_Digit":
            return "Both_Only_Double_Digit"
        elif f1_label == "Only_Single_Digit" and f2_label == "Only_Single_Digit":
            return "Both_Only_Single_Digit"
        elif f1_label == "Mixed_Digits" and f2_label == "Mixed_Digits":
            return "Both_Mixed_Digits"
        else:
            return "Different_Digit_Labels"


    def commonComponents(self, f2):
        if self.numerator == f2.numerator:
            return 'Common_Numerator'
        elif self.denominator == f2.denominator:
            return 'Common_Denominator'
        else:
            return 'No_Common_Components'
    
    def componentType(self, f2):
        if self.commonComponents(f2) != 'No_Common_Components':
            return 'Common_Components'
        else:
            return 'Without_Common_Components'
    
    def numDistance(self, f2):
        return self.numerator - f2.numerator
    
    def denomDistance(self, f2):
        return self.denominator - f2.denominator
    
    def decimalDistance(self, f2):
        return self.decimal - f2.decimal
    
    def gap(self):
        return abs(self.denominator - self.numerator) 
    
    def gapType(self, f2):
        f1gap = self.gap()
        f2gap = f2.gap()

        if self.decimal > f2.decimal:
            if f1gap < f2gap:
                return 'Gap_Compatible'
            elif f1gap > f2gap:
                #33/46 vs 5/9
                return 'Gap_Incompatible'
            else:
                return 'Gap_Neutral'
        elif self.decimal < f2.decimal:
            if f1gap > f2gap:
                return 'Gap_Compatible'
            elif f1gap < f2gap:
                return 'Gap_Incompatible'
            else:
                return 'Gap_Neutral'
        else:
            return 'Unknown'
        
    def pairOrder(self, f2):
        if self.decimal > f2.decimal:
            return 'Left_Larger'
        elif self.decimal < f2.decimal:
            return 'Right_Larger'
        else:
            return 'Equal'  
          
    def proper(self):
        if self.numerator < self.denominator:
            return 'Proper'
        elif self.numerator > self.denominator:
            return 'Improper'
        else:
            return 'Whole'