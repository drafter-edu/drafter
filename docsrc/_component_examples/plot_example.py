from drafter import *
import matplotlib.pyplot as plt

@route
def index(state: str) -> Page:
    # Create a simple plot
    plt.figure(figsize=(8, 6))
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    plt.plot(x, y, 'bo-')
    plt.title('Simple Line Plot')
    plt.xlabel('X values')
    plt.ylabel('Y values')
    plt.grid(True)
    
    return Page(state, [
        "Matplotlib Plot Example:",
        Header("Simple Line Plot"),
        MatPlotLibPlot(),
        LineBreak(),
        Button("Generate New Plot", generate_plot)
    ])

@route
def generate_plot(state: str) -> Page:
    # Create a different plot
    plt.figure(figsize=(8, 6))
    import random
    x = list(range(10))
    y = [random.randint(1, 10) for _ in x]
    plt.bar(x, y)
    plt.title('Random Bar Chart')
    plt.xlabel('Categories')
    plt.ylabel('Values')
    
    return Page(state, [
        "New Random Plot Generated:",
        MatPlotLibPlot(),
        LineBreak(),
        Link("Back to original", index)
    ])

start_server("")