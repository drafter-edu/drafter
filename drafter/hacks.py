"""
This module contains hacks to work around limitations of various platforms.
"""
import sys

__all__ = []


if sys.platform == 'skulpt':
    # Rewrite the __str__ method of MatPlotLibPlot to use its savefig method
    import matplotlib.pyplot as plt
    from drafter.components import MatPlotLibPlot

    MatPlotLibPlot.__str__ = plt.savefig