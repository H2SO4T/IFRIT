import sys

sys.path.append("/home/menendez/eurystheus")
from eurystheus.visitors.pyVisitors import CleanGuards

cleaner = CleanGuards.CleanGuards(sys.argv[1])
cleaner.setFormulas()
formulas=cleaner.getTranslation()
for formula in formulas:
    print(formula)
