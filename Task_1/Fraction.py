class Fraction:
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
    
    # Filter Functions
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
        # I discoverd on the stimuli excel sheet that fractions with common denominators or commmon numerators
        # were left bank on the compatibility column. Wasn't sure if I should add this or not. 
        # if (self.numerator == f2.numerator) or (self.denominator == f2.denominator):
        #     return 'Unknown'
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

