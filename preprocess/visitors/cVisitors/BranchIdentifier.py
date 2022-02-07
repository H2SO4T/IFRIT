from pycparser import c_ast, c_generator
from .BlockCreator import BlockCreator

class BranchIdentifier():
    class BranchIdentifier_Visitor(c_ast.NodeVisitor):

        def __init__(self):
           self.branch=False
           self.lines=[]

        def visit_Compound(self,node):
            gen=c_generator.CGenerator()
            if(self.branch==True and node.block_items[0].coord !=None):
                self.lines.append(node.block_items[0].coord.line)
            self.generic_visit(node)
            
        def visit_If(self,node):
            self.branch=True
            self.generic_visit(node)
            self.brach=False

        def visit_For(self,node):
            self.branch=True
            self.generic_visit(node)
            self.brach=False

    def identifyLine(self,ast):
        block_vis=BlockCreator()
        block_vis.visit(ast)
        branch_vis=self.BranchIdentifier_Visitor()
        branch_vis.visit(ast)
        return(branch_vis.lines)
