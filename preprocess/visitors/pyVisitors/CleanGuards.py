import parser
import ast
from math import sin, cos, tan
from .VisitorCleaner import VisitorCleaner

class CleanGuards:
    def __init__(self,fileName={}):
        self.fileName=fileName

    def setFormulas(self,formulas=None):
        if formulas:
            self.formulas=formulas
        else:
            self.formulas=[]
            with open(self.fileName) as f:
                fileLines = f.readlines()
            for line in fileLines:
                self.formulas.append(line)
#                print(line)

    def getTranslation(self):
        translations=[]
        for index, f in enumerate(self.formulas):
#            print('{} - {:*^76}'.format(index, f))
            visitor = VisitorCleaner()
            visitor.visit(ast.parse(str(f)))
            translations.append(' '.join(map(str, visitor.tokens)))
        return translations
