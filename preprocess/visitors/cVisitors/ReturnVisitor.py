from pycparser import c_ast

class ReturnVisitor(c_ast.NodeVisitor):
    retVal=None
    decVal=None
    def visit_Return(self, node):
#        print(node.expr.name)
        self.retVal=node.expr.name

    def getRetVal(self):
        return self.retVal

    def visit_Decl(self,node):
         if(self.retVal):
             if(node.name==self.retVal):
                 self.decVal=node

    def getDecVal(self):
        return self.decVal
