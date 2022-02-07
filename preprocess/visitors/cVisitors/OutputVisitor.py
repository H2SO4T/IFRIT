from pycparser import c_ast
from .BlockCreator import BlockCreator

class OutputVisitor():
    class OutputVisitorDecls(c_ast.NodeVisitor):

        def __init__(self):
            self.funcDecl=False
            
        def createOutputIf(self,expr):
            expressList = [c_ast.Constant(type='int',value='0')]
            funcCall = c_ast.FuncCall(c_ast.ID(name="assert"),c_ast.ExprList(expressList))
            if_all= c_ast.If( c_ast.BinaryOp(left=c_ast.ID(name='__out_var'),op='==',right= expr), c_ast.Compound([funcCall]),iffalse=None)
            return(if_all)

        def visit_FuncDecl(self,node):
            self.funcDecl=True
            self.chosenType=node.type.type
            self.generic_visit(node)
            self.funcDecl=False

        def visit_ParamList(self,node):
            declaration=c_ast.Decl('__out_var',[],[],[],c_ast.TypeDecl('__out_var',[],self.chosenType),None,None)
            node.params.append(declaration)
            
        def visit_Compound(self,node):
            for pos,child in enumerate(node.children()):
                if isinstance(child[1],c_ast.Return):
                    blockOut=self.createOutputIf(child[1].expr)
                    node.block_items.insert(pos,blockOut)
                self.visit(child[1])

    def instrument(self,ast):
        cleaner=BlockCreator()
        cleaner.generic_visit(ast)        
        self.visitor=self.OutputVisitorDecls()
        self.visitor.visit(ast)
        
    def observedCopy(self,ast):
        self.visitor.replaceByPrint(ast)
    def has_instrumented(self,ast):
        return(self.visitor.sanity())
