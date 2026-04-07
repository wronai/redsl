
CONSTANT_1 = 1.5
CONSTANT_2 = 2.5
CONSTANT_3 = 3
CONSTANT_3 = 3.14159
CONSTANT_4 = 4
CONSTANT_5 = 5

def calculate_area(radius):
    pi = 3.14159
    return pi * radius * radius

def process_items(items):
    results = []
    for item in items:
        if item > 0:
            if item % 2 == 0:
                results.append(item * 2.5)
            else:
                results.append(item * 1.5)
    return results

def format_data(data):
    formatted = []
    for d in data:
        formatted.append(f'Value: {d}')
    return formatted

if __name__ == "__main__":
    print('Module loaded')
    data = [1, 2, 3, 4, 5]
    print(process_items(data))