from pycparser import c_ast

class ReturnLineVisitor():
    class ReturnLineVisitorDecls(c_ast.NodeVisitor):
        def __init__(self,linenum):
            self.linenum=linenum
            self.path=[]
            self.reached=False
            self.b1 = c_ast.Return(c_ast.ExprList([c_ast.Constant(value='-1',type='int')]))
        
        def visit_Return(self,node):
            if node != self.b1:
                node.expr=c_ast.ExprList([c_ast.ID(name="inst_block")])
        
        def generic_visit(self, node):
            #print(node.coord)
            if(isinstance(node,c_ast.Compound)):
                for pos,child in enumerate(node.children()):
                    if child[1].coord and child[1].coord.line == self.linenum:
                        #print(pos)
                        #print(type(node))
                        node.block_items.insert(pos+1,self.b1)
                        #print(type(node).__name__)
                        #print(node.coord)
                        #print(child[1].coord.line)
                        self.reached=True
            for c_name, c in node.children():
                if c_name in ["stmt","iftrue","iffalse"]:
                    if not(self.reached):
                        self.path.insert(0,c)
                if (c != self.b1):
                    self.visit(c)
                if c_name in ["stmt","iftrue","iffalse"]:
                    if not(self.reached):
                        self.path.pop(0)
    def instrument(self,ast,linenum):
        value=c_ast.Constant(value='0',type='int')
        typeid=c_ast.TypeDecl(declname='inst_block',quals=[],type=c_ast.IdentifierType(['int']))
        blockdecl=c_ast.Decl(name='inst_block',quals=[],storage=[],funcspec=[],bitsize=None,init=value,type=typeid)
        ast.body.block_items.insert(0,blockdecl)
        blockplus=c_ast.UnaryOp(op="p++",expr=c_ast.ID("inst_block"))
        visitor=self.ReturnLineVisitorDecls(linenum)
        visitor.generic_visit(ast)
        for element in visitor.path:
            element.block_items.insert(0,blockplus)
    # def visit_If(self,node):
    #     if not(self.reached):
    #         self.path.insert(0,node)
    #     self.generic_visit(node)
    #     if not(self.reached):
    #         self.path.pop(0)
    # def visit_For(self,node):
    #     if not(self.reached):
    #         self.path.insert(0,node)
    #     self.generic_visit(node)
    #     if not(self.reached):
    #         self.path.pop(0)
    
