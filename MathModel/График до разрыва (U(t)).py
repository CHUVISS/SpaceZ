import numpy as np # подключаем библиотеку для работы с множествами
from scipy.integrate import odeint # импортируем функцию для интегрирования систем ОДУ
import matplotlib.pyplot as plt # подключаем библиотеку для рисования графиков
import math

fig, ax = plt.subplots() # создаём Рисунок и 1 график на нём ax
def f(x):
    return math.log(x)
f2 = np.vectorize(f)

t = np.array([0, 15, 25, 35, 45, 49]) # Добавляем возможность делать преобразования
ax.plot(t, -0.01 * t + 2.1 * f2(1/(1 - 0.0068*t))) # рисуем график, задавая значением по оси y функцию y, а значением по оси x функцию x
plt.xlabel('t, sec') 
plt.ylabel('U, kм/sec')
plt.grid(color = 'black') # задаём легенду осям и цвет сетки
plt.show() # Выводим на экран
