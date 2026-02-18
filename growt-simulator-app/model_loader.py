def load_csv(path):
    with open(path, 'r') as f:
        lines = f.readlines()
        data = []
        header = lines[0].strip().split(';')
        data.append(header)
        for line in lines[1:]:
            values = line.strip().split(';')
            data.append([float(v) for v in values])
        return data
    

