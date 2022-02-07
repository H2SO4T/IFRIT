from pycparser import c_ast

class LocalVisitor:
    class LocalVisitorDecls(c_ast.NodeVisitor):
        def __init__(self):
            self.decs=[]            
            self.infunc=False

        def visit_FuncDef(self, node):
            self.infunc=True
            self.generic_visit(node)
            self.infunc=False

        def visit_FuncDecl(self, node):
            self.infuncDecl=True
            self.generic_visit(node)
            self.infuncDecl=False
 
        def visit_TypeDecl(self,node):
            if self.infunc and not(self.infuncDecl):
                self.decs.append(node)
                    
        def getDecs(self):
            return self.decs
                        
    def getVariables(self,ast):
        self.visitorDecl = self.LocalVisitorDecls()
        self.visitorDecl.visit(ast)
        vars = self.visitorDecl.getDecs()
        return list([var.declname for var in vars])
