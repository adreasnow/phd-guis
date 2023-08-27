from pandas import DataFrame

def extractIndices(df: DataFrame) -> list[float]:
    levels = len(df.index[0])
    indexLists = [[] for i in range(levels)]
    for row in df.index:
        for count, level in enumerate(row):
            if level not in indexLists[count]:
                indexLists[count] += [level]
    return [df.columns.to_list()] + indexLists

