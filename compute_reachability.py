import pandas

max_input = 24000
reachability = list()
dataframe = pandas.read_csv('results copia.csv', sep=';')
for elem in dataframe['test input dimension']:
    if elem > max_input:
        reachability.append(100.0)
    else:
        reachability.append((elem/max_input)*100)

print(sum(reachability)/len(reachability))
