import matplotlib.pyplot as plt
import numpy as np

# Enable LaTeX rendering in Matplotlib
plt.rcParams['text.usetex'] = True

# Create a simple sine plot
x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(x, y, label=r'$\sin(x)$')

# Add LaTeX-rendered title and labels
ax.set_title(r'\textbf{LaTeX Test:} $\sin(x)$ vs $x$')
ax.set_xlabel(r'$x$')
ax.set_ylabel(r'$\sin(x)$')
ax.legend()

# Save the figure as a high-quality PDF
plt.savefig('latex_test.pdf', dpi=300, bbox_inches='tight')
plt.show()
