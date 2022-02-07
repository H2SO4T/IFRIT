from pycparser import c_ast
from .BlockCreator import BlockCreator


class AssertVisitor():
    class AssertLineVisitorDecls(c_ast.NodeVisitor):
        def __init__(self, linenum):
            self.linenum = linenum
            self.path = []
            self.reached = False
            expressList = [c_ast.Constant(type='int', value='0')]
            self.funcCall = c_ast.FuncCall(c_ast.ID(name="assert"), c_ast.ExprList(expressList))

        def sanity(self):
            return self.reached

        def generic_visit(self, node):
            # print(node.coord)
            if (isinstance(node, c_ast.Compound)):
                for pos, child in enumerate(node.children()):
                    if child[1].coord and child[1].coord.line == self.linenum:
                        if (isinstance(child[1], c_ast.If)):
                            child[1].iftrue.block_items.insert(0, self.funcCall)
                            self.inst_block = [child[1].iftrue.block_items]
                            self.inst_pos = [0]
                            if child[1].iffalse != None:
                                child[1].iffalse.block_items.insert(0, self.funcCall)
                                self.inst_block.append(child[1].iffalse.block_items)
                                self.inst_pos.append(0)
                        elif (isinstance(child[1], c_ast.For)):
                            child[1].stmt.block_items.insert(0, self.funcCall)
                            self.inst_block = [child[1].stmt.block_items]
                            self.inst_pos = [0]
                        elif (isinstance(child[1], c_ast.Return)):
                            node.block_items.insert(pos, self.funcCall)
                            self.inst_block = [node.block_items]
                            self.inst_pos = [pos]
                        else:
                            print(pos)
                            # print(type(node))
                            node.block_items.insert(pos + 1, self.funcCall)
                            self.inst_block = [node.block_items]
                            self.inst_pos = [pos + 1]
                            # print(type(node).__name__)
                            # print(node.coord)
                            # print(child[1].coord.line)
                        self.reached = True
            for c_name, c in node.children():
                if c_name in ["stmt", "iftrue", "iffalse"]:
                    if not self.reached:
                        self.path.insert(0, c)
                if c != self.funcCall:
                    self.visit(c)
                if c_name in ["stmt", "iftrue", "iffalse"]:
                    if not self.reached:
                        self.path.pop(0)

        def replaceByPrint(self, ast):
            expressList = [c_ast.Constant(type='string', value='"[[REACHED]]"')]
            ifexpress = c_ast.Assignment(op="=", lvalue=c_ast.ID(name="inst_flag"),
                                         rvalue=c_ast.Constant(type='int', value='1'))
            self.funcCall.name = c_ast.ID(name="perror")
            self.funcCall.args = c_ast.ExprList(expressList)
            if_all = c_ast.If(
                c_ast.BinaryOp(left=c_ast.ID(name='inst_flag'), op='==', right=c_ast.Constant(type='int', value='0')),
                c_ast.Compound([self.funcCall, ifexpress]), iffalse=None)
            for position, inst_block in enumerate(self.inst_block):
                inst_block[self.inst_pos[position]] = if_all

    def instrument(self, ast, linenum):
        cleaner = BlockCreator()
        cleaner.generic_visit(ast)
        self.visitor = self.AssertLineVisitorDecls(linenum)
        self.visitor.generic_visit(ast)

    def observedCopy(self, ast):
        self.visitor.replaceByPrint(ast)

    def has_instrumented(self, ast):
        return (self.visitor.sanity())
