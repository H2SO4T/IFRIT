import re


# it uniforms the c syntax
def reindent(filename):
    with open(filename, 'r+') as f:
        final_file = list()
        for line in f.readlines():
            result = re.split('({|})', line)
            for st in result:
                if st == '{' or st == '}':
                    final_file.append(f'\n{st}\n')
                else:
                    final_file.append(st)
        final_string = ''
        for st in final_file:
            if st != '\n' and st != '':
                final_string += st
        res = re.sub(r'(\n\t* *\n+)', r'\n', final_string)
        f.seek(0)
        f.write(res)
        f.truncate()


if __name__ == '__main__':
    reindent('prova0.c')
    reindent('prova1.c')
    reindent('prova0.c.pre.c')
    reindent('prova1.c.pre.c')
