from pycparser import c_ast

class RemoverVisitor:
    class ScanfVisitorDecls(c_ast.NodeVisitor):
        def __init__(self):
            self.decs=[]

        def visit_Decl(self,node):
            node = None

    def getVariables(self,ast):
        self.visitorNames = self.ScanfVisitorNames()
        self.visitorNames.visit(ast)
        self.visitorDecl = self.ScanfVisitorDecls(self.visitorNames.varNames)
        self.visitorDecl.visit(ast)
        return self.visitorDecl.getDecVal() 
