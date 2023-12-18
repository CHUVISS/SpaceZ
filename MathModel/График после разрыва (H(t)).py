import numpy as np # подключаем библиотеку для работы с множествами
from scipy.integrate import odeint # импортируем функцию для интегрирования систем ОДУ
import matplotlib.pyplot as plt # подключаем библиотеку для рисования графиков
import math

fig, ax = plt.subplots() # создаём Рисунок и 1 график на нём ax
def f(x):
    return math.log(x)
ln = np.vectorize(f)

V0 = 1.49535337 # kм/c
H0 = 64.59 #м
w = 0.00515 #мю

t = np.array([i for i in range(0, 136, 5)]) # Добавляем возможность делать преобразования
t2 = np.array([j for j in range(0, 100,5)])
ax.plot(t, 0.15 * t -0.01 * t ** 2 / 2 + 2.1/w * ((1- w*t)*ln(1- w*t) + w*t)) # рисуем график, задавая значением по оси y функцию y, а значением по оси x функцию x
ax.plot(t2 + 135, H0 + V0 * t2 - (0.01 * t2**2 / 2))
plt.xlabel('t, с') 
plt.ylabel('H, км')
plt.grid(color = 'black') # задаём легенду осям и цвет сетки
plt.show() # Выводим на экран

