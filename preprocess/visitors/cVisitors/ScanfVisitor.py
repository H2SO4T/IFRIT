from pycparser import c_ast

class ScanfVisitor:
    class ScanfVisitorNames(c_ast.NodeVisitor):
        def __init__(self):
            self.varNames=[]

        def visit_FuncCall(self, node):
            if (node.name.name == 'scanf'):
                for expr in node.args.exprs:
                    if isinstance(expr,c_ast.UnaryOp):
                        self.varNames.append(expr.expr.name)

        def getNames(self):
            return self.varNames
                        
    class ScanfVisitorDecls(c_ast.NodeVisitor):
        def __init__(self,varNames):
            self.decs=[]
            self.varNames=varNames

        def visit_Decl(self,node):
            if(len(self.varNames)>0):
                if(node.name in self.varNames):
                    self.decs.append(node)

        def getDecVal(self):
            return self.decs

    def getVariables(self,ast):
        self.visitorNames = self.ScanfVisitorNames()
        self.visitorNames.visit(ast)
        self.visitorDecl = self.ScanfVisitorDecls(self.visitorNames.varNames)
        self.visitorDecl.visit(ast)
        return self.visitorDecl.getDecVal() 
