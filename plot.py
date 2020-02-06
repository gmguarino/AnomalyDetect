import json
import numpy as np
import matplotlib.pyplot as plt

filename = 'test.json'
with open(filename, 'r') as f:
    d = json.load(f)

plt.figure()
plt.plot(d['times'], d['values'], label='values')
plt.plot(d['times'], d['baseline'], label='baseline')
plt.legend()
plt.figure()
plt.plot(d['times'], d['season'], label='season')
plt.legend()
plt.figure()
plt.plot(d['times'], d['anomaly'], label='anomaly')
plt.plot(d['times'], d['remainder'], label='remainder')

plt.legend()
plt.show()
