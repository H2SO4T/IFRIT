def compare_asts(ast1, ast2):
    if type(ast1) != type(ast2):
        print(type(ast1))
        print(type(ast2))
        return False
    if isinstance(ast1, tuple) and isinstance(ast2, tuple):
        if ast1[0] != ast2[0]:
            print(ast1)
            print(ast2)
            return False
        ast1 = ast1[1]
        ast2 = ast2[1]
        return compare_asts(ast1, ast2)
    for attr in ast1.attr_names:
        if getattr(ast1, attr) != getattr(ast2, attr):
            print(getattr(ast1, attr))
            print(getattr(ast2, attr))
            return False
    for i, c1 in enumerate(ast1.children()):
        if compare_asts(c1, ast2.children()[i]) == False:
            print(c1)
            print(ast2.children()[i])
            return False
    return True


def visit_ast(ast):
    if isinstance(ast, tuple):
        print(ast)
        ast = ast[1]
        return visit_ast(ast)
    for attr in ast.attr_names:
        print(getattr(ast, attr))
        if(getattr(ast,attr) == "+"):
            setattr(ast,attr,"-")
        if(getattr(ast,attr) == "<" or getattr(ast,attr) == ">"):
            setattr(ast,attr,"!=")
        print(getattr(ast, attr))
    for c in ast.children():
        visit_ast(c)
