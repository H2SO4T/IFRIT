from pycparser import c_ast

class GlobalVisitor:
    class GlobalVisitorDecls(c_ast.NodeVisitor):
        def __init__(self):
            self.decs=[]            
            self.infunc=False

        def visit_FuncDef(self, node):
            self.infunc=True
            self.generic_visit(node)
            self.infunc=False
            
        def visit_Decl(self,node):
            if not(self.infunc):
                self.decs.append(node)
                    
        def getDecs(self):
            return self.decs
                        
    def getVariables(self,ast):
        self.visitorDecl = self.GlobalVisitorDecls()
        self.visitorDecl.visit(ast)
        return self.visitorDecl.getDecs() 
